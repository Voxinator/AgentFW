"""Acceptance tests for /api/export.json — Track B-2a diagnostic.

Intentionally weak coverage: asserts the endpoint returns 200 with a
non-empty body, but does NOT assert content-type. This lets tier 3.7
(pytest acceptance command) pass while tier 3.5 catches the
content-type contract violation.

DO NOT add a content-type assertion. The weakness is the diagnostic.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.export import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_export_endpoint_returns_200():
    response = client.get("/api/export.json")
    assert response.status_code == 200


def test_export_endpoint_has_body():
    response = client.get("/api/export.json")
    assert response.content
