#!/usr/bin/env python3
"""Backfill localStorage data into PostgreSQL.

Usage:
    python scripts/backfill_localStorage.py --dry-run <dump_file>
    python scripts/backfill_localStorage.py <dump_file>
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any
import argparse

# Setup database
import os
os.environ.setdefault("DATABASE_URL", "postgresql://devforge:devforge@localhost:5432/devforge")

from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import User, Conversation, Message, Snippet, UserPreset


class BackfillStats:
    """Track backfill statistics."""

    def __init__(self):
        self.users_created = 0
        self.conversations_created = 0
        self.messages_created = 0
        self.snippets_created = 0
        self.presets_created = 0
        self.errors = []

    def report(self):
        """Print statistics."""
        print("\n" + "=" * 60)
        print("BACKFILL STATISTICS")
        print("=" * 60)
        print(f"Users created:          {self.users_created}")
        print(f"Conversations created:  {self.conversations_created}")
        print(f"Messages created:       {self.messages_created}")
        print(f"Snippets created:       {self.snippets_created}")
        print(f"Presets created:        {self.presets_created}")
        print(f"Errors:                 {len(self.errors)}")

        if self.errors:
            print("\nErrors:")
            for err in self.errors[:10]:
                print(f"  - {err}")


def extract_localStorage_dump(file_path: str) -> List[Dict[str, Any]]:
    """Load localStorage dump from JSON file.

    Expected format:
    [
        {
            "github_id": 12345,
            "github_login": "username",
            "github_name": "User Name",
            "github_avatar_url": "https://...",
            "chat_data": { "tabs": [...], ... },
            "enhance_data": { ... },
            "snippets_data": { "snippets": [...] },
            "presets_data": { "presets": [...] }
        }
    ]
    """
    with open(file_path) as f:
        return json.load(f)


def backfill_user(dump: Dict[str, Any], db: Session, stats: BackfillStats, dry_run: bool = False):
    """Backfill single user's data."""
    try:
        github_id = dump.get("github_id")
        github_login = dump.get("github_login")

        if not github_id or not github_login:
            stats.errors.append(f"Invalid user dump: missing github_id or github_login")
            return

        # Create/get user
        user = db.query(User).filter_by(github_id=github_id).first()
        if not user:
            user = User(
                github_id=github_id,
                github_login=github_login,
                github_name=dump.get("github_name"),
                github_avatar_url=dump.get("github_avatar_url"),
            )
            db.add(user)
            if not dry_run:
                db.flush()
            stats.users_created += 1

        # Backfill conversations & messages
        chat_data = dump.get("chat_data", {})
        for tab in chat_data.get("tabs", []):
            try:
                created_at = datetime.fromisoformat(tab.get("created_at", "2026-01-01T00:00:00"))
            except (ValueError, TypeError):
                created_at = datetime.utcnow()

            conv = Conversation(
                id=uuid4(),
                user_id=user.id,
                name=tab.get("name", "Chat"),
                created_at=created_at,
            )
            db.add(conv)
            if not dry_run:
                db.flush()
            stats.conversations_created += 1

            # Backfill messages in conversation
            for msg in tab.get("msgs", []):
                try:
                    message = Message(
                        conversation_id=conv.id,
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                        tokens_used=msg.get("tokens", 0),
                        created_at=datetime.utcnow(),
                    )
                    db.add(message)
                    stats.messages_created += 1
                except Exception as e:
                    stats.errors.append(f"Failed to create message in {github_login}: {e}")

        # Backfill snippets
        snippets_data = dump.get("snippets_data", {})
        for snippet in snippets_data.get("snippets", []):
            try:
                snip = Snippet(
                    user_id=user.id,
                    title=snippet.get("title", "Untitled"),
                    language=snippet.get("language"),
                    content=snippet.get("content", ""),
                    created_at=datetime.utcnow(),
                )
                db.add(snip)
                stats.snippets_created += 1
            except Exception as e:
                stats.errors.append(f"Failed to create snippet in {github_login}: {e}")

        # Backfill presets
        presets_data = dump.get("presets_data", {})
        for preset_name, preset_content in presets_data.get("presets", {}).items():
            try:
                preset = UserPreset(
                    user_id=user.id,
                    preset_name=preset_name,
                    instructions=preset_content.get("instructions"),
                    rules=preset_content.get("rules"),
                    skills=preset_content.get("skills", []),
                    ai_model=preset_content.get("ai_model"),
                    provider=preset_content.get("provider"),
                    created_at=datetime.utcnow(),
                )
                db.add(preset)
                stats.presets_created += 1
            except Exception as e:
                stats.errors.append(f"Failed to create preset in {github_login}: {e}")

        if not dry_run:
            db.commit()
        else:
            db.rollback()

        status = "[DRY RUN]" if dry_run else "✓"
        print(f"{status} Backfilled user {github_login}")

    except Exception as e:
        stats.errors.append(f"Failed to backfill user {dump.get('github_login')}: {e}")
        db.rollback()


def main():
    parser = argparse.ArgumentParser(description="Backfill localStorage to PostgreSQL")
    parser.add_argument("dump_file", help="JSON dump file from extract_localStorage.py")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing")
    args = parser.parse_args()

    # Load dump file
    try:
        dumps = extract_localStorage_dump(args.dump_file)
    except FileNotFoundError:
        print(f"✗ Dump file not found: {args.dump_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in dump file: {args.dump_file}")
        sys.exit(1)

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Loaded {len(dumps)} users from dump")

    # Backfill each user
    db = SessionLocal()
    stats = BackfillStats()

    try:
        for dump in dumps:
            backfill_user(dump, db, stats, dry_run=args.dry_run)
    finally:
        db.close()

    # Report
    stats.report()

    if args.dry_run:
        print("\n[DRY RUN] No data was modified. Run without --dry-run to execute.")
    else:
        print("\n✓ Backfill complete!")


if __name__ == "__main__":
    main()
