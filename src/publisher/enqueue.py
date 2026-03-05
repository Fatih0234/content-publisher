from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from . import db


def main() -> None:
    parser = argparse.ArgumentParser(description="Enqueue a LinkedIn post")
    parser.add_argument("--account-label", required=True, help="Label of the linkedin_accounts row")
    parser.add_argument("--publish-at", required=True, help="ISO8601 UTC datetime e.g. 2026-03-05T15:00:00Z")
    parser.add_argument("--body", required=True, help="Post text content")
    args = parser.parse_args()

    # Validate datetime
    try:
        publish_at = datetime.fromisoformat(args.publish_at.replace("Z", "+00:00"))
    except ValueError:
        print(f"ERROR: --publish-at must be ISO8601, got: {args.publish_at}", file=sys.stderr)
        sys.exit(1)

    # Look up account by label
    result = (
        db.get_client()
        .table("linkedin_accounts")
        .select("id, label")
        .eq("label", args.account_label)
        .single()
        .execute()
    )
    if not result.data:
        print(f"ERROR: No account with label '{args.account_label}'", file=sys.stderr)
        sys.exit(1)

    account_id = result.data["id"]

    # Insert post
    insert_result = (
        db.get_client()
        .table("scheduled_posts")
        .insert(
            {
                "account_id": account_id,
                "body": args.body,
                "publish_at": publish_at.isoformat(),
                "status": "queued",
            }
        )
        .execute()
    )
    post = insert_result.data[0]
    print(f"Enqueued post {post['id']} for {publish_at.isoformat()} (account: {args.account_label})")


if __name__ == "__main__":
    main()
