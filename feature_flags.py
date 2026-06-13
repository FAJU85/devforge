"""Feature flag system for gradual rollout (10% → 50% → 100%)."""

import os
import hashlib
from typing import Optional, Dict, Any


class FeatureFlags:
    """Feature flag manager with percentage-based rollout."""

    def __init__(self):
        self.flags: Dict[str, Dict[str, Any]] = {
            "enable_db_sync": {
                "enabled": os.environ.get("ENABLE_DB_SYNC", "false").lower() == "true",
                "rollout_percentage": int(os.environ.get("DB_SYNC_ROLLOUT_PERCENTAGE", "0")),
                "description": "Enable database persistence for conversations (v2 API)",
            }
        }

    def is_enabled(self, flag_name: str, user_id: Optional[str] = None) -> bool:
        """Check if a flag is enabled for a user.

        Uses consistent hashing so same user always gets same result.
        """
        if flag_name not in self.flags:
            return False

        flag = self.flags[flag_name]
        if not flag["enabled"]:
            return False

        rollout_pct = flag["rollout_percentage"]
        if rollout_pct >= 100:
            return True
        if rollout_pct <= 0:
            return False

        # Consistent hashing: same user always gets same result
        if not user_id:
            user_id = "anonymous"

        hash_value = int(hashlib.md5(f"{flag_name}:{user_id}".encode()).hexdigest(), 16)
        bucket = hash_value % 100
        return bucket < rollout_pct

    def get_flag_status(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """Get flag metadata."""
        return self.flags.get(flag_name)

    def update_rollout(self, flag_name: str, percentage: int) -> None:
        """Update rollout percentage (0-100)."""
        if flag_name in self.flags:
            self.flags[flag_name]["rollout_percentage"] = max(0, min(100, percentage))

    def set_enabled(self, flag_name: str, enabled: bool) -> None:
        """Enable/disable a flag."""
        if flag_name in self.flags:
            self.flags[flag_name]["enabled"] = enabled


# Global instance
flags = FeatureFlags()


def is_db_sync_enabled(user_id: Optional[str] = None) -> bool:
    """Check if database sync is enabled for user."""
    return flags.is_enabled("enable_db_sync", user_id)


def get_rollout_percentage() -> int:
    """Get current rollout percentage."""
    flag = flags.get_flag_status("enable_db_sync")
    return flag["rollout_percentage"] if flag else 0
