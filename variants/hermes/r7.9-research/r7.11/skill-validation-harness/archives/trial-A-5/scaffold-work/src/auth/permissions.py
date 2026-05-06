"""Permission helpers for record-level access control."""

from src.auth import User


def has_permission(user: User, record: dict) -> bool:
    """Return True iff record['owner_id'] == user.user_id."""
    return record.get("owner_id") == user.user_id

def filter_records_for_user(user: User, records: list[dict]) -> list[dict]:
    """Return only records owned by the user."""
    return [r for r in records if has_permission(user, r)]
