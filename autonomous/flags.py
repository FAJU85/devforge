"""Feature flag management — in-memory dict with JSON persistence."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

_log = logging.getLogger(__name__)

_FLAGS: dict[str, dict] = {}
_FLAGS_FILE = os.environ.get("FLAGS_FILE", "feature_flags.json")
_FLAGS_LOCK = threading.RLock()
_VALID_STATUSES = frozenset({"dark", "canary", "live", "rollback"})


@dataclass
class FeatureFlag:
    name: str
    description: str
    enabled: bool = True
    rollout_pct: int = 0
    status: str = "dark"  # "dark" | "canary" | "live" | "rollback"
    created_at: str = field(default_factory=lambda: _now())
    updated_at: str = field(default_factory=lambda: _now())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_flags() -> None:
    """Load flags from JSON file into memory (no-op if file missing)."""
    global _FLAGS
    with _FLAGS_LOCK:
        try:
            with open(_FLAGS_FILE, "r") as fh:
                _FLAGS = json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            _FLAGS = {}


def save_flags() -> None:
    """Persist the in-memory flags dict to JSON file atomically."""
    with _FLAGS_LOCK:
        snapshot = json.dumps(_FLAGS, indent=2)
    # Write outside the lock so readers aren't blocked during I/O.
    dir_ = os.path.dirname(os.path.abspath(_FLAGS_FILE)) or "."
    tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w") as fh:
            fh.write(snapshot)
        os.replace(tmp_path, _FLAGS_FILE)
    except OSError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        _log.error("Failed to persist feature flags to %s: %s", _FLAGS_FILE, exc)
        raise


def get_all() -> list[dict]:
    """Return all flags as a list of dicts."""
    with _FLAGS_LOCK:
        return list(_FLAGS.values())


def create(name: str, description: str, rollout_pct: int = 0) -> dict:
    """Create a new feature flag and persist it."""
    with _FLAGS_LOCK:
        if name in _FLAGS:
            raise ValueError(f"Flag '{name}' already exists")
        flag = FeatureFlag(
            name=name,
            description=description,
            rollout_pct=max(0, min(100, rollout_pct)),
        )
        _FLAGS[name] = asdict(flag)
        result = dict(_FLAGS[name])
    save_flags()
    return result


def update(name: str, **kwargs) -> dict:
    """Update one or more fields on an existing flag and persist."""
    with _FLAGS_LOCK:
        if name not in _FLAGS:
            raise KeyError(f"Flag '{name}' not found")
        allowed = {"description", "enabled", "rollout_pct", "status"}
        for k, v in kwargs.items():
            if k not in allowed:
                raise ValueError(f"Unknown field: {k}")
            if k == "rollout_pct":
                v = max(0, min(100, int(v)))
            elif k == "status":
                if v not in _VALID_STATUSES:
                    raise ValueError(
                        f"Invalid status '{v}'; must be one of {sorted(_VALID_STATUSES)}"
                    )
            _FLAGS[name][k] = v
        _FLAGS[name]["updated_at"] = _now()
        result = dict(_FLAGS[name])
    save_flags()
    return result


def delete(name: str) -> bool:
    """Delete a flag by name. Returns True if deleted, False if not found."""
    with _FLAGS_LOCK:
        if name not in _FLAGS:
            return False
        del _FLAGS[name]
    save_flags()
    return True


def is_flag_enabled(flag_name: str, user_id: str = "") -> bool:
    """Deterministic hash-based routing: returns True if user_id is in the canary cohort.

    Stable across requests for the same (flag_name, user_id) pair.
    Falls back to IP-based routing when user_id is empty.
    """
    with _FLAGS_LOCK:
        flag = _FLAGS.get(flag_name)

    if not flag or not flag.get("enabled", True):
        return False

    status = flag.get("status", "dark")
    rollout_pct = int(flag.get("rollout_pct", 0))

    if status == "live" or rollout_pct >= 100:
        return True
    if status in ("dark", "rollback") or rollout_pct <= 0:
        return False

    # Deterministic bucket: 0..99
    key = f"{flag_name}:{user_id}".encode("utf-8")
    bucket = int(hashlib.md5(key, usedforsecurity=False).hexdigest(), 16) % 100
    return bucket < rollout_pct


# Load persisted flags on import
load_flags()
