# Export Feature Plan

## Phase 1: Core Serializers
- Objective: Implement CSV, JSON, and PDF serializer functions in the export directory.
- Paths: /tmp/r7.11-item8-scaffold/src/export/csv.py, /tmp/r7.11-item8-scaffold/src/export/json.py, /tmp/r7.11-item8-scaffold/src/export/pdf.py, /tmp/r7.11-item8-scaffold/src/export/formats.py
- Acceptance Criteria: Functions defined with signature (records: list[dict]) -> str|bytes; handles empty lists.
- Size estimate: 3pt

## Phase 2: API Endpoints + Permissions
- Objective: Implement export endpoints in src/api/export.py and permission checks in src/auth/permissions.py.
- Paths: /tmp/r7.11-item8-scaffold/src/api/export.py, /tmp/r7.11-item8-scaffold/src/auth/permissions.py
- Acceptance Criteria: Endpoints exist, use permission checks to filter data ownership, and return correct media types.
- Size estimate: 3pt

## Phase 3: Tests + Documentation
- Objective: Implement tests for serializers, API, and permissions, and update API docs.
- Paths: /tmp/r7.11-item8-scaffold/tests/test_api_export.py, /tmp/r7.11-item8-scaffold/tests/test_csv.py, /tmp/r7.11-item8-scaffold/README.md
- Acceptance Criteria: All tests pass; README updated with new API details.
- Acceptance Command: .venv/bin/pytest /tmp/r7.11-item8-scaffold/tests
- Size estimate: 3pt
