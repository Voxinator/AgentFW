from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.export import router
from src.auth import User
from src.auth.permissions import has_permission

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_csv_endpoint_returns_text_csv_content_type():
    """Test GET /api/export/csv returns correct content type."""
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    assert "owner_id" in response.text

def test_json_endpoint_returns_application_json_content_type():
    """Test GET /api/export/json returns correct content type."""
    response = client.get("/api/export/json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert isinstance(response.json(), list)

def test_pdf_endpoint_returns_application_pdf_content_type():
    """Test GET /api/export/pdf returns correct content type."""
    response = client.get("/api/export/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0
