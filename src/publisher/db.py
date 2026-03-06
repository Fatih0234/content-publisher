from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from supabase import create_client, Client

from . import config

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
    return _client


def claim_due_posts(worker_id: str, limit: int) -> list[dict]:
    result = get_client().rpc(
        "claim_due_posts",
        {"p_limit": limit, "p_worker_id": worker_id},
    ).execute()
    return result.data or []


def get_account(account_id: str) -> dict:
    result = (
        get_client()
        .table("linkedin_accounts")
        .select("*")
        .eq("id", account_id)
        .single()
        .execute()
    )
    return result.data


def mark_published(post_id: str, post_urn: str) -> None:
    get_client().table("scheduled_posts").update(
        {
            "status": "published",
            "post_urn": post_urn,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "locked_at": None,
            "locked_by": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", post_id).execute()


def mark_failed(post_id: str, error: str, attempt_count: int) -> None:
    if attempt_count >= config.MAX_ATTEMPTS:
        update = {
            "status": "failed",
            "locked_at": None,
            "locked_by": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    else:
        requeue_at = datetime.now(timezone.utc) + timedelta(
            minutes=config.REQUEUE_BACKOFF_MINUTES
        )
        update = {
            "status": "queued",
            "publish_at": requeue_at.isoformat(),
            "locked_at": None,
            "locked_by": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    get_client().table("scheduled_posts").update(update).eq("id", post_id).execute()


def increment_attempt_count(post_id: str, current_count: int) -> None:
    get_client().table("scheduled_posts").update(
        {"attempt_count": current_count + 1}
    ).eq("id", post_id).execute()


def log_attempt(
    post_id: str,
    status: str,
    http_status: int | None = None,
    response_snippet: str | None = None,
    error_message: str | None = None,
) -> None:
    get_client().table("publish_attempts").insert(
        {
            "post_id": post_id,
            "status": status,
            "http_status": http_status,
            "response_snippet": response_snippet,
            "error_message": error_message,
        }
    ).execute()


def get_account_by_label(label: str) -> dict:
    result = (
        get_client()
        .table("linkedin_accounts")
        .select("*")
        .eq("label", label)
        .single()
        .execute()
    )
    return result.data


def enqueue_linkedin_post(
    account_label: str,
    body: str,
    publish_at: datetime,
    discord_message_id: str,
) -> str:
    account = get_account_by_label(account_label)
    result = (
        get_client()
        .table("scheduled_posts")
        .insert(
            {
                "account_id": account["id"],
                "body": body,
                "publish_at": publish_at.isoformat(),
                "status": "pending_approval",
                "discord_message_id": discord_message_id,
            }
        )
        .execute()
    )
    return result.data[0]["id"]


def get_pending_approval_posts() -> list[dict]:
    result = (
        get_client()
        .table("scheduled_posts")
        .select("*")
        .eq("status", "pending_approval")
        .not_.is_("discord_message_id", "null")
        .execute()
    )
    return result.data or []


def approve_post(post_id: str) -> None:
    get_client().table("scheduled_posts").update(
        {
            "status": "queued",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", post_id).execute()


def reject_post(post_id: str) -> None:
    get_client().table("scheduled_posts").update(
        {
            "status": "rejected",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", post_id).execute()


def is_content_processed(url: str) -> bool:
    result = (
        get_client()
        .table("processed_content")
        .select("id")
        .eq("source_url", url)
        .execute()
    )
    return bool(result.data)


def mark_content_processed(url: str) -> None:
    get_client().table("processed_content").insert(
        {"source_url": url}
    ).execute()
