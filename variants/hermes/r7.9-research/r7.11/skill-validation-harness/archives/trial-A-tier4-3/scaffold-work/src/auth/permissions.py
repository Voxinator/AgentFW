"""Permission helpers for record-level access control."""

from src.auth import User

def has_permission(user: User, record: dict) -> bool:
    """
    Return True if the user has permission to access the record.
    Permission is granted if the record's owner_id matches the user's user_id.
    """
    if not record:
        return False
    return record.get("owner_id") == user.user_id

def has_permission_for_many(user: User, records: list[dict]) -> bool:
    """
    Return True if the user has permission for ALL provided records.
    """
    return all(has_permission(user, r) for r in records)

if __name__ == "__main__":
    from src.auth import User
    # Dummy data for verification
    dummy_user = User(user_id="user_123")
    record_1 = {"owner_id": "user_123", "id": "rec_1"}
    record_2 = {"owner_id": "user_456", "id": "rec_2"}
    
    print(f"Testing has_permission: {has_permission(dummy_user, record_1)}")
    print(f"Testing has_permission (fail): {has_permission(dummy_user, record_2)}")
    print(f"Testing has_permission_for_many: {has_permission_for_many(dummy_user, [record_1, record_1])}")

