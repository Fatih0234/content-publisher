from __future__ import annotations

import requests


class LinkedInError(Exception):
    def __init__(self, http_status: int, message: str):
        super().__init__(message)
        self.http_status = http_status
        self.message = message


def publish_text(
    author_urn: str,
    token: str,
    body: str,
    version: str,
) -> tuple[str, dict]:
    """
    POST a text-only post to LinkedIn REST API.
    Returns (post_urn, raw_response) on success.
    Raises LinkedInError on failure.
    """
    payload = {
        "author": author_urn,
        "commentary": body,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": version,
        "X-Restli-Protocol-Version": "2.0.0",
    }

    response = requests.post(
        "https://api.linkedin.com/rest/posts",
        json=payload,
        headers=headers,
        timeout=30,
    )

    if not response.ok:
        raise LinkedInError(
            http_status=response.status_code,
            message=response.text[:500],
        )

    # LinkedIn returns the post URN in the X-RestLi-Id header
    post_urn = response.headers.get("X-RestLi-Id", "")
    try:
        raw = response.json()
    except Exception:
        raw = {"body": response.text}

    return post_urn, raw
