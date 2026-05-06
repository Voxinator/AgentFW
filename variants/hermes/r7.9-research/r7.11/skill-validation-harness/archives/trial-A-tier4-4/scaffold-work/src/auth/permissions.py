"""Permission helpers for record-level access control."""

from src.auth import User


def has_permission(user: User, record: dict) -> bool:
    """Return True iff record['owner_id'] == user.user_id."""
    return record.get("owner_id") == user.user_id


def has_permission_for_many(user: User, records: list[dict]) -> list[dict]:
    """Return only the records that the user has permission for."""
    return [r for r in records if has_permission(user, r)]
