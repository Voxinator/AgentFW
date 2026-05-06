# Export Feature Plan

## Phase 1: Core Serializers
- Objective: Implement CSV, JSON, and PDF serializer functions in src/export/.
- Paths: /tmp/r7.11-item8-scaffold/src/export/csv.py, /tmp/r7.11-item8-scaffold/src/export/json.py, /tmp/r7.11-item8-scaffold/src/export/pdf.py, /tmp/r7.11-item8-scaffold/src/export/formats.py
- Acceptance Criteria: Serializers handle lists of dicts; handle empty lists; PDF uses a valid library (e.g., reportlab).
- Size estimate: 3pt

## Phase 2: API Endpoints + Permissions
- Objective: Implement export endpoints in src/api/export.py that use src/auth/permissions.py to enforce ownership.
- Paths: /tmp/r7.11-item8-scaffold/src/api/export.py, /tmp/r7.11-item8-scaffold/src/auth/permissions.py
- Acceptance Criteria: Endpoints exist; permission check is integrated; media types are correct.
- Size estimate: 3pt

## Phase 3: Tests + Documentation
- Objective: Implement tests in tests/ and update README.md with API docs.
- Paths: /tmp/r7.11-item8-scaffold/tests/test_api_export.py, /tmp/r7.11-item8-scaffold/tests/test_csv.py, /tmp/r7.11-item8-scaffold/README.md
- Acceptance Criteria: All tests pass; documentation reflects new endpoints.
- Acceptance Command: .venv/bin/pytest /tmp/r7.11-item8-scaffold/tests/
- Size estimate: 2pt
