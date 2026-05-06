from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from src.api.export import router, get_current_user
from src.auth import User

app = FastAPI()
app.include_router(router)

# Mock user u1 (Alice)
alice = User(user_id="u1", email="alice@example.com")
# Mock user u2 (Bob)
bob = User(user_id="u2", email="bob@example.com")

def override_get_current_user_alice():
    return alice

def override_get_current_user_bob():
    return bob

client = TestClient(app)

def test_csv_endpoint_returns_text_csv_content_type():
    """Test GET /api/export/csv returns correct content type."""
    app.dependency_overrides[get_current_user] = override_get_current_user_alice
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    app.dependency_overrides.clear()

def test_json_endpoint_returns_application_json_content_type():
    """Test GET /api/export/json returns correct content type."""
    app.dependency_overrides[get_current_user] = override_get_current_user_alice
    response = client.get("/api/export/json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    app.dependency_overrides.clear()

def test_pdf_endpoint_returns_application_pdf_content_type():
    """Test GET /api/export/pdf returns correct content type."""
    app.dependency_overrides[get_current_user] = override_get_current_user_alice
    response = client.get("/api/export/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    app.dependency_overrides.clear()

def test_single_record_export_success():
    """Test accessing an owned record returns 200."""
    app.dependency_overrides[get_current_user] = override_get_current_user_alice
    # Record 1 is owned by u1
    response = client.get("/api/export/1/csv")
    assert response.status_code == 200
    app.dependency_overrides.clear()

def test_single_record_export_forbidden():
    """Test accessing a record owned by someone else returns 403."""
    app.dependency_overrides[get_current_user] = override_get_current_user_alice
    # Record 3 is owned by u2
    response = client.get("/api/export/3/csv")
    assert response.status_code == 403
    app.dependency_overrides.clear()

def test_single_record_not_found():
    """Test accessing a non-existent record returns 404."""
    app.dependency_overrides[get_current_user] = override_get_current_user_alice
    response = client.get("/api/export/999/csv")
    assert response.status_code == 404
    app.dependency_overrides.clear()
