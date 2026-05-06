# Verify pre-staged export endpoint — phased plan

## Phase 1: Verify pre-staged JSON export endpoint
- Objective: confirm `src/api/export.py` and `tests/test_api_export.py` exist, the test suite passes against them, and report findings without modifying the implementation
- Paths: src/api/export.py, tests/test_api_export.py
- Acceptance Criteria: implementation file unchanged from start; pytest exits 0
- Size estimate: 1pt
- Acceptance Command: .venv/bin/pytest tests/test_api_export.py
