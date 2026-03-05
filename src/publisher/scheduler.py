from __future__ import annotations

import json
import logging

from . import config, db
from .linkedin_client import publish_text, LinkedInError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def run() -> None:
    log.info("Claiming posts (worker=%s, limit=%d)", config.WORKER_ID, config.CLAIM_LIMIT)
    posts = db.claim_due_posts(config.WORKER_ID, config.CLAIM_LIMIT)
    log.info("Claimed %d post(s)", len(posts))

    for post in posts:
        post_id = post["id"]
        attempt_count = post["attempt_count"] + 1
        db.increment_attempt_count(post_id, post["attempt_count"])

        account = db.get_account(post["account_id"])

        log.info("Publishing post %s (attempt %d)", post_id, attempt_count)
        try:
            post_urn, raw = publish_text(
                author_urn=account["author_urn"],
                token=account["access_token"],
                body=post["body"],
                version=config.LINKEDIN_VERSION,
            )
            db.mark_published(post_id, post_urn)
            db.log_attempt(
                post_id=post_id,
                status="published",
                http_status=201,
                response_snippet=json.dumps(raw)[:500],
            )
            log.info("Post %s published as %s", post_id, post_urn)

        except LinkedInError as exc:
            log.error("Post %s failed (HTTP %d): %s", post_id, exc.http_status, exc.message)
            db.mark_failed(post_id, exc.message, attempt_count)
            db.log_attempt(
                post_id=post_id,
                status="failed" if attempt_count >= config.MAX_ATTEMPTS else "queued",
                http_status=exc.http_status,
                error_message=exc.message[:500],
            )

        except Exception as exc:
            log.exception("Unexpected error publishing post %s", post_id)
            db.mark_failed(post_id, str(exc), attempt_count)
            db.log_attempt(
                post_id=post_id,
                status="failed" if attempt_count >= config.MAX_ATTEMPTS else "queued",
                error_message=str(exc)[:500],
            )


if __name__ == "__main__":
    run()
