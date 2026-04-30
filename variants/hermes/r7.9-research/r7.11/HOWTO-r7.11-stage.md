# HOWTO — Stage / smoke / unstage r7.11 on the Hermes VM

Operator runbook for the three new r7.11 tools (`verify_phase`,
`end_session_for_handoff`, `escalate_to_operator`). Scripts live in
`variants/hermes/r7.9-research/r7.11/` on the Mac and ssh to `ubuntu-vm`
for VM-side mutation. Do not run any script twice in parallel.

## 1. Pre-conditions

VM at canonical:

| File | Expected md5 |
|------|--------------|
| `~/.hermes/hermes-agent/HERMES.md` | `0780c232a6cb52e13e432261f0d68ad9` |
| `~/.hermes/hermes-agent/run_agent.py` | `94ad8712678df5e96b9f407446edf249` |
| `~/.hermes/hermes-agent/toolsets.py` | `5d126e7f1987468c0514cbc474ba12eb` |
| `~/.hermes/hermes-agent/model_tools.py` | `10aaf53294ba39569844ebac7076e9c9` |

Stage's pre-flight checks the first two; the others are recorded for
visual confirmation. `OMLX_API_KEY` must be exported before
`smoke-r7.11.sh`. Stage/unstage do not need it.

## 2. Stage

```bash
bash probe-r7.11-stage.sh stage
```

Phases (each logged): (1) pre-flight: local sources, canonical md5s, no
stale `.probe-r7.11-orig`. (2) Backup `toolsets.py` + `model_tools.py`.
(3) Create `tools/r7_11_lib/`. (4) Copy 4 lib modules; rewrite
`verify_phase_tool.py` imports (`import verified_state` →
`from . import verified_state`, etc.). (5) Write 3 thin shims at top
of `tools/`. (6) Patch `toolsets.py` (append 3 names to
`_HERMES_CORE_TOOLS`) and `model_tools.py` (append 3 imports after
`tools.delegate_worker`). (7) `python3 -m py_compile` everything.
(8) Snapshot md5s to `/tmp/r7.11-stage-md5s.txt`.

Success indicators: `STAGE COMPLETE.` in stdout; toolsets.py +
model_tools.py md5s changed; 5 files in `r7_11_lib/`; 3 shims in
`tools/`; manifest at `/tmp/r7.11-stage-md5s.txt`.

## 3. Smoke

```bash
export OMLX_API_KEY=...   # if not set
bash smoke-r7.11.sh
```

Builds `/tmp/r7.11-smoke-scaffold/` (PLAN.md + real-not-stub `src/foo.py`
+ verify-config.json), launches `hermes chat -Q --max-turns 15
-t hermes-cli -m gemma-4-26B-A4B-it-MLX-8bit --source r7.11-smoke`
under a 300s hard timeout, prompts the parent to call `verify_phase`
then `end_session_for_handoff`, captures stdout/stderr/session JSON +
the post-run sentinel + verified-state.json, writes a structured
report at `/tmp/r7.11-smoke-report.md`.

Smoke ALWAYS exits 0 if it produced a report. It does NOT make
halt-or-unstage decisions — the operator does.

### Decision points (the 5 named failure modes)

1. **Did the parent call `verify_phase`?** — registration / discovery.
   No `verified-state.json` → tool never fired. Causes: not registered
   (loader error in stderr), parent didn't pick it (toolset bug),
   schema rejected (look for `InputValidationError` in stderr).
2. **Did the schema accept valid args?** — `TOOL_PARAMETERS_SCHEMA`
   bug if `InputValidationError` appears.
3. **Did the sentinel fire?** — check `.session-end-signal.json` in
   the report. Absent + parent claims it ended → `end_session_for_handoff`
   wrote elsewhere or didn't run.
4. **Did Hermes exit cleanly?** — exit code in report. For 6b scope,
   expected behavior is parent emits a final assistant message after
   both tool calls and Hermes naturally turn-ends; forced wrapper-exit
   is item 7's concern.
5. **Was `persisted_to` correct?** — should be
   `/tmp/r7.11-smoke-scaffold/verified-state.json`. Mismatch = wiring
   bug.

## 4. Open assumption to validate via smoke

Does the Hermes tool loader scan `tools/*.py` top-level only, or
recurse into `tools/r7_11_lib/`? **Investigation done (2026-04-26 via
ssh-read of `model_tools.py`)**: loader uses an EXPLICIT module import
list (lines 138–162). It does NOT scan. Existing subdirectories
(`tools/browser_providers/`, `tools/environments/`) are not loaded as
tools — they're sub-packages used by the actual tool .py files. So
`tools/r7_11_lib/` is the layout's only known risk; smoke confirms it
empirically. If stderr shows `r7_11_lib` errors during tool loading,
operator can decide whether to relocate `r7_11_lib/` outside `tools/`.

## 5. Unstage

```bash
bash probe-r7.11-unstage.sh
```

(1) Pre-flight: confirm both backups exist; if only one, fail with
PARTIAL UNSTAGE STATE. (2) Restore both files. (3) Recursively remove
`tools/r7_11_lib/`. (4) Remove 3 shims. (5) Purge stale `.pyc`. (6)
`py_compile` sanity. (7) Verify post-unstage canonical md5s.

Idempotent: unstage on a clean tree scans for orphan shim/lib files
and exits 0.

## 6. Halt-or-unstage decision tree

- **Sentinel fired AND verified-state.json `passed: true` AND no
  loader errors** → mechanism works end-to-end on a trivial case.
  Proceed to item 7 + n=5 confirmation.
- **Sentinel fired but `passed: false`** → tier 1/2/3 logic
  misaligned with trivial fixture. Debug `verify_phase.py` before
  proceeding. Unstage if blocking other work.
- **No sentinel and no verified-state.json** → tools didn't fire.
  Check stderr for tool-loader errors. If `r7_11_lib` named, §4
  assumption failed; relocate and re-stage. Otherwise, dispatch
  problem (parent didn't pick / schema rejected). Unstage and
  investigate.
- **Hermes itself crashed** (non-zero exit, no Python output) →
  unstage. Likely registration-time exception in a shim or lib init.
  Capture stderr, unstage, fix, re-stage.

Do not leave a partial stage on the VM overnight. If ambiguous,
unstage and re-stage cleanly.
