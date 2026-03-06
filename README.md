# LinkedIn + X Scheduled Publisher

Automated content pipeline: generates posts with Gemini → posts drafts to Discord for approval → publishes approved posts to LinkedIn. X/Twitter suggestions are stored for manual review.

## Architecture

```
Content sources (static URLs)
  └── src/publisher/content_fetcher.py
        └── src/publisher/content_agent.py  (Gemini API)
              └── src/publisher/discord_client.py
                    └── #content-drafts channel (Discord)
                          └── React ✅ or ❌ to approve/reject

GitHub Actions (*/30 * * * *)
  └── src/publisher/check_approvals.py
        ├── reads Discord reactions
        └── updates Supabase: pending_approval → queued | rejected

GitHub Actions (*/5 * * * *)
  └── src/publisher/scheduler.py
        ├── claim_due_posts() RPC  (SELECT FOR UPDATE SKIP LOCKED)
        ├── linkedin_client.publish_text()
        └── mark_published / mark_failed / log_attempt

Supabase DB
  linkedin_accounts   — OAuth tokens + author URNs
  scheduled_posts     — pending_approval/queued/publishing/published/failed
  publish_attempts    — audit log per attempt
  x_suggestions       — pending/approved/rejected tweet drafts
  processed_content   — dedup by source URL
```

## Content Generation & Approval Flow

1. **Generate** (`generate.yml`, daily at 08:00 UTC): fetches content items, calls Gemini to write a LinkedIn post + tweet, posts a combined draft to `#content-drafts` in Discord.
2. **Approve**: react ✅ to the Discord message to approve, ❌ to reject.
3. **Check approvals** (`check_approvals.yml`, every 30 min): reads reactions, sets `queued` or `rejected` in Supabase.
4. **Publish** (`publish.yml`, every 5 min): claims queued posts and publishes them to LinkedIn.

Status flow: `pending_approval` → ✅ → `queued` → `publishing` → `published`
                              → ❌ → `rejected`

## Setup

### 1. Supabase

Apply the migrations:

```bash
supabase db push
# or paste each file in supabase/migrations/ into the SQL editor in order
```

Insert a LinkedIn account:

```sql
INSERT INTO linkedin_accounts (label, actor_type, author_urn, access_token)
VALUES (
  'my-account',
  'person',
  'urn:li:person:XXXXXXXX',
  'AQV...'   -- LinkedIn OAuth2 access token
);
```

### 2. Discord

- Create a bot and add it to your server with **View Channel** + **Read Message History** on `#content-drafts`.
- Create webhooks for `#content-drafts`, `#published`, and `#errors`.
- Copy the drafts channel ID.

### 3. Local development

```bash
cp .env.example .env
# fill in all required vars (see table below)

pip install uv && uv sync
uv run python -m src.publisher.generate        # generate + post drafts to Discord
uv run python -m src.publisher.check_approvals # poll reactions, update statuses
uv run python -m src.publisher.scheduler       # publish queued LinkedIn posts
```

### 4. GitHub Actions secrets

Set these in **Settings → Secrets → Actions**:

| Secret | Required by | Description |
|--------|-------------|-------------|
| `SUPABASE_URL` | all | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | all | Service role key (not anon) |
| `GOOGLE_API_KEY` | generate | Gemini API key |
| `LINKEDIN_ACCOUNT_LABEL` | generate | Label matching `linkedin_accounts.label` |
| `LINKEDIN_VERSION` | publish | e.g. `202501` |
| `DISCORD_BOT_TOKEN` | generate, check_approvals | Bot token for reading reactions |
| `DISCORD_WEBHOOK_DRAFTS` | generate | Webhook URL for `#content-drafts` |
| `DISCORD_WEBHOOK_PUBLISHED` | scheduler | Webhook URL for `#published` |
| `DISCORD_WEBHOOK_ERRORS` | generate | Webhook URL for `#errors` |
| `DISCORD_CHANNEL_DRAFTS_ID` | check_approvals | Channel ID of `#content-drafts` |

`WORKER_ID` is automatically set to `${{ github.run_id }}`.

## Smoke test

```bash
# 1. Generate drafts (posts to Discord)
uv run python -m src.publisher.generate

# 2. React ✅ to the Discord message

# 3. Check approvals (sets post to queued)
uv run python -m src.publisher.check_approvals

# 4. Publish
uv run python -m src.publisher.scheduler

# 5. Verify in Supabase
# SELECT status, post_urn FROM scheduled_posts ORDER BY created_at DESC LIMIT 1;
# SELECT * FROM publish_attempts ORDER BY attempted_at DESC LIMIT 1;
```

## Retry logic

- Failed posts requeue with a configurable backoff (default +15 min, set `REQUEUE_BACKOFF_MINUTES`)
- After 3 attempts (`MAX_ATTEMPTS`) the post is marked `failed` permanently
- Stale locks (>30 min) are automatically reclaimed on the next run

## Troubleshooting

| Problem | Check |
|---------|-------|
| `KeyError: SUPABASE_URL` | `.env` file missing or not loaded |
| `401` from LinkedIn | `access_token` expired — refresh and update `linkedin_accounts` |
| Posts stuck in `publishing` | Lock held >30 min — next run reclaims them automatically |
| `claim_due_posts` returns 0 | `publish_at` is in the future, or status is not `queued` |
| No drafts posted to Discord | Check `GOOGLE_API_KEY`, `DISCORD_WEBHOOK_DRAFTS`, content source URLs |
| Reactions not picked up | Check `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_DRAFTS_ID` |

## X / Twitter

X suggestions are generated alongside LinkedIn posts and stored in `x_suggestions`. The Discord approval flow sets them to `approved`; manual posting on X is still required.

```sql
-- Review pending
SELECT id, text, notes, created_at FROM x_suggestions WHERE status = 'pending' ORDER BY created_at;

-- After posting manually
UPDATE x_suggestions SET status = 'published' WHERE id = '<uuid>';
```
