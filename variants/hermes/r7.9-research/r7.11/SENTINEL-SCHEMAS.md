# Sentinel JSON schemas (r7.11 item 6a)

Two sentinel files written by `handoff_tools.py` to the scaffold root.
**These are handoff triggers; they are NOT authoritative state.** The
authoritative source of phase state is `verified-state.json`, written
by `verify_phase_tool.verify_phase_tool` (items 1+5).

## Who-writes / who-reads

| File | Written by | Read by |
|------|------------|---------|
| `<scaffold_root>/.session-end-signal.json` | `end_session_for_handoff` (called by parent agent) | Wrapper substrate (item 7) — for handoff routing only. |
| `<scaffold_root>/.session-escalate-signal.json` | `escalate_to_operator` (called by parent agent) | Wrapper substrate — pauses the run; surfaces to operator. |
| `<scaffold_root>/verified-state.json` | `verify_phase` via items 1+5 | Wrapper substrate — **AUTHORITATIVE** for phase state and routing decisions. |

The wrapper protocol on detecting a sentinel: kill the Hermes process,
read `verified-state.json` for actual phase state, then decide the
next action. The sentinel itself is metadata for logging and debugging
only.

## `.session-end-signal.json` schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `schema_version` | string | yes | Currently `"1.0"`. |
| `kind` | string | yes | Always `"session-end"`. |
| `timestamp` | string | yes | ISO 8601 UTC, e.g. `"2026-04-26T14:23:01Z"`. |
| `session_id` | string | yes | Hermes session_id (or synthesized `tool-call-<unix>`). |
| `completed_phase` | int or null | yes | Highest phase id completed this session; null OK. **Non-load-bearing.** |
| `parent_intent_log` | string or null | yes | One of `"advance"`, `"done"`, `"escalate"`, or null. **Non-load-bearing.** |
| `parent_summary` | string | yes | Free-text parent narrative; logged for operator. |

Example:

```json
{
  "schema_version": "1.0",
  "kind": "session-end",
  "timestamp": "2026-04-26T14:23:01Z",
  "session_id": "hermes-sess-abc",
  "completed_phase": 2,
  "parent_intent_log": "advance",
  "parent_summary": "phase 2 verified passed; phase 3 pending"
}
```

## `.session-escalate-signal.json` schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `schema_version` | string | yes | Currently `"1.0"`. |
| `kind` | string | yes | Always `"session-escalate"`. |
| `timestamp` | string | yes | ISO 8601 UTC. |
| `session_id` | string | yes | Hermes session_id (or synth). |
| `reason` | string | yes | One of `verify_failed_after_max_revisions`, `ambiguous_requirements`, `external_dependency`, `other`. |
| `message` | string | yes | Operator-facing message; non-empty. |
| `suggested_action` | string or null | yes | Optional hint to operator. |

Example:

```json
{
  "schema_version": "1.0",
  "kind": "session-escalate",
  "timestamp": "2026-04-26T14:23:01Z",
  "session_id": "hermes-sess-xyz",
  "reason": "verify_failed_after_max_revisions",
  "message": "phase 3 has failed 5 revisions; root cause unclear",
  "suggested_action": "inspect verified-state.json history; consider rewriting PLAN.md phase 3 paths"
}
```

## Relationship to `verified-state.json`

If the wrapper detects either sentinel, it reads `verified-state.json`
for **authoritative phase state** to decide the next action. The
sentinel is metadata only:

- `parent_intent_log: "advance"` does not advance the phase — only a
  passed=true verdict in `verified-state.json` does.
- `completed_phase: 3` is informational — the wrapper checks the
  `phase_state` array in `verified-state.json` to determine which
  phases actually passed.
- `parent_summary` is logged for operator debugging; it never
  influences routing.

This is the §6 F2 "wrapper-as-source-of-truth" mitigation: a parent
that fabricates its narrative cannot corrupt the run, because the
wrapper does not consult the narrative for decisions.

## Atomicity and double-call

- Both sentinels are written atomically (write-temp + fsync +
  os.replace) in the scaffold root.
- A second call in the same session raises `ToolError` rather than
  overwriting; the wrapper substrate clears the sentinel between
  sessions.
- On atomic-write failure, no `.tmp` files are left behind.
