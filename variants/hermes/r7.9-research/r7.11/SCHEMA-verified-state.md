# SCHEMA — verified-state.json (r7.11, schema_version "1.0")

Terse field reference for the machine-authoritative state file. For
semantics see DESIGN-r7.11-architecture.md §4 and §4.A/B/C.
`schema_version` must equal `"1.0"`; `load()` rejects anything else.

## Top-level

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | Must be `"1.0"`. |
| `spec` | object | See Spec. Immutable after bootstrap. |
| `phase_state` | array<PhaseStateEntry> | One entry per spec.phases, same order. |
| `history` | array<HistoryEntry> | Append-only audit log. |

## Spec

| Field | Type | Notes |
|---|---|---|
| `scaffold_root` | string | Absolute path to scaffold dir. |
| `plan_md_path` | string | Absolute path to PLAN.md. |
| `phases` | array<PhaseSpec> | Ordered. |

### PhaseSpec

| Field | Type | Notes |
|---|---|---|
| `id` | int | Unique within spec.phases. |
| `title` | string | Human label from PLAN.md. |

## PhaseStateEntry

| Field | Type | Default | Notes |
|---|---|---|---|
| `id` | int | — | Must match a `spec.phases[].id`. |
| `status` | enum | `pending` | See PhaseStatus below. |
| `tier_run` | int? | null | Last verify_phase tier (1–4). |
| `verified_at` | string? | null | ISO-8601 UTC, `"YYYY-MM-DDTHH:MM:SSZ"`. |
| `session_id` | string? | null | Hermes session that produced the verdict. |
| `missing_paths` | string[] | `[]` | Tier 1 findings. |
| `integrity_issues` | string[] | `[]` | Tier 3 findings. |
| `runtime_smoke_findings` | string[] | `[]` | Sub-tier 3.5 findings. |
| `acceptance_runner_findings` | string[] | `[]` | Sub-tier 3.7 (acceptance-runner) findings. Prefix taxonomy: `[ACCEPTANCE_PASSED]`, `[ACCEPTANCE_FAILED:N]`, `[ENVIRONMENT:..]`, `[INCONCLUSIVE:..]`, `[SKIPPED]`. `[ACCEPTANCE_FAILED:N]` and `[ENVIRONMENT:..]` set the verdict's `passed=false` and contribute captured stdout/stderr to `corrective_dispatch`. Empty when the phase block in `PLAN.md` did not declare an `Acceptance Command:` field. |
| `semantic_concerns` | string[] | `[]` | Tier 4 findings. |
| `corrective_dispatch` | string? | null | Paste-ready re-dispatch goal. |
| `revision_count` | int | 0 | Incremented on every failed verdict. |
| `max_revisions` | int | 3 | Wrapper escalates when count ≥ this. |

### PhaseStatus (enum)

`pending` · `in_progress` · `verified_passed` · `verified_failed`

## HistoryEntry

| Field | Type | Notes |
|---|---|---|
| `session_id` | string | |
| `phase_id` | int | |
| `verdict` | string | `"passed"` or `"failed"`. |
| `ts` | string | ISO-8601 UTC. |

## DecisionAction (returned by `decide()`, not persisted)

`advance` · `revise` · `escalate` · `complete`

Sequential-discipline rule: a failed-or-pending earlier phase always
wins over later phases. ESCALATE is emitted when an earlier failed
phase has `revision_count >= max_revisions`; ADVANCE is only emitted
for the next pending/in_progress phase after all-passed predecessors.

## Atomic-write contract

`save(state, path)`: serialize JSON in memory; open
`NamedTemporaryFile(delete=False)` in the **same directory** as `path`;
write, `flush()`, `os.fsync()`, close; `os.replace(tmp, path)`. On any
exception (write/fsync/replace/signal) the temp file is `unlink()`ed
and the exception re-raised. Readers can assume `path` is either the
prior committed state or the new committed state — never partial.

## Validation policy on `load()`

- `schema_version` must equal `"1.0"`.
- Required fields present at every level (top, spec, each phase, each history entry).
- All enum values valid (`status`, `verdict`).
- `phase_state[].id` must be a member of `spec.phases[].id`.
- **Unknown extra fields are tolerated** at all levels for forward-compatibility.
  Wrapper and parent are independently versioned; rejecting unknown
  fields would couple their release cycles.
- **Missing optional fields default appropriately.** A pre-r7.11-F7 state
  file written before `acceptance_runner_findings` was introduced loads
  successfully; the field defaults to `[]`. (Same forward/backward-compat
  rule applies to other list-of-string and optional fields.)

Failure raises `SchemaError(ValueError)`. Semantic violations during
`record_verdict` (e.g., unknown phase_id) raise `IntegrityError(ValueError)`.

## Authorship

Per DESIGN §4: written EXCLUSIVELY by `verify_phase` (not yet built;
this module is item 1). Read by wrapper on every
`end_session_for_handoff`; read by every resumed parent session as
ground truth.
