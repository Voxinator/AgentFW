"""Tests for src.api.export."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.export import router

app = FastAPI()
app.include_router(router, prefix="/api")

@pytest.fixture
def client():
    return TestClient(app)

def test_csv_endpoint_returns_text_csv_content_type(client):
    """Test GET /api/export/csv returns text/csv."""
    response = client.get("/api/export/csv?user_id=user_123&record_ids=rec_1&record_ids=rec_2")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

def test_json_endpoint_returns_application_json_content_type(client):
    """Test GET /api/export/json returns application/json."""
    response = client.get("/api/export/json?user_id=user_123&record_ids=rec_1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

def test_pdf_endpoint_returns_application_pdf_content_type(client):
    """Test GET /api/export/pdf returns application/pdf."""
    response = client.get("/api/export/pdf?user_id=user_123&record_ids=rec_1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

def test_export_forbidden_error(client):
    """Test that requesting a forbidden record returns 403."""
    # rec_forbidden_1 will be assigned to 'other_user' in the mock logic
    response = client.get("/api/export/csv?user_id=user_123&record_ids=rec_forbidden_1")
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied for one or more records"

def test_export_invalid_format(client):
    """Test that an unsupported format returns 400."""
    response = client.get("/api/export/xml?user_id=user_123&record_ids=rec_1")
    assert response.status_code == 400
    assert "Unsupported format" in response.json()["detail"]
