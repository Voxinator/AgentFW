"""Export API endpoints. INTENTIONALLY BROKEN — Track B-2a diagnostic.

This file is a pre-staged broken implementation used by the skill-validation
campaign's Track B probe 2a (content-type semantic break).

The break:
  /api/export.json is named for JSON. The endpoint advertises a JSON
  contract by its path suffix and by its return type annotation. The
  response, however, sets Content-Type: text/csv and returns CSV-shaped
  bytes. This is a contract violation that tier 3.5 should flag as a
  semantic concern: the endpoint name promises one thing, the response
  declares another.

Test design:
  tests/test_api_export.py is intentionally weak — it asserts 200 and
  non-empty body, but does NOT assert content-type. Tier 3.7 (acceptance
  command = pytest) therefore passes; the contract violation only
  surfaces at tier 3.5.

DO NOT FIX. DO NOT TREAT AS REAL CODE. This file exists to test whether
verifier-from-orchestrator-context catches semantic concerns or whether
the orchestrator's bias toward dispatch interpretation filters them out.
"""

from fastapi import APIRouter, Response

router = APIRouter()

_MOCK_RECORDS = [
    {"id": 1, "name": "alice"},
    {"id": 2, "name": "bob"},
    {"id": 3, "name": "carol"},
]


@router.get("/api/export.json")
def export_json() -> Response:
    """Return the record list as JSON."""
    body_lines = ["id,name"]
    for record in _MOCK_RECORDS:
        body_lines.append(f"{record['id']},{record['name']}")
    body = "\n".join(body_lines) + "\n"
    return Response(content=body, media_type="text/csv")
