"""Append-only evolution cycle audit log."""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone

_log = logging.getLogger(__name__)
_AUDIT_FILE = os.environ.get("AUDIT_FILE", "evolution_audit.json")
_AUDIT_LOCK = threading.Lock()
_MAX_ENTRIES = 1000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(
    flag_name: str,
    action: str,         # "rollout" | "hold" | "rollback" | "promote_live" | "error"
    reason: str,
    metrics: dict,       # the canary metrics used for this decision
    from_pct: int,
    to_pct: int,
) -> None:
    """Append one decision to the audit log."""
    entry = {
        "timestamp": _now(),
        "flag": flag_name,
        "action": action,
        "reason": reason,
        "metrics": metrics,
        "from_pct": from_pct,
        "to_pct": to_pct,
    }
    with _AUDIT_LOCK:
        events = _load()
        events.append(entry)
        if len(events) > _MAX_ENTRIES:
            events = events[-_MAX_ENTRIES:]
        _save(events)


def get_history(flag_name: str | None = None, limit: int = 100) -> list[dict]:
    """Return recent history, most-recent first."""
    events = _load()
    if flag_name:
        events = [e for e in events if e.get("flag") == flag_name]
    return list(reversed(events[-limit:]))


def _load() -> list:
    try:
        with open(_AUDIT_FILE, "r") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(events: list) -> None:
    try:
        with open(_AUDIT_FILE, "w") as fh:
            json.dump(events, fh, indent=2)
    except OSError as exc:
        _log.error("Failed to write audit log %s: %s", _AUDIT_FILE, exc)
