#!/usr/bin/env python3
"""Validate backfill data consistency.

Usage:
    python scripts/validate_backfill.py <dump_file>
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any
import argparse


def validate_dump(dump_file: str) -> Dict[str, Any]:
    """Validate localStorage dump structure and content."""
    try:
        with open(dump_file) as f:
            dumps = json.load(f)
    except FileNotFoundError:
        print(f"✗ File not found: {dump_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON: {dump_file}")
        sys.exit(1)

    if not isinstance(dumps, list):
        print("✗ Dump must be a JSON array of user objects")
        sys.exit(1)

    stats = {
        "total_users": 0,
        "total_conversations": 0,
        "total_messages": 0,
        "total_snippets": 0,
        "total_presets": 0,
        "errors": [],
        "warnings": [],
    }

    for i, dump in enumerate(dumps):
        # Validate required fields
        if not isinstance(dump, dict):
            stats["errors"].append(f"Item {i}: Not a dict")
            continue

        if "github_id" not in dump:
            stats["warnings"].append(f"Item {i}: Missing github_id")
            continue

        if "github_login" not in dump:
            stats["warnings"].append(f"Item {i}: Missing github_login")
            continue

        stats["total_users"] += 1

        # Count conversations
        chat_data = dump.get("chat_data", {})
        if not isinstance(chat_data, dict):
            stats["warnings"].append(f"User {dump.get('github_login')}: chat_data not a dict")
            continue

        tabs = chat_data.get("tabs", [])
        if not isinstance(tabs, list):
            stats["warnings"].append(f"User {dump.get('github_login')}: tabs not a list")
            continue

        for tab in tabs:
            stats["total_conversations"] += 1

            # Count messages
            msgs = tab.get("msgs", [])
            if not isinstance(msgs, list):
                stats["warnings"].append(f"User {dump.get('github_login')}: msgs not a list")
                continue

            for msg in msgs:
                if not isinstance(msg, dict) or "content" not in msg:
                    stats["errors"].append(f"User {dump.get('github_login')}: Invalid message")
                    continue
                stats["total_messages"] += 1

        # Count snippets
        snippets_data = dump.get("snippets_data", {})
        snippets = snippets_data.get("snippets", [])
        if isinstance(snippets, list):
            stats["total_snippets"] += len(snippets)

        # Count presets
        presets_data = dump.get("presets_data", {})
        presets = presets_data.get("presets", {})
        if isinstance(presets, dict):
            stats["total_presets"] += len(presets)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Validate backfill dump file")
    parser.add_argument("dump_file", help="JSON dump file from localStorage export")
    args = parser.parse_args()

    print(f"Validating: {args.dump_file}\n")

    stats = validate_dump(args.dump_file)

    # Print statistics
    print("=" * 60)
    print("DUMP FILE STATISTICS")
    print("=" * 60)
    print(f"Total users:            {stats['total_users']}")
    print(f"Total conversations:    {stats['total_conversations']}")
    print(f"Total messages:         {stats['total_messages']}")
    print(f"Total snippets:         {stats['total_snippets']}")
    print(f"Total presets:          {stats['total_presets']}")

    if stats["warnings"]:
        print(f"\nWarnings ({len(stats['warnings'])}):")
        for warning in stats["warnings"][:10]:
            print(f"  ⚠ {warning}")
        if len(stats["warnings"]) > 10:
            print(f"  ... and {len(stats['warnings']) - 10} more")

    if stats["errors"]:
        print(f"\nErrors ({len(stats['errors'])}):")
        for error in stats["errors"][:10]:
            print(f"  ✗ {error}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")
        sys.exit(1)

    print("\n✓ Dump file is valid and ready for backfill")


if __name__ == "__main__":
    main()
