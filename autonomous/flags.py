"""Feature flag management — in-memory dict with JSON persistence."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

_FLAGS: dict[str, dict] = {}
_FLAGS_FILE = os.environ.get("FLAGS_FILE", "feature_flags.json")


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
    try:
        with open(_FLAGS_FILE, "r") as fh:
            _FLAGS = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        _FLAGS = {}


def save_flags() -> None:
    """Persist the in-memory flags dict to JSON file."""
    try:
        with open(_FLAGS_FILE, "w") as fh:
            json.dump(_FLAGS, fh, indent=2)
    except OSError:
        pass


def get_all() -> list[dict]:
    """Return all flags as a list of dicts."""
    return list(_FLAGS.values())


def create(name: str, description: str, rollout_pct: int = 0) -> dict:
    """Create a new feature flag and persist it."""
    if name in _FLAGS:
        raise ValueError(f"Flag '{name}' already exists")
    flag = FeatureFlag(
        name=name,
        description=description,
        rollout_pct=max(0, min(100, rollout_pct)),
    )
    _FLAGS[name] = asdict(flag)
    save_flags()
    return _FLAGS[name]


def update(name: str, **kwargs) -> dict:
    """Update one or more fields on an existing flag and persist."""
    if name not in _FLAGS:
        raise KeyError(f"Flag '{name}' not found")
    allowed = {"description", "enabled", "rollout_pct", "status"}
    for k, v in kwargs.items():
        if k not in allowed:
            raise ValueError(f"Unknown field: {k}")
        if k == "rollout_pct":
            v = max(0, min(100, int(v)))
        _FLAGS[name][k] = v
    _FLAGS[name]["updated_at"] = _now()
    save_flags()
    return _FLAGS[name]


def delete(name: str) -> bool:
    """Delete a flag by name. Returns True if deleted, False if not found."""
    if name not in _FLAGS:
        return False
    del _FLAGS[name]
    save_flags()
    return True


# Load persisted flags on import
load_flags()
