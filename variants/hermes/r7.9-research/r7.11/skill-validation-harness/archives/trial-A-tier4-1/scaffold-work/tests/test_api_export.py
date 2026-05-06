from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.export import router
from src.auth import get_current_user, User

app = FastAPI()
app.include_router(router)

# Mock user for testing
TEST_USER = User(user_id="u1", email="alice@example.com")

def override_get_current_user():
    return TEST_USER

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_csv_endpoint_success():
    # Record 1 belongs to u1
    response = client.get("/export/csv/1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"

def test_csv_endpoint_forbidden():
    # Record 2 belongs to u2
    response = client.get("/export/csv/2")
    assert response.status_code == 403

def test_json_endpoint_success():
    response = client.get("/export/json/1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

def test_pdf_endpoint_success():
    response = client.get("/export/pdf/1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

def test_not_found():
    response = client.get("/export/csv/999")
    assert response.status_code == 404
