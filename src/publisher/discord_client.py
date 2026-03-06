from __future__ import annotations

import time

import requests

from . import config
from .content_fetcher import ContentItem

_DISCORD_API = "https://discord.com/api/v10"

APPROVE_EMOJI = "\u2705"  # ✅
REJECT_EMOJI = "\u274c"   # ❌


def _bot_headers() -> dict:
    return {"Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"}


def post_draft(item: ContentItem, linkedin_text: str, x_text: str) -> str:
    """Post draft to #content-drafts via webhook. Returns discord message id."""
    content = (
        f"**New draft: {item.title}**\n"
        f"Source: {item.url}\n\n"
        f"**LinkedIn:**\n{linkedin_text}\n\n"
        f"**X / Tweet:**\n{x_text}\n\n"
        f"React {APPROVE_EMOJI} to approve or {REJECT_EMOJI} to reject."
    )

    resp = requests.post(
        f"{config.DISCORD_WEBHOOK_DRAFTS}?wait=true",
        json={"content": content},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def get_reactions(message_id: str) -> set[str]:
    """Return set of emoji names that have reactions on the message."""
    resp = requests.get(
        f"{_DISCORD_API}/channels/{config.DISCORD_CHANNEL_DRAFTS_ID}/messages/{message_id}",
        headers=_bot_headers(),
        timeout=10,
    )
    if resp.status_code == 429:
        retry_after = float(resp.json().get("retry_after", 1.0))
        time.sleep(retry_after + 0.1)
        resp = requests.get(
            f"{_DISCORD_API}/channels/{config.DISCORD_CHANNEL_DRAFTS_ID}/messages/{message_id}",
            headers=_bot_headers(),
            timeout=10,
        )
    resp.raise_for_status()
    data = resp.json()
    # Small delay to avoid hitting rate limits on consecutive calls
    time.sleep(0.5)
    return {r["emoji"]["name"] for r in data.get("reactions", [])}


def post_published(post_urn: str, body_preview: str) -> None:
    """Post success notification to #published channel."""
    content = f"Published to LinkedIn\nURN: `{post_urn}`\nPreview: {body_preview[:120]}"
    requests.post(
        config.DISCORD_WEBHOOK_PUBLISHED,
        json={"content": content},
        timeout=10,
    ).raise_for_status()


def post_error(message: str) -> None:
    """Post error notification to #errors channel."""
    requests.post(
        config.DISCORD_WEBHOOK_ERRORS,
        json={"content": f"Error: {message}"},
        timeout=10,
    ).raise_for_status()
