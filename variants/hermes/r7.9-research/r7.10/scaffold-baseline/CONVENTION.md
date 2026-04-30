# scaffold-baseline convention

Files in `src/` and `tests/` are **stub placeholders**, not finished
code. The parent agent's job during a trial is to FILL the stubs in
place, not to create parallel files alongside them.

## Rule

If a file at `<scaffold_root>/src/...` exists but is docstring-only
(or near-empty), treat it as a stub to be implemented under a
PLAN.md phase whose `Paths:` declaration includes that file.

Do NOT create a parallel file (e.g. `export_routes.py` alongside
`export.py`) — this produces:

- Duplicate top-level symbols (`router`, `MOCK_RECORDS`, endpoint
  functions, etc.) that break FastAPI app composition (and trip
  tier-3 CAT4 orphan-collision checks)
- Confusion about which file is canonical
- An orphan baseline stub left behind that no phase claims

## Why this convention exists

In r7.11 item-8 trial 3, the parent created
`src/api/export_routes.py` in phase 3 alongside the baseline
`src/api/export.py`. Both defined the same `router` and the same 3
endpoint functions. content_verify flagged 6 duplicate-symbol
findings; tier-3 CAT4 missed it because CAT4 only inspected
PLAN.md-declared paths and `src/api/export.py` was not in any phase.

The architecture's tier-3 wiring analyzer was extended (r7.11 F-9
part B) to walk `<scaffold_root>/{src,tests}` for orphan .py files
and feed them into CAT4's collision check. But the convention itself
is the prevention: ship stubs, fill stubs, don't shadow stubs.

## What stub-shape looks like

A stub file should be importable but contain no top-level definitions
beyond a module docstring:

    """Module purpose. Populated by capability-curve trials."""

Files matching this shape are recognized as stubs by the verifier
and the convention assumes they will be filled by the trial's parent
under the phase whose `Paths:` declaration claims that file.

## Examples in this scaffold

These are all valid stub-shape files, ready to be filled:

- `src/api/export.py` — Export API endpoints
- `src/export/csv.py` — CSV export
- `src/export/json.py` — JSON export
- `src/export/pdf.py` — PDF export
