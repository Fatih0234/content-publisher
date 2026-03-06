from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class ContentItem:
    title: str
    url: str
    summary: str
    source: Literal["blog", "youtube"]


def fetch_static_content() -> list[ContentItem]:
    return [
        ContentItem(
            title="Building a Serverless LinkedIn Scheduler with GitHub Actions",
            url="https://example.com/blog/linkedin-scheduler-github-actions",
            summary=(
                "A deep dive into building a fully serverless LinkedIn post scheduler "
                "using GitHub Actions cron jobs, Supabase as the database, and the "
                "LinkedIn API. No servers to maintain, zero idle cost."
            ),
            source="blog",
        ),
        ContentItem(
            title="Why I Stopped Using Docker for Local Development",
            url="https://example.com/blog/no-docker-local-dev",
            summary=(
                "After years of Docker-first development, I switched back to native "
                "tooling. Here's what changed, what broke, and what's surprisingly better."
            ),
            source="blog",
        ),
        ContentItem(
            title="Supabase RLS in Practice: Lessons from Production",
            url="https://example.com/blog/supabase-rls-production",
            summary=(
                "Row-level security sounds simple until you hit edge cases in production. "
                "This post covers patterns that work, anti-patterns to avoid, and debugging "
                "techniques when policies behave unexpectedly."
            ),
            source="blog",
        ),
        ContentItem(
            title="Python Dataclasses vs Pydantic: When to Use Each",
            url="https://example.com/blog/dataclasses-vs-pydantic",
            summary=(
                "Dataclasses ship with Python's stdlib and Pydantic adds validation and "
                "serialization. Here's a practical comparison with real-world examples "
                "showing where each shines."
            ),
            source="blog",
        ),
        ContentItem(
            title="GitHub Actions Cron: Gotchas and Best Practices",
            url="https://example.com/blog/github-actions-cron-gotchas",
            summary=(
                "GitHub Actions scheduled workflows have quirks: they can be delayed, "
                "skipped on inactive repos, and have UTC-only scheduling. This post covers "
                "all the gotchas and how to build reliable cron-based pipelines."
            ),
            source="blog",
        ),
    ]
