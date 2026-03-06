from __future__ import annotations

import argparse
import sys

from . import x_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Save an X post suggestion")
    parser.add_argument("--text", required=True, help="Tweet text (max 280 chars)")
    parser.add_argument("--notes", default=None, help="Optional context/notes for this suggestion")
    args = parser.parse_args()

    if len(args.text) > 280:
        print(f"ERROR: text exceeds 280 characters ({len(args.text)})", file=sys.stderr)
        sys.exit(1)

    suggestion = x_db.insert_suggestion(text=args.text, notes=args.notes)
    print(f"Saved suggestion {suggestion['id']}: {args.text[:60]}{'...' if len(args.text) > 60 else ''}")


if __name__ == "__main__":
    main()
