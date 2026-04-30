"""Auth helpers."""


class User:
    """Minimal user model for scaffold tests."""

    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email


def get_current_user() -> User:
    """Stub: returns a fixed scaffold user. Real impl would read request context."""
    return User(user_id="u1", email="alice@example.com")
