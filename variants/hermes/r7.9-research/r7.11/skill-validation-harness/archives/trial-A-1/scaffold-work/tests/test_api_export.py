import pytest
from src.api.export import export_data
from src.auth import User

@pytest.fixture
def user():
    return User(user_id="user_123")

@pytest.fixture
def valid_records():
    return [
        {"id": 1, "name": "Item 1", "owner_id": "user_123"},
        {"id": 2, "name": "Item 2", "owner_id": "user_123"},
    ]

@pytest.fixture
def unauthorized_records():
    return [
        {"id": 1, "name": "Item 1", "owner_id": "user_123"},
        {"id": 2, "name": "Item 2", "owner_id": "other_user"},
    ]

def test_export_json_success(user, valid_records):
    result = export_data(user, valid_records, "json")
    assert isinstance(result, str)
    assert '"id": 1' in result

def test_export_csv_success(user, valid_records):
    result = export_data(user, valid_records, "csv")
    assert isinstance(result, str)
    assert "id,name" in result

def test_export_pdf_success(user, valid_records):
    result = export_data(user, valid_records, "pdf")
    assert isinstance(result, bytes)
    assert len(result) > 0

def test_export_permission_denied(user, unauthorized_records):
    with pytest.raises(PermissionError, match="User does not have permission"):
        export_data(user, unauthorized_records, "json")

def test_export_unsupported_format(user, valid_records):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_data(user, valid_records, "xml")

def test_export_empty_records(user):
    # Testing that empty records still work (returns empty serialization)
    assert export_data(user, [], "json") == "[]"
    assert export_data(user, [], "csv") == ""
    assert export_data(user, [], "pdf") == b""
