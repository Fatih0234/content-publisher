from __future__ import annotations

from dataclasses import dataclass

from google import genai

from . import config
from .content_fetcher import ContentItem

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GOOGLE_API_KEY)
    return _client


@dataclass
class GeneratedPost:
    linkedin_text: str
    x_text: str


_LINKEDIN_PROMPT = """\
You are a professional content writer for LinkedIn. Write a LinkedIn post based on the article below.

Requirements:
- 150-300 words
- Professional but conversational tone
- Start with a hook (question, bold statement, or surprising fact)
- Include 3-5 relevant hashtags at the end
- No generic filler phrases like "In today's fast-paced world"
- Focus on a single insight or takeaway

Article title: {title}
Article URL: {url}
Article summary: {summary}

Write only the post text, nothing else.
"""

_X_PROMPT = """\
You are a sharp tech Twitter/X writer. Write a tweet based on the article below.

Requirements:
- Maximum 280 characters (strict limit)
- Punchy and direct — no fluff
- May include 1-2 hashtags if they fit naturally
- Include the URL at the end

Article title: {title}
Article URL: {url}
Article summary: {summary}

Write only the tweet text, nothing else.
"""


def generate_posts(item: ContentItem) -> GeneratedPost:
    client = _get_client()

    linkedin_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=_LINKEDIN_PROMPT.format(
            title=item.title,
            url=item.url,
            summary=item.summary,
        ),
    )

    x_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=_X_PROMPT.format(
            title=item.title,
            url=item.url,
            summary=item.summary,
        ),
    )

    linkedin_text = linkedin_response.text.strip()
    x_text = x_response.text.strip()

    # Hard-enforce X character limit
    if len(x_text) > 280:
        x_text = x_text[:277] + "..."

    return GeneratedPost(linkedin_text=linkedin_text, x_text=x_text)
