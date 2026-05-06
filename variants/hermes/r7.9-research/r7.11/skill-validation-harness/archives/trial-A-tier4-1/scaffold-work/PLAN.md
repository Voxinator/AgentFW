# Export Feature Plan

## Phase 1: Core Serializers
- Objective: Implement CSV, JSON, and PDF serializer functions in src/export/.
- Paths: /tmp/r7.11-item8-scaffold/src/export/csv.py, /tmp/r7.11-item8-scaffold/src/export/json.py, /tmp/r7.11-item8-scaffold/src/export/pdf.py, /tmp/r7.11-item8-scaffold/src/export/formats.py
- Acceptance Criteria: Each serializer (CSV, JSON, PDF) defined in formats.py or specific files; signature (records: list[dict]) -> str|bytes; empty-list case handled.
- Size estimate: 3pt

## Phase 2: Auth & API Endpoints
- Objective: Implement permission checks in src/auth/permissions.py and GET endpoints in src/api/export.py.
- Paths: /tmp/r7.11-item8-scaffold/src/auth/permissions.py, /tmp/r7.11-item8-scaffold/src/api/export.py
- Acceptance Criteria: Endpoints verify ownership via permissions.py; media_types set correctly; 403 returned on permission failure.
- Size estimate: 3pt

## Phase 3: Tests & Documentation
- Objective: Implement pytest tests and update API documentation.
- Paths: /tmp/r7.11-item8-scaffold/tests/test_api_export.py, /tmp/r7.11-item8-scaffold/README.md
- Acceptance Criteria: All tests pass (including permission failures); README updated with export endpoint details.
- Acceptance Command: .venv/bin/pytest tests/
- Size estimate: 2pt
