# Project Progress

## Session 1 — Full pipeline implementation (2026-03-06)

### What was built

**Goal:** Add content ingestion + AI generation + human approval loop to the existing LinkedIn scheduler.

**Architecture implemented:**
```
content_fetcher.py (static fixtures)
        ↓
generate.py — Gemini generates LinkedIn post + tweet
        ↓
Discord #content-drafts — user reacts ✅/❌
        ↓
check_approvals.py — reads reactions → updates Supabase status
        ↓
scheduler.py — publishes queued posts → notifies #published
```

**Files created:**
- `supabase/migrations/0004_approval_flow.sql`
- `src/publisher/content_fetcher.py` — ContentItem dataclass + 5 static items
- `src/publisher/content_agent.py` — Gemini gemini-2.0-flash, two separate prompts
- `src/publisher/discord_client.py` — webhook posting + bot reaction reading
- `src/publisher/generate.py` — orchestrates full generation pipeline
- `src/publisher/check_approvals.py` — polls reactions for LinkedIn + X
- `.github/workflows/generate.yml` — cron 0 8 * * *
- `.github/workflows/check_approvals.yml` — cron */30 * * * *

**Files modified:**
- `src/publisher/config.py` — added Google/Discord env vars
- `src/publisher/db.py` — added enqueue_linkedin_post, approval CRUD, processed_content helpers
- `src/publisher/x_db.py` — added discord_message_id param, approval helpers
- `src/publisher/scheduler.py` — added Discord #published notification on successful publish
- `pyproject.toml` + `requirements.txt` — added google-genai

**Issues hit and resolved:**
1. Gemini call appeared to hang — was just slow on first call (~2s), user hit Ctrl+C prematurely
2. Discord 403 — bot not invited to server. Fixed by generating OAuth2 invite URL and adding bot
3. Discord 429 rate limit — fixed by adding retry-after handling + 0.5s delay between requests
4. discord_client.post_published() had ContentItem param — simplified to just (urn, body_preview)

### Test results (all passing)
- `generate.py` — 5 drafts generated and posted to Discord, inserted to Supabase ✅
- `check_approvals.py` — ✅ reaction → queued, ❌ reaction → rejected, no reaction → unchanged ✅
- Dedup works — re-running generate.py skips already-processed URLs ✅

### Current limitation
`content_fetcher.py` returns 5 hardcoded fake blog posts. Real content sources not yet wired up.

---

## Future Work

### Option A: RSS Feed Integration

Replace `fetch_static_content()` with a live RSS/Atom parser.

**Dependencies to add:**
```
feedparser
```

**Implementation sketch (`content_fetcher.py`):**
```python
import feedparser
from datetime import datetime, timezone, timedelta

RSS_FEEDS = [
    "https://yourblog.com/feed",
    # add more feeds here
]
LOOKBACK_HOURS = 25  # fetch items published in last 25h (runs daily)

def fetch_rss_content() -> list[ContentItem]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    items = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            # parse published date
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published < cutoff:
                continue
            items.append(ContentItem(
                title=entry.title,
                url=entry.link,
                summary=entry.get("summary", entry.get("description", "")),
                source="blog",
            ))
    return items
```

**Key design decisions:**
- `LOOKBACK_HOURS=25` gives 1h overlap to avoid missing items if cron runs slightly late
- dedup via `processed_content` table handles duplicates when the same item appears across runs
- Strip HTML from summary if feed returns HTML (`from html import unescape` + regex or `bleach`)
- Add `RSS_FEEDS` to config.py as comma-separated env var: `RSS_FEEDS=url1,url2`

**Config addition:**
```python
RSS_FEEDS: list[str] = [u.strip() for u in os.getenv("RSS_FEEDS", "").split(",") if u.strip()]
```

---

### Option B: YouTube API Integration

Fetch latest video uploads and generate posts promoting them.

**Dependencies to add:**
```
google-api-python-client
```

**Setup required (one-time):**
1. Enable YouTube Data API v3 in Google Cloud Console (same project as Gemini or separate)
2. Create API key (not OAuth — channel listing is public)
3. Add `YOUTUBE_CHANNEL_ID` and `YOUTUBE_API_KEY` to env vars

**Implementation sketch (`content_fetcher.py`):**
```python
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta

def fetch_youtube_content() -> list[ContentItem]:
    youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()

    response = youtube.search().list(
        part="snippet",
        channelId=config.YOUTUBE_CHANNEL_ID,
        order="date",
        publishedAfter=cutoff,
        type="video",
        maxResults=10,
    ).execute()

    items = []
    for item in response.get("items", []):
        snippet = item["snippet"]
        video_id = item["id"]["videoId"]
        items.append(ContentItem(
            title=snippet["title"],
            url=f"https://www.youtube.com/watch?v={video_id}",
            summary=snippet.get("description", "")[:500],
            source="youtube",
        ))
    return items
```

**Config additions:**
```python
YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_CHANNEL_ID: str = os.getenv("YOUTUBE_CHANNEL_ID", "")
```

**Prompt tweak for YouTube:**
The `content_agent.py` prompts should be adjusted based on `item.source`:
- LinkedIn prompt for YouTube: emphasize "watch the video", include timestamp hooks, CTA to comment
- X prompt for YouTube: include video URL directly, shorter teaser

---

### Combining sources

Once both are implemented, `fetch_static_content()` can be replaced with:

```python
def fetch_content() -> list[ContentItem]:
    items = []
    if config.RSS_FEEDS:
        items.extend(fetch_rss_content())
    if config.YOUTUBE_CHANNEL_ID and config.YOUTUBE_API_KEY:
        items.extend(fetch_youtube_content())
    return items
```

No other changes needed — dedup, generation, Discord posting, and approval flow all work the same regardless of source.
