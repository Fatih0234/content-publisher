from __future__ import annotations

import logging
from datetime import datetime, timezone

from . import config
from . import db
from . import x_db
from . import discord_client
from .content_fetcher import fetch_static_content
from .content_agent import generate_posts

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def run() -> None:
    items = fetch_static_content()
    log.info("Fetched %d content item(s)", len(items))

    for item in items:
        if db.is_content_processed(item.url):
            log.info("Skipping already-processed URL: %s", item.url)
            continue

        log.info("Generating posts for: %s", item.title)
        try:
            generated = generate_posts(item)
        except Exception:
            log.exception("Failed to generate posts for %s", item.url)
            try:
                discord_client.post_error(f"Generation failed for: {item.url}")
            except Exception:
                pass
            continue

        log.info("Posting draft to Discord for: %s", item.title)
        try:
            message_id = discord_client.post_draft(
                item, generated.linkedin_text, generated.x_text
            )
        except Exception:
            log.exception("Failed to post draft to Discord for %s", item.url)
            continue

        log.info("Discord message id: %s", message_id)

        publish_at = datetime.now(timezone.utc)

        try:
            if not config.LINKEDIN_ACCOUNT_LABEL:
                raise RuntimeError("LINKEDIN_ACCOUNT_LABEL env var is not set")
            post_id = db.enqueue_linkedin_post(
                account_label=config.LINKEDIN_ACCOUNT_LABEL,
                body=generated.linkedin_text,
                publish_at=publish_at,
                discord_message_id=message_id,
            )
            log.info("Inserted LinkedIn post %s (pending_approval)", post_id)
        except Exception:
            log.exception("Failed to insert LinkedIn post for %s", item.url)
            continue

        try:
            x_db.insert_suggestion(
                text=generated.x_text,
                notes=item.url,
                discord_message_id=message_id,
            )
            log.info("Inserted X suggestion for %s", item.url)
        except Exception:
            log.exception("Failed to insert X suggestion for %s", item.url)

        db.mark_content_processed(item.url)
        log.info("Marked as processed: %s", item.url)


if __name__ == "__main__":
    run()
