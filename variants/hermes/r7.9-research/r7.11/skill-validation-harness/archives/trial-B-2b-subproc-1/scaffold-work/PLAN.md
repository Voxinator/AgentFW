# Export Feature Plan

## Phase 1: Core Serializers
- Objective: Implement CSV, JSON, and PDF serializer functions.
- Paths: /tmp/r7.11-item8-scaffold/src/export/csv.py, /tmp/r7.11-item8-scaffold/src/export/json.py, /tmp/r7.11-item8-scaffold/src/export/pdf.py
- Acceptance Criteria: Each serializer defined with signature (records: list[dict]) -> str|bytes; empty-list case handled; PDF uses a valid library like reportlab.
- Size estimate: 3pt

## Phase 2: API Endpoints + Permission Logic
- Objective: Add export endpoints in src/api/export.py with ownership-based permission filtering.
- Paths: /tmp/r7.11-item8-scaffold/src/api/export.py, /tmp/r7.11-item8-scaffold/src/auth/permissions.py
- Acceptance Criteria: 3 GET endpoints; each verifies user ownership of records before serialization; correct media types returned.
- Size estimate: 3pt

## Phase 3: Tests + Documentation
- Objective: Implement test coverage for all formats and permission scenarios, and update API docs.
- Paths: /tmp/r7.11-item8-scaffold/tests/test_export.py, /tmp/r7.11-item8-scaffold/docs/api.md
- Acceptance Criteria: pytest passes for all formats and permission-denied cases; docs/ reflects new endpoints and usage.
- Acceptance Command: .venv/bin/python -m pytest tests/test_export.py
- Size estimate: 2pt
