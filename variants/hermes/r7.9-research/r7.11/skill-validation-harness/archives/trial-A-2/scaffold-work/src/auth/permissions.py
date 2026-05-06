"""Permission helpers for record-level access control."""

from src.auth import User


def has_permission(user: User, record: dict) -> bool:
    """Return True iff record['owner_id'] == user.user_id."""
    return record.get("owner_id") == user.user_id
