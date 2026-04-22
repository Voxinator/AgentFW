---
type: A1 judge verdict (S5)
date: 2026-04-20
campaign: r7.7 Path A
worker: S5
---
# A1 judge verdict

## Verdict: ACCEPT (with two non-blocking notes on stage-script semantics)

The A1 runtime behavior is correct and verified end-to-end on live MoE dispatches: with `HERMES_CHILD_TOOLSET_RESTRICT=1`, the child session's tools array excludes `todo`; with the flag unset, `todo` is present (r7.5 baseline preserved). Syntax is clean. The stage script is idempotent and honors the `.probe-r7.7-orig` backup contract. Two stage-chain quirks are documented below but do not invalidate A1 — they affect the stage-script's status-reporting purity, not the runtime correctness that matters for S7.

## Evidence

### 1. Syntax

- Python AST: **PASS** — `python3 -c "import ast; ast.parse(...)"` on `variants/hermes/delegate_worker_v2.py` emits `AST OK`.
- Bash syntax: **PASS** — `bash -n probe-variantJ-A1-stage.sh` emits `BASH SYNTAX OK`.
- Helper smoke-executed on the VM directly (using venv python) returns a well-typed list; `_resolve_parent_toolsets(FakeAgent)` → `['clarify','delegation','file','todo']`; `_derive_restricted_child_toolset` → `['clarify','delegation','file']`. `todo` is correctly stripped. Helper does NOT choke on a FakeAgent with `enabled_toolsets=None`, `valid_tool_names=[...]`, nor on an enabled_toolsets=list variant.

### 2. Stage script idempotency

Tripwire md5 of the local Mac-side `variants/hermes/delegate_worker_v2.py`: `cadb49504950dc40459f95f33b38dc9f`.

- Pre-test: `variantF-stage.sh status` → UNSTAGED (clean, canonical). Staged variantF (precondition per script comments).
- `variantJ-A1-stage.sh status` (post variantF stage) → reports PARTIAL because remote md5 == local (variantF uploaded the A1-patched source) but no `.probe-r7.7-orig` backup yet exists. **See Note 1 below.**
- `variantJ-A1-stage.sh stage` → idempotent no-op (local md5 == remote md5) and correctly creates the `.probe-r7.7-orig` backup defensively. Status → STAGED.
- Re-run `stage` → still reports "already staged (local == remote md5); no-op" and STATE stays STAGED. Idempotent.
- `variantJ-A1-stage.sh unstage` → "delegate_worker_v2.py restored from .probe-r7.7-orig" (copies backup back, which is byte-identical because variantF uploads the same patched source). Subsequent `status` still reports STAGED because the backup remains on disk and md5s still match — **see Note 2**.
- After manually removing the `.probe-r7.7-orig` backup, `variantJ-A1-stage.sh status` reports PARTIAL. This is expected given the stage-chain semantics.
- After `variantF-stage.sh unstage`: VM canonical. `HERMES.md` md5 = `0780c232a6cb52e13e432261f0d68ad9` ✓.

### 3. Live test — flag ON

- Model: `gemma-4-26B-A4B-it-MLX-8bit` (MoE)
- Parent toolset: `delegation,todo,clarify,file_readonly`
- Env: `HERMES_CHILD_TOOLSET_RESTRICT=1`
- Source tag: `r7.7-s5-judge-on3`
- Parent session: `/home/parallels/.hermes/sessions/session_20260420_142918_79528a.json`
- Child session: `/home/parallels/.hermes/sessions/session_20260420_142921_150a65.json`

Parent tools array (sanity):
`['clarify','delegate_task','delegate_worker','delegate_worker_v2','read_file','search_files','todo']` — 7 tools, `todo` present. Matches the parent toolset spec.

**Child tools array (the critical assertion):**
`['read_file','search_files']` — 2 tools.

- `todo` present? **NO** (expected). A1 stripped it.
- Other expected tools present? **YES** — `read_file` and `search_files` from the `file_readonly` toolset. The `delegation` and `clarify` toolsets were stripped by the canonical `_strip_blocked_tools` call in `delegate_tool.py`, as the diag predicted. The minimum viable residual for a file_readonly-only parent with A1 is exactly `{read_file, search_files}`, which is what we got.

Dispatch mechanics confirmed: the parent called `delegate_worker_v2(classification=structured, goal=...)`, which spawned a subagent whose tools array reflects the A1 restriction.

### 4. Live test — flag OFF

- Same prompt, same model, same parent toolset
- Env: `HERMES_CHILD_TOOLSET_RESTRICT` unset (explicitly unset in the ssh invocation)
- Source tag: `r7.7-s5-judge-off`
- Parent session: `/home/parallels/.hermes/sessions/session_20260420_142942_0ee9fb.json`
- Child session: `/home/parallels/.hermes/sessions/session_20260420_142945_0f7ce6.json`

Parent tools array: identical to flag-ON — 7 tools with `todo`.

**Child tools array:**
`['read_file','search_files','todo']` — 3 tools.

- `todo` present? **YES** (expected baseline).
- Baseline r7.5 behavior restored? **YES** — the diff vs flag-ON is exactly the `todo` entry, which is what A1 is designed to gate. No other tool surface drift.

The A/B is clean and minimal: only `todo` moves between flag states. This is exactly what a non-expansive, env-gated substrate strip should do.

### 5. Post-unstage canonical

- After `variantJ-A1-stage.sh unstage` + manual backup removal + `variantF-stage.sh unstage`:
  - `variantF-stage.sh status` → **STATE: UNSTAGED (clean, canonical)**.
  - VM tripwire `HERMES.md` md5: `0780c232a6cb52e13e432261f0d68ad9` — **MATCH** to canonical baseline.
  - `toolsets.py`, `model_tools.py`, `run_agent.py` all show 0 `delegate_worker_v2` references (expected canonical state).
  - `delegate_worker_v2.py` on VM is absent (moved to `/tmp/delegate_worker_v2.py.probe-r7.4-removed` by the variantF unstage). This is clean — only variantF stages that file onto the VM.
- variantJ-A1 fully unstaged? **YES.** Backup removed, and since variantF is now also unstaged, there is no `delegate_worker_v2.py` on the VM at all — the A1 overlay cannot possibly be active.

## Notes (non-blocking)

### Note 1 — Stage-chain invariance: variantF already uploads the A1-patched source

Because the Mac-side `variants/hermes/delegate_worker_v2.py` **is** the A1-patched file (the S3 edit landed in that single source-of-truth), staging variantF uploads an A1-patched `delegate_worker_v2.py` to the VM. There is no intermediate "pre-A1 β-fuse" artifact checked into the repo. Consequently:

- variantJ-A1's `stage` becomes a byte-level no-op when variantF is already staged — both are uploading the same file. The runtime-gate (`HERMES_CHILD_TOOLSET_RESTRICT` env var) is the only A/B lever.
- The `.probe-r7.7-orig` backup created by variantJ-A1 is a copy of the A1-patched file, not a pre-A1 one. If the operator wants "A/B at the file level," they can't do it through variantJ-A1's unstage — they must regress the repo file itself (via git) and re-stage variantF.

This is consistent with the plan's design (§6.6: "runtime behavior still gated by HERMES_CHILD_TOOLSET_RESTRICT=1"). The env-var gate is the A/B mechanism, and my live tests validated both sides of that mechanism. So this is a stage-script-status-reporting quirk, not a functional defect.

Recommendation for S7: keep the runtime env-var as the A/B selector. Do not use stage/unstage for A/B.

### Note 2 — `variantJ-A1-stage.sh status` doesn't cleanly toggle to UNSTAGED post-unstage

After `unstage`, the script copies `.probe-r7.7-orig` back over `delegate_worker_v2.py`. Because both files are byte-identical, md5s match, and the `status` check still reports STAGED (its decision rule is `remote==local && backup_present → STAGED`). The backup remains on disk forever unless removed manually.

Why it still doesn't break the ship: after a full `variantF unstage`, the remote `delegate_worker_v2.py` disappears entirely, so the stale `.probe-r7.7-orig` becomes orphaned. The ultimate canonical check is the variantF status line, which is clean.

Recommendation (not a blocker): the S3 `unstage` could `rm -f delegate_worker_v2.py.probe-r7.7-orig` after restoring, so subsequent `status` cleanly reports UNSTAGED. I did not edit the script per constraints; logging for follow-up.

### Note 3 — Pre-existing "unhashable type: 'slice'" error surfaces intermittently on `delegate_worker_v2`

My first live attempt (flag ON, classification=one-shot) hit: `Error executing tool: Error during OpenAI-compatible API call #1: unhashable type: 'slice'`. This is **NOT** introduced by A1: (a) one-shot path returns before any A1 code runs, (b) the same error string appears in session JSONs dating back to 2026-04-19 (pre-A1), (c) my second and third live tests on the same code path succeeded cleanly. Two sessions from 2026-04-19 reproduced it (`session_20260419_124936_789d14.json` among others), so this is an existing β-fuse flake unrelated to this campaign. Logging for awareness; not a reason to reject A1.

## If REJECT: what to fix (for S3 re-dispatch)

N/A — verdict is ACCEPT.

## If ACCEPT: ready for S7 smoke test

**YES.** A1's runtime contract is met:

1. With `HERMES_CHILD_TOOLSET_RESTRICT=1`: child sessions spawned via `delegate_worker_v2` (structured/long-horizon) have `todo` stripped from their tools array. Verified on live MoE dispatch.
2. Without the env var: child sessions inherit the parent's toolset including `todo`. r7.5 baseline preserved. Verified on live MoE dispatch.
3. Stage script is idempotent and honors backup semantics; VM returns to canonical state cleanly after unstage of both variantJ-A1 and variantF.
4. Helper is non-expansive (cannot grant the child tools the parent lacks — intersection logic in `delegate_tool.py:242-243` enforces this regardless).
5. No grandchild concern (MAX_DEPTH=2 + `delegation` blocked for children; diag §2-Q4).

S7 should proceed once A2 also passes its judge. For the Arm G ablation probe (A1-only) the runtime gate is the env var flip; the staged binary is identical either way.
