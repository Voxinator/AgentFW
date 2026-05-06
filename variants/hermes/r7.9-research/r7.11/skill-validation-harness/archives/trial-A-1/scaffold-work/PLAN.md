# Export Feature Plan

## Phase 1: Core Serializers
- Objective: Implement CSV, JSON, and PDF serializer functions in the export module.
- Paths: /tmp/r7.11-item8-scaffold/src/export/csv.py, /tmp/r7.11-item8-scaffold/src/export/json.py, /tmp/r7.11-item8-scaffold/src/export/pdf.py
- Acceptance Criteria: Functions defined for each format (records: list[dict]) -> str|bytes; handles empty lists.
- Size estimate: 3pt

## Phase 2: Permissions & API Integration
- Objective: Implement permission checks and the API export endpoint.
- Paths: /tmp/r7.11-item8-scaffold/src/auth/permissions.py, /tmp/r7.11-item8-scaffold/src/api/export.py
- Acceptance Criteria: `has_permission` logic implemented; `export` endpoint in `api/export.py` uses it and calls appropriate serializers.
- Size estimate: 3pt

## Phase 3: Tests & Documentation
- Objective: Implement comprehensive tests and update API documentation.
- Paths: /tmp/r7.11-item8-scaffold/tests/test_api_export.py, /tmp/r7.11-item8-scaffold/tests/test_csv.py, /tmp/r7.11-item8-scaffold/README.md
- Acceptance Criteria: Pytest passes for all export and permission scenarios; README updated with export API details.
- Acceptance Command: .venv/bin/pytest /tmp/r7.11-item8-scaffold/tests/
- Size estimate: 2pt
