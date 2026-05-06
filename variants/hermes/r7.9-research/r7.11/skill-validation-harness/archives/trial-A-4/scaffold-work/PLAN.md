# Export Feature Plan

## Phase 1: Core Serializers
- Objective: Implement CSV, JSON, and PDF serializer functions in src/export/.
- Paths: /tmp/r7.11-item8-scaffold/src/export/csv.py, /tmp/r7.11-item8-scaffold/src/export/json.py, /tmp/r7.11-item8-scaffold/src/export/pdf.py, /tmp/r7.11-item8-scaffold/src/export/formats.py
- Acceptance Criteria: Serializers defined with signature (records: list[dict]) -> str|bytes; handle empty lists; formats.py provides a unified interface.
- Size estimate: 3pt

## Phase 2: API Endpoints and Permissions
- Objective: Implement GET endpoints in src/api/export.py that use src/auth/permissions.py to enforce ownership.
- Paths: /tmp/r7.11-item8-scaffold/src/api/export.py, /tmp/r7.11-item8-scaffold/src/auth/permissions.py
- Acceptance Criteria: Endpoints exist for CSV, JSON, PDF; they check user ownership via permissions module; return appropriate media types.
- Size estimate: 3pt

## Phase 3: Testing and Documentation
- Objective: Implement comprehensive tests and update API documentation.
- Paths: /tmp/r7.11-item8-scaffold/tests/test_api_export.py, /tmp/r7.11-item8-scaffold/tests/test_csv.py, /tmp/r7.11-item8-scaffold/README.md
- Acceptance Criteria: All tests pass (including permission-denied cases); README.md updated with export endpoint details.
- Acceptance Command: .venv/bin/pytest /tmp/r7.11-item8-scaffold/tests
- Size estimate: 2pt
