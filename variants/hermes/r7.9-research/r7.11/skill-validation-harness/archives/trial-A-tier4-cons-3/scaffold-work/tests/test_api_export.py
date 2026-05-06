"""Tests for src.api.export (scaffold — worker will populate endpoint tests)."""

from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.export import router

test_app = FastAPI()
test_app.include_router(router)

# Mock dependencies for testing
def test_csv_endpoint_returns_text_csv_content_type():
    """Worker should implement GET /api/export/csv; test checks Content-Type header."""
    client = TestClient(test_app)
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "user data 1" in response.text

def test_json_endpoint_returns_application_json_content_type():
    """Worker should implement GET /api/export/json; test checks Content-Type header."""
    client = TestClient(test_app)
    response = client.get("/api/export/json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    # Check if JSON is valid and contains expected data
    import json
    data = json.loads(response.text)
    assert len(data) == 2  # u1 has 2 records

def test_pdf_endpoint_returns_application_pdf_content_type():
    """Worker should implement GET /api/export/pdf; test checks Content-Type header."""
    client = TestClient(test_app)
    response = client.get("/api/export/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert isinstance(response.content, bytes)

def test_invalid_format_returns_400():
    """Worker should return 400 for unsupported formats."""
    client = TestClient(test_app)
    response = client.get("/api/export/xml")
    assert response.status_code == 400
    assert "Unsupported format" in response.json()["detail"]
