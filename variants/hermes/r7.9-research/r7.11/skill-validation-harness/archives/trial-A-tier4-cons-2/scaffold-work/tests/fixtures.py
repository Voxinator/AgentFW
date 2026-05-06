"""Shared test fixtures."""

from src.auth import User


def make_user(user_id: str = "u1") -> User:
    return User(user_id=user_id, email=f"{user_id}@example.com")


def make_record(owner_id: str = "u1", value: int = 42) -> dict:
    return {"owner_id": owner_id, "value": value, "name": f"record-{value}"}
