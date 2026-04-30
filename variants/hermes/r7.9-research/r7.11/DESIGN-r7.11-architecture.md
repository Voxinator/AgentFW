# DESIGN — r7.11 Architecture: Verified-State Multi-Session Resumable

**Author**: 2026-04-26 design session
**Status**: DRAFT for operator review. No firmware work begun.
**Predecessors**: `r7.10/HANDOFF-r7.10-current.md`, `r7.10/ARTIFACT-r7.10-budget-60min-n5.md`, `r7.10/NOTE-r7.10-budget-n10-r4-rescore.md`.

---

## §1. Preamble — the campaign-arc lesson and the reframe

The arc from r7.5 through r7.10 progressively narrowed the failure surface:

- **r7.5–r7.8**: child-side interventions (HWO scaffold, A1/A2/T1) all landed inside noise. The CEILING FINDING closed those campaigns: the agentic layer is at ceiling on the 4-task probe; ~2/3 of FAILs are generation-layer pathologies.
- **r7.9-ε1**: parent-decomposition rubric produced the first non-noise lift.
- **r7.10**: validated the *mechanism* for parent-side decomposition — `write_plan_md` tool-description teaching reaches the planning layer at 60–80% PLAN.md write rate, with phased v1 dispatches following the OBJECTIVE/PATHS/ACCEPTANCE template.

What r7.10 also revealed — visible only after content-verified scoring of n=10 + n=5: **end-to-end completion is not budget-bounded; it is synthesis-trust-bounded.**

Across 25 trials at progressively more generous budgets and lower temperatures, content-verified strict completion was 0/25; charitable was 2/25. The mechanism reliably produces decomposition + dispatch + child execution + parent synthesis. What it does NOT produce is a synthesis that is *grounded in checkable reality*.

The two charitable cases (prior n=10 r4, recent n=5 r5) both had real workers writing real code, ending in parent claims that overstated coherence:

- **n=10 r4**: real reportlab-based PDF serializer in `pdf.py`; `formats_init.py` auto-load registered a hardcoded fake (`b"%PDF-1.4\n%test-content\n%%EOF"`) that silently shadowed it. Tests pass anyway because they only check status code + content-type. Parent claimed "uses ReportLab" — true at file level, false at runtime.
- **n=5 r5**: real CSV/JSON serializers, but API endpoints don't import them (dead code). Two of four test files left as `raise NotImplementedError` stubs. Parent claimed "ALL TESTS PASSED" — true of the new files, false of the unfixed stubs.

The recent n=5 r4 was a third, more striking case: zero implementation files written by any child, parent claimed end-to-end completion regardless. **Synthesis untethered from state.**

> **The architectural reframe r7.11 ships:** *the mechanism layer is robust; the synthesis layer is the new failure surface; r7.11's job is to make synthesis trustworthy by grounding it in verified state between phases.*

This converges with what Anthropic's effective-harnesses post and OpenDev's compaction strategy independently arrived at: long-horizon work that exceeds single-session capacity needs verified state across phase boundaries, not just plan-and-dispatch state.

---

## §2. Lifecycle

The parent agent is the orchestrator. The wrapper is dumb substrate. Session boundaries are tool calls, not turn budgets or wrapper timeouts. The lifecycle in compressed form:

```
                        BOOTSTRAP SESSION
                              │
                              ▼
                   ┌─────────────────────┐
                   │ classify (β-fuse)   │
                   │ write_plan_md       │
                   │ create todo         │
                   │ end_session_handoff │
                   └──────────┬──────────┘
                              │  [wrapper observes exit signal,
                              │   reads verified-state.json,
                              │   resumes next session]
                              ▼
                       PHASE N SESSION
                              │
                              ▼
                   ┌─────────────────────┐
                   │ delegate_worker (v1)│
                   │ child phase work    │
                   │ verify_phase(N)     │ ◄────────┐
                   └──────────┬──────────┘          │
                              │                     │
              ┌───────────────┼───────────────┐     │
              ▼               ▼               ▼     │
         passed=true     passed=false     escalate?  │
              │               │               │     │
              ▼               │               ▼     │
   end_session_handoff        │      escalate_to_operator
      (advance to N+1)        │            (pause)
                              │                     │
                     ┌────────▼─────────┐           │
                     │ revise:           │           │
                     │ delegate_worker   │           │
                     │ with corrective   │           │
                     │ dispatch guidance │───────────┘
                     │ from verify result│
                     └───────────────────┘

                              │  [N+1 ... N+M]
                              ▼
                      FINAL SESSION
                              │
                              ▼
                   ┌─────────────────────┐
                   │ verify_phase(final) │
                   │ synthesis grounded  │
                   │ in verified-state   │
                   └─────────────────────┘
```

Every transition between sessions is a tool call. The parent never "decides to keep going" implicitly — it must explicitly call `end_session_for_handoff` (advance/done) or `escalate_to_operator` (pause for human).

---

## §3. Tool surface

The parent's r7.11 toolset is r7.10's plus three new tools. Schemas below are sketches, not final API.

### Carried forward from r7.10 (no change)

- **`delegate_worker_v2`** — β-fuse classification + first-cut PLAN. Curve-p schema unchanged (parser-bug-immune).
- **`delegate_worker`** (v1) — phase dispatch. Single-string-goal contract. The OBJECTIVE/PATHS/ACCEPTANCE template the parent learned from `write_plan_md`'s description still drives dispatch goals.
- **`write_plan_md`** — tool-description teaches the 3-phase decomposition pattern. Same description as r7.10 (proven 5/5 PLAN.md write rate at temp 0.3 / 60-min). The known parser bug (`unhashable type: 'slice'`) is descoped: parents pivot to `write_file` cleanly.
- **`todo`** — phase-iteration tracker. Load-bearing for the cycle in r7.10. Must persist across session resumes (open verification — see §5).
- **`write_file`**, **`read_file`**, **`search_files`** — generic file ops. Used by parent for PLAN.md fallback and exploration; used by children for implementation.

### New in r7.11

#### Return-type contract (Hermes constraint)

All three new r7.11 tools' Hermes-side handler shims (`r7_11_verify_phase.py`, `r7_11_end_session.py`, `r7_11_escalate.py`) **must return `str`**, not Python `dict` or other native types. Returning a non-string value triggers a downstream `unhashable type: 'slice'` error in Hermes' API-call result-handling pipeline that masquerades as a tool failure even when the underlying handler ran correctly and side effects (sentinel writes, `verified-state.json` updates) persisted.

Concretely, the shim pattern is:

```python
def _handle(args, **kw):
    result = verify_phase_tool(...)   # returns dict
    return json.dumps(result)         # return string
```

The dict-typed return from the underlying Python module (`verify_phase_tool`, `end_session_for_handoff`, `escalate_to_operator`) is the right shape for testing and downstream Python consumers. The shim's `json.dumps` boundary marshals that into Hermes' wire format. **Do not rely on implicit coercion** — it doesn't happen, and the failure mode (slice error masquerading as tool failure) is misleading. The shim is the single coercion point; explicit `json.dumps` keeps the boundary debuggable and keeps the failure loud if a future shim accidentally drops the wrap.

This was isolated empirically during r7.11 item 6b smoke trial bisection (2026-04-27); see `r7.x-followups.md` F-2 for the trigger isolation narrative. An upstream `tools/registry.py:dispatch` coercion would prevent this from biting future tool authors but is descoped from r7.11 (canonical Hermes change is a different risk class than `.probe-*` staging).

#### `verify_phase`

The load-bearing new tool. Runs in tiers, returns structured result, writes to `verified-state.json` as a side effect.

```yaml
verify_phase:
  description: |
    Verify a phase's deliverables against PLAN.md.
    Runs tiers 1-3 (presence, syntax, wiring) by default; tier 4
    (semantic judge) only when `tier=4` is explicitly passed.
    Result is also persisted to <scaffold>/verified-state.json,
    which is the wrapper's authoritative source of phase state.
    
    On passed=false, the result includes corrective-dispatch
    guidance — a string suitable for re-dispatching the phase
    via delegate_worker. Re-dispatch with explicit focus on the
    missing paths the verifier identified.
  parameters:
    phase_id:                {type: integer, description: "phase number from PLAN.md"}
    tier:                    {type: integer, default: 3, enum: [1, 2, 3, 4]}
    with_runtime_smoke_test: {type: bool, default: false,
                              description: "Opt-in sub-tier 3.5. Imports the modules PLAN.md
                                            declares for this phase in a sandboxed subprocess
                                            and inspects runtime state (e.g., what's actually
                                            registered on declared registries). Catches
                                            importlib-shadowing patterns that pure AST analysis
                                            misses. Recommended when PLAN.md declares modules
                                            with import-time side effects."}
  returns:
    passed:                  bool
    tier_run:                int          # the integer tier; 3.5 is reflected via runtime_smoke_findings
    missing_paths:           [string]     # files PLAN.md said should exist but don't
    integrity_issues:        [string]     # tier-3 findings (dead code, unused imports, etc.)
    runtime_smoke_findings:  [string]     # sub-tier 3.5 only; runtime registration shadowing, etc.
    semantic_concerns:       [string]     # tier-4 only
    corrective_dispatch:     string       # ready-to-paste goal for re-dispatch
    persisted_to:            string       # path to verified-state.json
```

#### corrective_dispatch — worked examples

`corrective_dispatch` is the highest-leverage doctrine-delivery vector in this architecture. It's grounded in the same mechanism r7.10 validated: tool-description teaching reaches the planning layer, and tool-result text steers the next dispatch. Two concrete examples illustrate what `verify_phase` must produce:

- **For an n=10 r4-style PDF case (real serializer dead, fake serializer registered):**
  > *"Re-dispatch with explicit focus on `src/export/pdf.py` PDFSerializer registration. The duplicate registration in `formats_init.py` is shadowing the real serializer at runtime; either remove `formats_init.py` or update `PDFSerializer` registration order so the reportlab-based class wins."*

- **For an n=5 r5-style unwired-serializers case (API endpoints inline serialization):**
  > *"Re-dispatch with explicit focus on `src/api/export.py` imports. Endpoints currently inline serialization; they should import `serialize_to_csv` / `serialize_to_json` / `serialize_to_pdf` from `src/export/` and call those functions instead of inlining."*

These examples are not boilerplate. They name specific paths, identify the specific root-cause pattern, and prescribe a specific corrective action. The verifier's job is to produce text shaped like these examples — not "fix the issue" or "address the missing file" but a complete, paste-ready dispatch goal that follows the OBJECTIVE/PATHS/ACCEPTANCE template the parent already follows in r7.10.

#### Verification tiers

| Tier | What it checks | Cost | Catches |
|------|----------------|------|---------|
| **1: Presence** | each path in PLAN.md exists; file body is non-trivial (≥ N chars or ≥ M lines, configurable; not a pure docstring stub) | very cheap (stat + wc) | r7.10 n=5 r4 fabrication (zero files written) |
| **2: Syntax** | each Python file: `ast.parse` succeeds; no `raise NotImplementedError` in non-test code; imports resolve against project + venv | cheap (AST + import resolution) | r7.10 n=5 r5 unfixed test stubs; broken syntax |
| **3: Wiring** | AST analysis: defined symbols referenced from elsewhere in the project; declared imports actually used; tests reference real implementations (test bodies invoke functions the impl files define) | medium | r7.10 n=5 r5 unwired serializers (API endpoints don't import the modules); part of n=10 r4 |
| **3.5: Runtime smoke test** (opt-in) | sandboxed subprocess: imports the modules PLAN.md declares for this phase, inspects runtime state (registry contents, declared symbols' actual identity, which class is bound to which registered name). ~50 LOC Python in a sandbox; no scaffold mutation. Activated via `with_runtime_smoke_test=true` on the verify_phase call. **Not auto-invoked**; available when PLAN.md declares modules with import-time side effects (e.g., a serializer registry, a plugin loader, monkey-patched defaults) | medium-low (subprocess startup + import) | r7.10 n=10 r4 importlib-shadowing (real reportlab `PDFSerializer` defined in `pdf.py` but `formats.py` runs `importlib.import_module(".formats_init", ...)` which registers a hardcoded fake that wins at runtime). AST analysis can flag this if it follows importlib calls; runtime smoke confirms it deterministically by reading `registry._serializers["pdf"].__class__.__module__` |
| **4: Semantic** | judge-shaped sub-agent with fresh context: read parent's claim, read scaffold, return structured concerns (does the implementation match the claim? are tests substantive?) | expensive (sub-agent invocation, ~30–90s) | residual concerns tiers 1–3.5 don't catch — e.g., implementation passes presence/syntax/wiring/runtime but is logically wrong |

##### Phase-awareness in tier-2 import resolution

When `verify_phase` is called on phase N, it receives the full phase plan from PLAN.md (the `project_phases` list). The verifier computes a *tolerated-deferred set* equal to the union of declared paths from all phases other than N. An import in a phase-N file whose target resolves to a path in the tolerated-deferred set is recorded as `deferred (declared in phase M)` and does NOT cause `passed=false`. Imports that don't resolve project-relative, don't resolve via `importlib.util.find_spec`, and aren't in the tolerated set remain integrity issues.

This is what makes the verifier sound when phases write disjoint pieces of a single import graph. Worked example: phase 1 writes `src/export/csv.py` which does `from src.export.formats import Formatter`; phase 2 writes `src/export/formats.py`. At phase-1 verify time, `formats.py` is not yet on disk, but it is declared in phase 2's paths — the verifier defers the import and passes phase 1. At phase-2 verify time, `formats.py` IS on disk, so the import resolves project-relative directly. Phase ordering matters only for what's already on disk; the verifier's pass/fail signal is invariant under it as long as `project_phases` is provided.

Resolution is project-relative first, venv second; ambiguity is resolved by taking the most-specific module/package match under `scaffold_root`. The verifier never executes user code — `find_spec` is metadata-only.

**Tier policy r7.11 ships with:**

- Tiers 1 + 2 in the first build (minimum required to clear known r7.10 failure modes).
- Tier 3 in the same first build (medium cost, but catches the n=5 r5 unwired-serializers pattern and the AST-detectable parts of n=10 r4).
- **Sub-tier 3.5 (runtime smoke test) in the same first build, as opt-in.** Not auto-invoked; the parent activates it via `with_runtime_smoke_test=true` when PLAN.md declares modules with import-time side effects. The architecture explicitly addresses the importlib runtime-shadowing failure mode rather than leaving it as residual risk. Deterministic; sandboxed.
- **Tier 4 may be deferred to r7.12** if it lifts the build budget meaningfully. It's the only tier that requires sub-agent infrastructure beyond what r7.10 has.

Tier 4 is also the only tier where verification could itself fabricate (judge sub-agent might produce a "looks fine" verdict on something subtly wrong). Tiers 1–3.5 are deterministic; their false-positive rate is bounded by the analysis quality, not by inference temperature.

The opt-in framing for sub-tier 3.5 is intentional: AST wiring (tier 3) is sufficient for most phases, and importing scaffold code in a subprocess has nontrivial setup cost (PYTHONPATH wiring, venv selection, timeout handling). Reserving 3.5 for cases where the spec involves runtime registration / plugin loading / monkey-patching keeps the default verify path fast and predictable.

#### `end_session_for_handoff`

The parent's signal that the current session's work is done. Causes the wrapper to read `verified-state.json` and decide what to do next.

```yaml
end_session_for_handoff:
  description: |
    Signal the wrapper that this session's work is complete and the
    next session (if any) should resume from verified state. The
    wrapper does NOT trust this call's claim of what was completed —
    it reads verified-state.json directly to determine phase state.
    PLAN.md updates from the parent are informational; the JSON file
    is authoritative.
  parameters:
    completed_phase:    {type: integer, nullable: true,
                         description: "phase number this session worked on; null if this is bootstrap"}
    parent_intent_log:  {type: string, nullable: true,
                         enum: ["advance", "done", "escalate"],
                         description: "Optional. Logged for debugging / failure-analysis only —
                                       NON-LOAD-BEARING. The wrapper's authoritative source for
                                       next-session state is verified-state.json, regardless of
                                       what this field says (or whether it's set). Field name
                                       is deliberately suffixed `_log` to make the non-authoritative
                                       role explicit."}
    parent_summary:     {type: string, description: "human-readable summary for PLAN.md / logs; not authoritative"}
```

The parent's `parent_intent_log` is **non-load-bearing** — present only for debugging and failure-analysis observability. The wrapper's behavior is determined by `verified-state.json`:
- All phases in PLAN.md verified-passed → wrapper exits with success.
- Any phase verified-passed=false with no further revision attempts available → escalate or revise per policy.
- Phase N verified-passed=true and phase N+1 not yet attempted → resume next session at N+1.

#### `escalate_to_operator`

When the parent decides the situation needs human input. Causes the wrapper to pause cleanly with state preserved and surface the message.

```yaml
escalate_to_operator:
  description: |
    Pause the multi-session run for operator review. State is preserved;
    operator can inspect and resume with `<wrapper> resume <session_id>`.
  parameters:
    reason:  {type: string, enum: ["verify_failed_after_max_revisions",
                                    "ambiguous_requirements",
                                    "external_dependency",
                                    "other"]}
    message: {type: string, description: "operator-facing explanation"}
    suggested_action: {type: string, nullable: true}
```

The escalate path is the only way Brian re-enters the loop mid-run. It is also the safety valve against the indefinite-revise failure mode (§6).

---

## §4. State artifacts

Two files persist across session boundaries. They serve different audiences.

### PLAN.md — parent-facing, human-readable

Written by `write_plan_md` (or `write_file` fallback) during bootstrap. Read by every resumed session. Format unchanged from r7.10:

```markdown
## Phase 1: <title>
Objective: <single-line>
Paths: <comma-separated relative paths>
Acceptance Criteria: <bullet list or single line>
Size estimate: <small | medium | large>

## Phase 2: ...
```

**Authority**: PLAN.md is the parent's internal map. The parent re-reads it on resume to orient. Its content can be updated by the parent mid-run (e.g., a phase decomposes into sub-phases). It is NOT trusted by the wrapper.

### verified-state.json — machine-authoritative

Written exclusively by `verify_phase` as a side effect of every call. Read by the wrapper on every `end_session_for_handoff` to decide what to do next. Read by every resumed session as the parent's ground truth for "what's actually been verified."

```json
{
  "schema_version": "1.0",
  "spec": {
    "scaffold_root": "/tmp/export-probe-scaffold",
    "plan_md_path": "/tmp/export-probe-scaffold/PLAN.md",
    "phases": [
      {"id": 1, "title": "Core serializers"},
      {"id": 2, "title": "API + permissions"},
      {"id": 3, "title": "Tests + docs"}
    ]
  },
  "phase_state": [
    {
      "id": 1,
      "status": "verified_passed",
      "tier_run": 3,
      "verified_at": "2026-04-27T08:14:22Z",
      "session_id": "20260427_080012_abc123",
      "missing_paths": [],
      "integrity_issues": [],
      "revision_count": 0
    },
    {
      "id": 2,
      "status": "verified_failed",
      "tier_run": 3,
      "verified_at": "2026-04-27T08:32:09Z",
      "session_id": "20260427_081744_def456",
      "missing_paths": ["src/api/export.py"],
      "integrity_issues": ["src/auth/permissions.py imported but never invoked"],
      "revision_count": 1,
      "max_revisions": 3,
      "corrective_dispatch": "Re-dispatch with explicit focus on: src/api/export.py (must define GET /export endpoint that imports has_permission from src/auth/permissions.py and calls it on each record)."
    },
    {
      "id": 3,
      "status": "pending"
    }
  ],
  "history": [
    {"session_id": "...", "phase_id": 1, "verdict": "passed", "ts": "..."},
    {"session_id": "...", "phase_id": 2, "verdict": "failed", "ts": "..."}
  ]
}
```

**Authority**: this file is the wrapper's source of truth. The parent reads it but cannot lie to the wrapper *via* it — the parent doesn't write it directly; only `verify_phase` writes it, and `verify_phase` is deterministic on tiers 1–3.

**Persistence**: written to disk inside the scaffold root on every `verify_phase` call. Survives session boundaries. Is the wire format that lets a fresh session resume cold without re-running prior phases.

### Session resume contract

When the wrapper launches a resumed session via `hermes chat --resume <session_id>`, the parent's first turn should:

1. Read PLAN.md.
2. Read verified-state.json.
3. Identify the next pending or revision-needed phase.
4. Dispatch that phase via `delegate_worker` with the goal constructed from PLAN.md (and, on revision, prepended with the `corrective_dispatch` text from verified-state.json).

This re-orientation is the cost of multi-session — typically 1–2 turns. Acceptable; the alternative is unbounded single-session budget which we've shown doesn't work.

**Build prerequisite — todo-resume probe (30 min, blocks firmware work)**: does `todo` tool state persist across `hermes chat --resume` natively? r7.10 used todo for phase iteration within a session. The answer determines the resume contract. Probe protocol:

1. Spawn a Hermes session at canonical (no probe firmware staged).
2. Have the parent create a 3-entry todo list and mark one entry `in_progress`.
3. Exit cleanly via `--max-turns 1` after the todo write, or programmatically.
4. Resume via `hermes chat --resume <session_id> -q "list current todo state"`.
5. Inspect parent's response and any todo tool calls.

**If todo state persists**: design holds as-written; resumed sessions read todo natively.

**If todo state does NOT persist**: §4 session-resume contract amends. The parent's first turn on resume reconstitutes a todo list from `verified-state.json:phase_state` (each phase becomes one todo entry; status mapped: `verified_passed` → completed, `verified_failed` or `pending` → pending, the active phase → in_progress). The verify_phase tool's side-effect surface expands to write the todo-reconstitution snippet into PLAN.md as a resume-bootstrap pointer.

This probe is item #0 in the implementation-order list (§Implementation order, below) and explicitly blocks all subsequent firmware work.

### §4.A. Probe outcome and addendum (2026-04-26)

**Probe ran**: 2026-04-26 ~11:06–11:11. Two sessions, canonical Hermes (v0.8.0, 2026.4.8), gemma-4-26B-A4B-it-MLX-8bit at temp 0.3.

- **Session 1**: spawned cleanly. Parent created a 3-entry todo list via the todo tool. Final message "Todo created." Session JSON saved with 4 messages (user prompt + assistant tool-call + tool result + final message). Session ID `20260426_110656_5ed3a6`.
- **Session 2**: invoked `hermes chat --resume 20260426_110656_5ed3a6 -q "<inspect-todo prompt>"`. Parent ran 1 turn (~3s elapsed): called the todo tool, which returned `{"todos": [], "summary": {"total": 0, "pending": 0, ...}}`. Parent's final assistant message was literally `[]` (the empty JSON the tool returned).

**Outcome: NOT-PERSISTED, with a broader-than-expected scope.**

Empirical observations from the resumed session's saved JSON:
- The session JSON file at `session_20260426_110656_5ed3a6.json` was OVERWRITTEN by session 2's run. Post-resume `session_start` is 2026-04-26T11:10:36 (the resume invocation time, not the original 11:06:56).
- Post-resume `message_count` is 4: only session 2's messages (user prompt + tool call + tool result + final assistant). Session 1's 4 messages are lost from the JSON.
- The todo tool returned an empty list, confirming the in-memory `TodoStore` was empty in session 2 — the rehydration path (`_hydrate_todo_store` at `run_agent.py:2536`, designed to walk history backwards for the most recent todo response) had no history to walk.

**Diagnosis**: in this Hermes version, `--resume` does not load prior conversation history at all. The new session reuses the session_id but starts with empty `conversation_history`. The `_save_session_log` overwrite-guard (`run_agent.py:2411` — "skip overwrite if existing has more messages") permits the overwrite when new and existing message counts are equal, which is exactly the failure mode here.

**Root cause** (collateral finding): the SQLite session DB at `~/.hermes/state.db` has not been populated for any session since 2026-04-24 19:01. The `sessions` table holds 1092 entries; the `messages` table contains the corresponding turn-by-turn data; the most recent `started_at` is 2026-04-25 00:01 UTC. All n=5 trials from 2026-04-26 morning, all min-mechanism / budget-n10 trials from earlier in the campaign, and this probe's sessions exist ONLY as JSON files. Cross-checked: my probe session and three other recent JSON-only sessions all return `0` rows when queried by `id` against the `sessions` table. **Hermes' resume path reads from SQLite** (the SessionDB instance is the source of truth for `conversation_history`); JSON files are observability artifacts, not a fallback. With SQLite unpopulated, resume has nothing to load. Whatever broke session-DB persistence on 2026-04-24 is the upstream cause of the resume-doesn't-work behavior. **Diagnosis only — no firmware work to fix it. Flagged for operator as a Hermes-layer issue independent of r7.11 design.**

### §4.B. Addendum to the session-resume contract

Given the probe outcome, the §4 resume contract amends as follows. r7.11 architecture treats Hermes' `--resume` as **a fresh-context invocation that happens to share a session_id**, NOT as a true history-preserving resume.

#### Addendum A1. State propagation across sessions is exclusively through `verified-state.json` and PLAN.md

There is no native conversation memory shared across resumes. Both files are file-system-persisted, written by tools, and survive the boundary deterministically. This was the design's intended fallback model anyway; the probe makes it the only model.

#### Addendum A2. Parent's first turn on resume MUST re-orient explicitly

When the wrapper resumes a session via `hermes chat --resume <id>`, it injects an orientation prompt (or appends to the operator's resume prompt) instructing the parent to:

1. `read_file` PLAN.md
2. `read_file` verified-state.json
3. Identify the next pending or revision-needed phase
4. Reconstitute todo via the todo tool: one entry per PLAN.md phase, status mapped from verified-state.json (`verified_passed` → completed, `verified_failed` or `pending` → pending, active phase → in_progress)
5. Dispatch that phase via `delegate_worker` with goal constructed from PLAN.md (and, on revision, prepended with `corrective_dispatch` from verified-state.json)

This re-orientation is now load-bearing, not merely cost-of-resume. The wrapper enforces it by including these steps as a numbered checklist in the resume prompt header, leveraging the same tool-result-teaching mechanism r7.10 validated.

#### Addendum A3. Wrapper must snapshot prior session JSON before re-launch

Because `--resume` OVERWRITES the existing session JSON file, the wrapper's audit responsibility expands: before launching `hermes chat --resume <id>`, the wrapper copies the current session JSON to a per-phase archive (e.g., `<scaffold_root>/.session-archive/phase-N-attempt-M.json`). This preserves the full conversation record that would otherwise be lost. The archive is read-only data for post-hoc analysis; the live JSON file remains the per-run artifact.

This is a 1–2-line addition to the wrapper's responsibilities (§5).

#### Addendum A4. PLAN.md and verified-state.json fully replace conversation memory as the resume contract

The original §4 contract listed PLAN.md (parent-facing) and verified-state.json (machine-authoritative) as the canonical state artifacts. The probe makes this contract sufficient AND necessary: there is no other channel. The verified-state.json schema's `phase_state` array, with its `corrective_dispatch` field for failed phases, is now the *only* way the parent's next-phase decision is informed across a session boundary.

Practically this strengthens the architecture's failure-mode resistance:
- F1 (parent loops on revise) is unchanged: revision_count is wrapper-tracked.
- F2/F3 (parent fabricates / parent ignores verify) is *strengthened*: the parent on resume cannot deceive the wrapper *via narrative* because there is no narrative; everything goes through the verify tool's structured output to verified-state.json.
- F4 (verify_phase wrong) is unchanged.

The probe outcome is mild adversity that the architecture absorbs cleanly: the design's reliance on verified-state.json as machine-authoritative was already correct; the probe confirms it is the ONLY path, which removes ambiguity.

### §4.C. SessionDB regression — collateral finding to flag separately

The state.db `sessions` table has not been written to since 2026-04-25. Affects:
- Hermes `sessions list`, `session_search`, `--continue` (resolves by recency from SQLite)
- `--resume` with prior-history loading (this probe)
- Any feature that consults the SessionDB

**Not blocking r7.11 design.** The architecture works on top of file-based state regardless of whether SQLite is populated. But Brian should know: a Hermes-layer fix to restore SessionDB writes would unblock native `--continue`, history-preserving `--resume`, and session search. **Independent investigation; not on the r7.11 critical path.**

---

## §5. Wrapper substrate

The wrapper is a thin driver. Its responsibilities, in full:

1. **Launch bootstrap session** with the operator's spec (via existing `hermes chat` mechanism).
2. **Observe exit signal**: when the parent calls `end_session_for_handoff` or `escalate_to_operator`, the underlying tool's implementation arranges for `hermes chat` to exit cleanly (via a sentinel file, signal, or programmatic shutdown — implementation detail).
3. **Read `verified-state.json`** from the scaffold root.
4. **Decide next action**:
   - All phases in PLAN.md show `status: verified_passed` → emit success report, exit.
   - Some phase shows `status: verified_failed` AND `revision_count < max_revisions` → resume same session ID; parent will re-dispatch with corrective guidance from verified-state.json.
   - Some phase shows `verified_failed` AND `revision_count >= max_revisions` → escalate.
   - Some phase shows `verified_passed` and the next phase is `pending` → resume same session ID for next phase.
   - Parent called `escalate_to_operator` → pause; surface message; await operator input.
5. **Resume next session** via `hermes chat --resume <session_id> -q "<continue>"` if applicable.
6. **Loop steps 2–5** until terminal state (success / escalate / max-budget).

The wrapper has **no knowledge of Hermes's tool schemas, no decision logic about phases, no firmware-level concerns.** It is ~200 lines of bash or Python that polls a state file and re-launches Hermes. Operator-facing CLI is one command (e.g., `hermes-multi run <spec-file>`) plus `hermes-multi resume <session-id>` for escalations.

The wrapper's restraint is what makes the architecture coherent: by refusing to read the parent's narrative claims, it removes the surface where fabrication could deceive the lifecycle. The parent can claim anything in `parent_summary`; the wrapper doesn't read it.

---

## §6. Failure modes and mitigations

The four named failure modes the design has to handle, plus where the architecture leaves residual risk.

### F1. Parent loops on revise indefinitely

**Scenario**: phase N keeps failing tier-1/2/3 verification; parent keeps re-dispatching with corrective guidance; never converges.

**Mitigation**: per-phase `max_revisions` (default: 3) tracked in verified-state.json. On `revision_count >= max_revisions`, the wrapper triggers escalation regardless of parent intent. This is wrapper-enforced, not parent-policed — the parent cannot override it by hallucinating that the next dispatch will surely work.

**Residual risk**: 3 revisions might be too generous (wastes phases on hopeless dispatches) or too tight (some legitimate phases need iteration). Configurable per spec; default tunable empirically against the first n trials of the new firmware.

### F2. Parent declares phase complete despite verify_phase=false

**Scenario**: parent calls `verify_phase`, sees `passed: false`, then calls `end_session_for_handoff` with `next_action="advance"` or `next_action="done"`.

**Mitigation**: the wrapper's source of truth is `verified-state.json` directly, NOT the parent's claim of what happened. When `end_session_for_handoff` fires, the wrapper reads the JSON file and computes its own next action. If `verified-state.json` shows phase N as `verified_failed`, the wrapper resumes N for revision (or escalates if revisions are exhausted), regardless of what the parent said. The parent's `parent_intent_log` field is recorded for debugging but not consulted for routing. The parent's narrative summary in PLAN.md is informational; the JSON file is authoritative.

This means parent-side fabrication cannot deceive the wrapper because the wrapper isn't reading the parent's narrative — it's reading the file the verify tool wrote. The naming convention reinforces this: `verified-state.json` (machine-authoritative); `parent_intent_log` (non-authoritative); `parent_summary` (non-authoritative). The architecture refuses to give the parent a load-bearing channel that bypasses verifier output.

**Residual risk**: only fires if `verify_phase` itself produced a false `passed: true` (see F4). The mitigation is structural — fabrication-via-narrative is impossible; fabrication-via-tool-result is bounded by tier integrity.

### F3. Parent fabricates the verify_phase call's expected result

**Scenario**: parent dispatches `verify_phase`, sees `passed: false`, ignores the result, claims success in `parent_summary`. Same as F2 but reframed.

**Mitigation**: same as F2 — wrapper reads `verified-state.json`, ignores `parent_summary`. Additionally, the verify result text in the parent's context window includes specific missing paths and integrity issues. For the parent to coherently emit "complete!" in the same context where the verifier just listed "src/api/export.py never written", it would need to contradict its own immediate prior tool result in plain text. This is structurally hard for the model to do — far harder than confabulating without contradicting evidence (which is the r7.10 n=5 r4 pattern).

The verify tool's result becomes part of the prompt context. Grounding synthesis in verifier output is exactly what makes synthesis trustworthy.

**Revise loop integration**: when verify returns `passed: false`, the result text includes a `corrective_dispatch` field with explicit re-dispatch guidance: *"Re-dispatch with explicit focus on: src/api/export.py (must define GET /export endpoint that imports has_permission from src/auth/permissions.py and calls it on each record)."* This leverages the tool-description-teaching mechanism r7.10 validated — parents follow tool result guidance reliably (the entire write_plan_md teaching pathway is built on this). Putting next-action prompts in the verify result steers the next dispatch without requiring schema enforcement (which we already know parents Goodhart against — see HERMES.md prose rubric H2).

### F4. verify_phase itself wrong

**Scenario**: `verify_phase` returns `passed: true` for an actually-broken implementation.

**Mitigation**: tiered design.
- Tiers 1–3 are deterministic AST/file-system analyses. Their false-positive rate is bounded by the analysis logic, not by inference temperature. False positives are debugging targets, not stochastic risks.
- Tier 4 (judge sub-agent) is the only stochastic tier. It runs only when explicitly invoked by the parent (typically on borderline cases). Its result is advisory; tiers 1–3 are the load-bearing pass/fail signal.
- For ambiguity tier 1–3 can't resolve, the verifier's `corrective_dispatch` field can include "operator review recommended" — pushing the borderline case to escalation rather than auto-passing.

**Residual risk**: tier-3 wiring analysis can miss runtime-only behaviors (e.g., dynamic imports, monkey-patching, late binding). The n=10 r4 `formats_init.py` case is exactly this shape: `formats.py` runs `importlib.import_module(".formats_init", ...)` which registers fakes at import time. AST-only analysis can catch this if it follows importlib calls; sub-tier 3.5 (runtime smoke test) catches it deterministically by importing the modules in a sandboxed subprocess and inspecting which class is actually bound to each registered name. With 3.5 available as opt-in, the residual surface shrinks to behaviors that don't manifest at import time and that 3.5's smoke import doesn't trigger — e.g., registration conditional on an env var that the smoke subprocess doesn't set, or registration that fires on first request rather than at module load. These are narrower failure modes; design accepts the residual.

### F5 (residual). Spec ambiguity that doesn't surface as verifier-checkable

**Scenario**: PLAN.md is well-formed and verifier passes, but the operator's intent doesn't match the verified implementation. (Beyond r7.11's scope to fix; but worth naming.)

**Mitigation**: not a r7.11 problem. r7.11 ensures the parent's claim matches the file state. Whether the file state matches the operator's intent is a spec-clarity problem upstream.

**Residual risk**: persistent. Treat as a separate concern; r7.11 doesn't claim to solve it.

### What r7.10 misses that r7.11 catches

| r7.10 failure | Caught by r7.11 tier |
|---------------|---------------------|
| n=5 r4 — zero implementation, parent claims completion | Tier 1 (presence) |
| n=5 r5 — unfixed test stubs, parent claims "ALL TESTS PASSED" | Tier 2 (no `raise NotImplementedError` in test files) |
| n=5 r5 — serializers not wired into API | Tier 3 (wiring: `src/api/export.py` doesn't import `src/export/csv.py`) |
| n=10 r4 — fake PDF serializer registered, real one dead code | Tier 3 (AST-detectable parts: `pdf.py:PDFSerializer` defined but never imported by runtime call sites) + sub-tier 3.5 (runtime smoke test deterministically reads `registry._serializers["pdf"].__class__.__module__` and finds the fake from `formats_init`, not the real reportlab class from `pdf.py`) |

### What r7.11 still doesn't catch

- Logically wrong implementations that parse, wire correctly, and have non-trivial bodies but produce wrong output. Tier 4 might catch some; tier 4 is best-effort.
- Mismatch between operator intent and PLAN.md-as-written (F5 above).
- oMLX or substrate-level failures (paging artifacts, gateway crashes). These are operability concerns; mitigated by the existing campaign discipline (canonical state, tripwires).

---

## Appendix — r7.10 component map

| Component | Status in r7.11 |
|-----------|------------------|
| `delegate_worker_v2` (curve-p schema) | **kept verbatim** |
| `delegate_worker` (v1) | **kept verbatim** |
| `write_plan_md` tool + description teaching | **kept verbatim** (parser bug remains descoped) |
| `todo` tool | **kept**; resume-persistence behavior to verify empirically during build |
| HWO scaffold | **kept verbatim** |
| HERMES.md prose rubric | **kept verbatim** (don't iterate; H2 confirmed invisible) |
| β-fuse classification | **kept verbatim** |
| `_session_messages_live` patch on `run_agent.py` | **kept verbatim** (curve-p layer) |
| `verify_phase` (tiers 1–3) | **NEW** in r7.11 first build |
| `verify_phase` (sub-tier 3.5: runtime smoke test) | **NEW** in r7.11 first build (opt-in via `with_runtime_smoke_test=true`) |
| `verify_phase` (tier 4) | **DEFERRED to r7.12**; build only if first n trials show failure modes tiers 1–3.5 demonstrably miss |
| `end_session_for_handoff` | **NEW** in r7.11 first build |
| `escalate_to_operator` | **NEW** in r7.11 first build |
| `verified-state.json` schema | **NEW** in r7.11 first build |
| Wrapper substrate (`hermes-multi`) | **NEW** in r7.11 first build |
| PLAN.md format | **kept verbatim** from r7.10 |

The mechanism layer is preserved unchanged. r7.11 adds a verification surface and a lifecycle layer on top of it. The r7.10 finding that the mechanism is robust is what enables this — we are confident the foundation works, and the additions only need to be load-bearing for the synthesis-grounding job.

---

## Implementation order

Rank-ordered. Item 0 is a build prerequisite that blocks all subsequent firmware work.

0. **Build prerequisite — todo-resume probe (30 min).** Does `todo` tool state persist across `hermes chat --resume`? Protocol in §4. **Blocks firmware work.** Result either confirms §4 resume contract as-written, or amends it to specify parent reconstitutes todo from `verified-state.json:phase_state` on resume.
1. `verified-state.json` schema lock + read/write helpers (standalone Python module; no Hermes integration yet).
2. `verify_phase` tiers 1 + 2 as a standalone Python module (testable without Hermes; deterministic).
3. `verify_phase` tier 3 wiring analyzer (more delicate; needs care on importlib/dynamic patterns; AST-based).
4. `verify_phase` sub-tier 3.5 runtime smoke test (~50 LOC; sandboxed subprocess; opt-in via `with_runtime_smoke_test=true`).
5. Hermes tool wrapper for `verify_phase` (registers in toolsets, exposes to parent).
6. `end_session_for_handoff` and `escalate_to_operator` tools + wrapper exit-signal mechanism.
7. Wrapper substrate (Python; ~200 LOC; lives in `variants/hermes/probe/` or wherever organizationally cleanest at build time).
8. Smoke trial: 1 trial against T6 with the full r7.11 build; verify session boundaries fire correctly and verified-state.json reflects ground truth.
9. n=5 confirmation with content-verified scoring; compare strict-completion rate against r7.10 baseline (0/25 → ?).

Tier 4 (judge sub-agent) is independent of the above and **deferred to r7.12**. Build only if the n=5 confirmation surfaces failure modes that tiers 1–3.5 demonstrably miss.

---

## Decisions on previously-open design questions

Carrying forward operator decisions made during architecture review (2026-04-26):

| # | Question | Decision |
|---|----------|----------|
| Q1 | Tier-3 wiring analyzer in first build? | **Ships in first build.** A1 confirmed. |
| Q2 | Default `max_revisions = 3`? | **Accept default. Configurable per spec. Tune empirically** based on first n trials of the new firmware. |
| Q3 | Wrapper substrate language? | **Python.** Testability + JSON state machine outweigh bash convention. Lives in `variants/hermes/probe/` or whatever organizational location is cleanest at build time. |
| Q4 | `escalate_to_operator` UX? | **Start minimal**: paused exit + state file + stdout message. Operator resumes manually via `hermes-multi resume <session-id>`. **Don't build email / notification surface until autonomous-mode usage justifies it.** |
| Q5 | Tier 4 (semantic judge) in first build? | **Defer to r7.12.** Build only if first n trials show failure modes tiers 1–3.5 demonstrably miss. |

No further open questions block sign-off. Refinements A1–A5 (folded above) and the prerequisite probe are the only items between this design and firmware work.

---

## Sign-off status

This document incorporates operator refinements A1–A5 from architecture review:
- **A1** Tier 3 ships in first build (Q1 confirmed) → §3 tier policy + implementation-order item 3.
- **A2** Sub-tier 3.5 runtime smoke test added → §3 schema, tier table, tier policy; §6 F4 mitigation; §6 cross-table; appendix component map; implementation-order item 4.
- **A3** todo-resume probe promoted to build prerequisite → §4 (replaces open-verification paragraph); implementation-order item 0.
- **A4** `corrective_dispatch` field given two worked examples grounded in n=10 r4 and n=5 r5 → §3 (new subsection).
- **A5** `next_action` renamed to `parent_intent_log`, made optional, role-explicit → §3 schema; §6 F2 reframed.

Pending operator sign-off, the next action is **implementation-order item 0** (todo-resume probe). No firmware work begins until sign-off.
