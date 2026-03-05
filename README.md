# LinkedIn Scheduled Publisher

Publishes scheduled LinkedIn posts via GitHub Actions cron (every 5 min). Posts and credentials are stored in Supabase.

## Architecture

```
Supabase DB
  linkedin_accounts   — OAuth tokens + author URNs
  scheduled_posts     — queued/publishing/published/failed posts
  publish_attempts    — audit log per attempt

GitHub Actions (*/5 * * * *)
  └── src/publisher/scheduler.py
        ├── claim_due_posts() RPC  (SELECT FOR UPDATE SKIP LOCKED)
        ├── linkedin_client.publish_text()
        └── mark_published / mark_failed / log_attempt
```

## Setup

### 1. Supabase

Apply the migration:

```bash
supabase db push
# or paste supabase/migrations/0001_init.sql into the SQL editor
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

### 2. Local development

```bash
cp .env.example .env
# fill in SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. GitHub Actions secrets

Set these in **Settings → Secrets → Actions**:

| Secret | Value |
|--------|-------|
| `SUPABASE_URL` | Your project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (not anon key) |
| `LINKEDIN_VERSION` | e.g. `202501` |

`WORKER_ID` is automatically set to `${{ github.run_id }}`.

## Usage

### Enqueue a post

```bash
# Immediately (publishes on next scheduler run)
python -m src.publisher.enqueue \
  --account-label my-account \
  --publish-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --body "Hello LinkedIn!"

# Scheduled for a future time
python -m src.publisher.enqueue \
  --account-label my-account \
  --publish-at "2026-03-06T09:00:00Z" \
  --body "Good morning!"
```

Or use the helper script:

```bash
./scripts/enqueue_example.sh
```

### Run scheduler locally

```bash
./scripts/run_local.sh
# or
python -m src.publisher.scheduler
```

## Smoke test

```bash
# 1. Enqueue
python -m src.publisher.enqueue \
  --account-label my-account \
  --publish-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --body "Smoke test post"

# 2. Publish
python -m src.publisher.scheduler

# 3. Verify in Supabase
# SELECT status, post_urn FROM scheduled_posts ORDER BY created_at DESC LIMIT 1;
# SELECT * FROM publish_attempts ORDER BY attempted_at DESC LIMIT 1;
```

## Retry logic

- Failed posts requeue with a +15 min backoff
- After 3 attempts the post is marked `failed` permanently
- Stale locks (>30 min) are automatically reclaimed on the next run

## Troubleshooting

| Problem | Check |
|---------|-------|
| `KeyError: SUPABASE_URL` | `.env` file missing or not loaded |
| `401` from LinkedIn | `access_token` expired — refresh and update `linkedin_accounts` |
| Posts stuck in `publishing` | Lock held >30 min — next run reclaims them automatically |
| `claim_due_posts` returns 0 | `publish_at` is in the future, or status is not `queued` |
