"""Permission helpers for record-level access control."""

from src.auth import User


def check_ownership(user: User, resource_owner_id: str) -> bool:
    """Return True iff resource_owner_id == user.user_id."""
    return resource_owner_id == user.user_id

def has_permission(user: User, record: dict) -> bool:
    """Return True iff record['owner_id'] == user.user_id."""
    return record.get("owner_id") == user.user_id
