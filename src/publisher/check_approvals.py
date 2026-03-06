from __future__ import annotations

import logging

from . import db
from . import x_db
from . import discord_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def run() -> None:
    _check_linkedin_posts()
    _check_x_suggestions()


def _process_items(items: list[dict], approve_fn, reject_fn, label: str) -> None:
    for item in items:
        item_id = item["id"]
        message_id = item["discord_message_id"]

        try:
            reactions = discord_client.get_reactions(message_id)
        except Exception:
            log.exception("Failed to fetch reactions for message %s", message_id)
            continue

        log.info("%s %s reactions: %s", label, item_id, reactions)

        if discord_client.APPROVE_EMOJI in reactions:
            approve_fn(item_id)
            log.info("Approved %s %s", label, item_id)
        elif discord_client.REJECT_EMOJI in reactions:
            reject_fn(item_id)
            log.info("Rejected %s %s", label, item_id)


def _check_linkedin_posts() -> None:
    posts = db.get_pending_approval_posts()
    log.info("Checking %d pending LinkedIn post(s)", len(posts))
    _process_items(posts, db.approve_post, db.reject_post, "LinkedIn post")


def _check_x_suggestions() -> None:
    suggestions = x_db.get_pending_with_discord()
    log.info("Checking %d pending X suggestion(s)", len(suggestions))
    _process_items(suggestions, x_db.approve_suggestion, x_db.reject_suggestion, "X suggestion")


if __name__ == "__main__":
    run()
