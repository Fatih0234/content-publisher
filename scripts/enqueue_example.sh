#!/usr/bin/env bash
# Example: enqueue a post scheduled for now (immediate publish on next run)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

if [[ -f "$ROOT/.env" ]]; then
    set -a
    source "$ROOT/.env"
    set +a
fi

cd "$ROOT"

# Enqueue a post for right now
python -m src.publisher.enqueue \
    --account-label "my-account" \
    --publish-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --body "Hello from the LinkedIn scheduler!"

# Enqueue a post for a specific future time
# python -m src.publisher.enqueue \
#     --account-label "my-account" \
#     --publish-at "2026-03-06T09:00:00Z" \
#     --body "Scheduled post for tomorrow morning."
