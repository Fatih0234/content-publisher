from __future__ import annotations

from .db import get_client


def insert_suggestion(
    text: str,
    notes: str | None = None,
    discord_message_id: str | None = None,
) -> dict:
    result = (
        get_client()
        .table("x_suggestions")
        .insert({"text": text, "notes": notes, "discord_message_id": discord_message_id})
        .execute()
    )
    return result.data[0]


def get_pending_with_discord() -> list[dict]:
    result = (
        get_client()
        .table("x_suggestions")
        .select("*")
        .eq("status", "pending")
        .not_.is_("discord_message_id", "null")
        .execute()
    )
    return result.data or []


def approve_suggestion(suggestion_id: str) -> None:
    get_client().table("x_suggestions").update(
        {"status": "published"}
    ).eq("id", suggestion_id).execute()


def reject_suggestion(suggestion_id: str) -> None:
    get_client().table("x_suggestions").update(
        {"status": "rejected"}
    ).eq("id", suggestion_id).execute()


def list_suggestions(status: str = "pending") -> list[dict]:
    result = (
        get_client()
        .table("x_suggestions")
        .select("*")
        .eq("status", status)
        .order("created_at")
        .execute()
    )
    return result.data or []
