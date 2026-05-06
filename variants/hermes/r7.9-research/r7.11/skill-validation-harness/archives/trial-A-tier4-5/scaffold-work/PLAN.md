# Export Feature Plan

## Phase 1: Core Serializers
- Objective: Implement CSV, JSON, and PDF serializer functions in src/export/.
- Paths: /tmp/r7.11-item8-scaffold/src/export/csv.py, /tmp/r7.11-item8-scaffold/src/export/json.py, /tmp/r7.11-item8-scaffold/src/export/pdf.py, /tmp/r7.11-item8-scaffold/src/export/formats.py
- Acceptance Criteria: serializers defined with signature (records: list[dict]) -> str|bytes; empty-list case handled.
- Size estimate: 3pt

## Phase 2: Auth & Permissions
- Objective: Implement permission checking logic in src/auth/permissions.py.
- Paths: /tmp/r7.11-item8-scaffold/src/auth/permissions.py
- Acceptance Criteria: has_permission(user, resource) function correctly validates ownership.
- Size estimate: 2pt

## Phase 3: API Endpoints
- Objective: Add export endpoints in src/api/export.py that use serializers and check permissions.
- Paths: /tmp/r7.11-item8-scaffold/src/api/export.py
- Acceptance Criteria: GET /export/{format} routes exist, call correct serializer, and enforce has_permission.
- Size estimate: 3pt

## Phase 4: Tests & Documentation
- Objective: Complete test suite and update API docs.
- Paths: /tmp/r7.11-item8-scaffold/tests/test_api_export.py, /tmp/r7.11-item8-scaffold/README.md
- Acceptance Criteria: pytest passes for all export scenarios including permission denial.
- Acceptance Command: .venv/bin/pytest /tmp/r7.11-item8-scaffold/tests/
- Size estimate: 2pt
