# Export Feature Plan

## Phase 1: Core Serializers
- Objective: Implement CSV, JSON, and PDF serializer functions in src/export/serializers.py.
- Paths: /tmp/r7.11-item8-scaffold/src/export/serializers.py
- Acceptance Criteria: Serializers handle list[dict] input; support CSV, JSON, and PDF formats.
- Size estimate: 3pt

## Phase 2: API Endpoints + Permissions
- Objective: Implement export endpoints in src/api/export.py that use src/auth/permissions.py to enforce ownership.
- Paths: /tmp/r7.11-item8-scaffold/src/api/export.py, /tmp/r7.11-item8-scaffold/src/auth/permissions.py
- Acceptance Criteria: Endpoints call serializers and check permissions; return correct media types.
- Size estimate: 3pt

## Phase 3: Tests + Documentation
- Objective: Implement tests in tests/ and update README.md/docs.
- Paths: /tmp/r7.11-item8-scaffold/tests/test_api_export.py, /tmp/r7.11-item8-scaffold/tests/test_csv.py, /tmp/r7.11-item8-scaffold/README.md
- Acceptance Criteria: Pytest passes covering all formats and permission scenarios; README updated.
- Acceptance Command: .venv/bin/pytest /tmp/r7.11-item8-scaffold/tests/
- Size estimate: 2pt
