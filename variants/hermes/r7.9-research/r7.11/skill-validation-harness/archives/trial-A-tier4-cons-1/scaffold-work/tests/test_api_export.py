from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.export import router
from src.auth import User, get_current_user

app = FastAPI()
app.include_router(router, prefix="/api")

# Mock user for testing
TEST_USER = User(user_id="u1", email="test@example.com")

def override_get_current_user():
    return TEST_USER

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_export_csv_success():
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    # Check if it contains data from u1 (Item 1 and Item 2)
    assert b"Item 1" in response.content
    assert b"Item 2" in response.content
    assert b"Item 3" not in response.content  # u2's record

def test_export_json_success():
    response = client.get("/api/export/json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert b"Item 1" in response.content
    assert b"Item 3" not in response.content

def test_export_pdf_success():
    response = client.get("/api/export/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert b"--- DOCUMENT START ---" in response.content

def test_export_invalid_format():
    response = client.get("/api/export/xml")
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported format: xml"

def test_export_no_records_for_user():
    # Temporarily override user to one with no records
    empty_user = User(user_id="u99", email="none@example.com")
    app.dependency_overrides[get_current_user] = lambda: empty_user
    
    response = client.get("/api/export/json")
    assert response.status_code == 404
    assert response.json()["detail"] == "No records found for user"
    
    # Reset dependency
    app.dependency_overrides[get_current_user] = override_get_current_user
