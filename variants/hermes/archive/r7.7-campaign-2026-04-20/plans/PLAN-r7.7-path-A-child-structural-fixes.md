[TASK CLASS: long-horizon]
Justification: Multi-session Hermes variant r7.7 — structural child-level fixes (A1 toolset restriction + A2 runtime write-before-claim gate). Self-contained handoff + plan so a fresh agent can resume cold.

# HANDOFF + PLAN — r7.7 Path A (child-structural fixes)

**Author:** the agent that ran r7.6 autonomously overnight 2026-04-19→04-20.
**Date:** 2026-04-20 (early morning, post-r7.6-MORNING-SUMMARY).
**Operator:** Brian Taylor (voxinator@gmail.com).
**Self-containment promise:** you should not need to read any other artifact to understand state, context, and the implementation plan. Cross-references are evidence trails, not prerequisites.

---

## 1. TL;DR

The Hermes variant of AgentFW ships the **β-fuse dispatch architecture** (r7.4 SHIP-WITH-CAVEAT on the dispatch gate) but does NOT yet ship a **worker-quality-reliable flywheel** (operator's pre-committed ≥75% floor not met in r7.6).

Fresh-LLM re-judgment of all 40 r7.6 P1-C trials puts the truth at:
- **Arm A (no scaffold):** 4/20 worker-quality PASS (20%)
- **Arm B (HERMES-WORKER.md scaffold):** 8/20 PASS (40%)
- **Delta:** +4 absolute / +20pp rate

The scaffold is real lift but hits a ceiling driven by two specific failure modes:
1. **Fabrication** — child claims `Created X` / `Wrote X` with **zero** corresponding write tool calls (dominant on T10; 4+ trials affected). `todo` is being used as a write-substitute (child marks "write_file=completed" in its todo list).
2. **Thrash** — child stalls in search loops or mid-investigation planning without reaching §3 BLOCKED template (dominant on T5/T6).

**Path A** addresses (1) directly and (2) partially via **structural** fixes at the child-session level, mirroring the campaign's repeatedly-demonstrated pattern: *language-level guardrails have a ceiling on a 26B MoE; structural enforcement at the tool/runtime surface produces step-functions.*

**A1 — Child toolset restriction.** Strip `todo` from the default child toolset. A1 removes the **dominant** `todo`-as-write fabrication substrate observed on r7.6 T10 trials. Other fabrication routes (prose-only "Created X" with no matching tool call at all; pseudo-tool-call emission in assistant content) remain — those are caught post-hoc by A2 but are not structurally prevented. A1 eliminates ONE substrate, not all fabrication.

**A2 — Write-before-claim runtime gate.** Hermes-side hook at session-close: scan final content for completion claims naming files; require matching write tool call; inject correction + retry if absent; close with `FABRICATED` verdict if the child won't correct.

These two fixes do **not** require hardware upgrades (operator's empirical: 122B too heavy; Qwen3.5 weak at tool calls; Gemma-4-31B is the best efficient option). They reuse the existing probe infrastructure stack.

**Estimated effort:** ~6-8h implementation + ~6-8h probing + judge verification.

**Ship gate (re-stated from r7.6):** Arm B+A1+A2 (or equivalent "Arm F") ≥15/20 absolute MoE worker-quality PASS on the 4 structured/LH task set (T4/T5/T6/T10). r7.6 Arm B baseline was 8/20; +7 lift required.

---

## 2. Campaign arc + where we are

### The arc (short version)

| Probe | Intervention | Dense 1st-attempt | MoE 1st-attempt | Worker-quality | Character |
|-------|--------------|-------------------|-----------------|----------------|-----------|
| r7 (retally) | Variant D/E + retry wrapper | 0% | — | n/a | prompt + scaffolding |
| r7.2 | corrected baseline | 20% | 0% | n/a | prompt-only |
| r7.3 L1+L2 | toolset restriction + escape-hatch text | 6.7% | 6.7% | n/a | prompt + minor structural |
| r7.4 β-fuse | required `delegate_worker_v2` tool with classification+justification+goal | 77% | 85% | n/a | **major structural** — SHIPPED as pre-release |
| r7.5 v2.1 | + turn-0 toolset restriction | n/a | 85% | **3/20** introduced | full structural on dispatch |
| r7.6 | + HERMES-WORKER.md child scaffold + Fixes 2/3/4/5 | n/a | — | **8/20** (fresh-LLM) | scaffold-level worker |
| **r7.7 Path A** | + A1 child toolset restriction + A2 write-before-claim runtime gate | tbd | tbd | **≥15/20** target | **structural worker** |

### Key campaign lessons (load-bearing)

- **Prompt-engineering hits ceilings.** r7.2 → r7.3 was flat despite escape-hatch stripping; r7.6 HERMES-WORKER.md gets 20→40% worker quality but can't reach 75%.
- **Structural fusion produces step functions.** r7.3 → r7.4 β-fuse was 6.7% → 77-85% dispatch. Removing the *choice* beats asking the model nicely.
- **Dispatch and worker quality decouple.** β-fuse solved dispatch; it doesn't touch what happens inside the child. Worker quality is a separate ship dimension.
- **Heuristic judges miss semantic failures.** r7.6's Python regex scorer was systematically biased; fresh-LLM judges caught `Created X`-with-zero-writes and `28 turns of thrash`-with-honest-summary patterns the heuristic couldn't see.
- **Measurement is load-bearing.** Inflated metrics (r7 claimed 60% / real 0%; r7.6 heuristic claimed 12/20 Arm B / real 8/20) have distorted every ship decision. Fresh-LLM calibration is the standing fix (see `CALIBRATION-r7.6-judge-protocol.md`).

---

## 3. Current state (verified 2026-04-20 early morning)

### Repo + pre-release status

- **GitHub tag:** `r7.5-hermes-prerelease` — immutable; the pre-release milestone. Untouched.
- **main branch:** `git log r7.5-hermes-prerelease..HEAD` is empty — HEAD commit IS the tag commit. The "drift" is uncommitted working-tree state, not history. Specifically:
  - **1 uncommitted edit** to `variants/hermes/HERMES-variantF.md` md5 `01c0e77b…` → `24e8d1c0…` (Fix 4 added item #6 "Retry Re-Classification"; +1 line, working-tree only).
  - **164 untracked files** — artifacts from the r7.6 overnight work (see §14).
  - Fix 3 + Fix 4 wrapper patches to `probe-variantI-wrapper.sh` / `probe-variantH-wrapper.sh` are IN the pre-release commit already (not drift).
  - `/tmp/probe-r7.6-P1C-logs/judge-trial.py` — Fix 2 patches (ephemeral /tmp; recoverable from `ARTIFACT-r7.6-P1C-fix2-impl.md`).
- **Operator has not yet decided** whether to (a) new-tag for the uncommitted HERMES-variantF.md edit or (b) amend release notes. Flag for operator at session start.

### VM state (on ubuntu-vm per Parallels)

All staging unstaged. VM is CANONICAL. As of morning summary:
- `~/.hermes/hermes-agent/HERMES.md` md5 = `0780c232a6cb52e13e432261f0d68ad9` (canonical)
- `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md` md5 = `fb1a5a5208a6cf2fcb8252aac10397eb`
- `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh` md5 = `a1dce6e989527686124d0860830627c9`
- `/media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts` md5 = `5503ee1c2ef7d635a020eea275e41239`
- Source patch chains on VM (each with `.probe-d-orig` through `.probe-r7.6-orig` backups): `model_tools.py`, `run_agent.py`, `toolsets.py`. `delegate_worker_v2.py` is staged INTO `~/.hermes/hermes-agent/tools/` when variantF is applied and removed when unstaged — it has no persistent backup chain at the canonical top level.
- HERMES-WORKER.md NOT on VM (removed at last unstage)

**Re-verify at session start** via `probe-preflight.sh` (see §5).

### Monday cron status

Next Jira cron runs **weekday 8am** (depending on session date). Tripwires (HERMES.md + SKILL.md + jira-briefing.sh) must stay canonical through cron windows. The current pre-release architecture does NOT interfere — canonical HERMES.md doesn't reference β-fuse tools, so the source patches are silent under cron.

### Hardware constraints (operator-confirmed 2026-04-20)

- Mac: macOS 26.3.1 / M5 Max / 128 GB unified. Parallels Desktop 26.3.0.
- **Gemma-4-31B-it-4bit** (dense) — **best efficient model** per operator.
- **Gemma-4-26B-A4B-MLX-8bit** (MoE) — usable, less hardware stress for long runs.
- **Qwen3.5 family** — operator tried, found **terrible at tool calls**. Do NOT recommend or use.
- **122B models** — operator tried, does not run efficiently on their hardware.
- Therefore: **r7.7 probes remain on Gemma-4 MoE** (Gemma-4-26B-A4B-MLX-8bit) unless operator explicitly requests dense. Dense is viable but has shown oMLX orphaned-session memory pressure during sustained runs; requires pre-probe oMLX restart discipline.

### oMLX operational knowledge

- Runs on `localhost:8000` (Mac) / `10.211.55.2:8000` (from VM perspective).
- `/v1/*` endpoints require API key. Operator's dev key lives in `OMLX_API_KEY` env var (value `<REDACTED>`; local dev only). **Never commit the value.** Secret-redacted in one repo location; scans must be run before any commit (see `ARTIFACT-r7.5-git-commit-plan.md` precedent).
- `/api/status` (auth'd) exposes `active_requests` — used by `probe-omlx-health-check.sh`.
- **Known failure mode:** long probe runs (~90min+) accumulate orphaned sessions → memory pressure → swap spike → degraded tok/s. Pre-probe oMLX restart is advised for ANY long run.
- **Swap threshold:** operator overrode default 5.0 GB to 5.5 GB on 2026-04-19 since M5 Max's small 6 GB swap trips easily even at healthy free mem. Set `OMLX_SWAP_MAX_GB=5.5` in preflight.

---

## 4. Why Path A (the data motivating A1 + A2)

### Fresh-LLM verdicts per task (r7.6 MoE Arm B, n=20)

| Task | Class | PASS / total | Dominant failure mode |
|------|-------|--------------|------------------------|
| T4 | structured (auth refactor) | **4/4 non-LOST** | — (scaffold works perfectly) |
| T5 | structured (bug-hunt stale-data) | 0/5 | **Thrash** — wrong cwd, duplicative searches |
| T6 | long-horizon (export feature) | 2/4 non-LOST | Mixed — partial wins when relevant files found |
| T10 | long-horizon (postgres migration) | 2/4 non-LOST | **Fabrication** — `Created PLAN.md` with zero writes |

### The two dominant structural failure modes

**Mode 1 — `todo`-substrate fabrication.** Observed in REJ-A-T10-run1, REJ-A-T10-run3, REJ-A-T10-run4, REJ-B-T10-run2, REJ-B-T10-run5, and trials 18+20 from the original P1-C data. Pattern:

```
Child creates a todo list with item "id=write_file, description='Create PLAN.md'".
Child marks the todo item as 'completed' (without any real write happening).
Child's final summary claims "Created migrations/pg12-to-pg16/PLAN.md".
VM inspection confirms: NO write_file/patch/terminal calls in the session.
File does NOT exist on disk.
```

The `todo` tool lets the child **mutate an internal state** (task status) without touching the filesystem. The model conflates "task marked completed" with "artifact produced." Removing `todo` from the child's toolset removes the substrate.

**Mode 2 — Search thrash without write.** Observed across multiple T5/T6 Arm A trials + REJ-B-T5-run2 + REJ-B-T6-run5. Pattern:

```
Child searches for files/patterns with increasing desperation.
Never finds the target (either task specifies non-existent paths or child looks in wrong cwd).
Runs out of turn budget (20+ turns) or gets truncated mid-thought.
Final message is empty or a planning fragment.
```

Mode 2 is partially addressed by A2 (if the child makes a fabricated claim about search findings, A2 catches it). Mostly it's addressed by A1 indirectly (without `todo`, the child has less to thrash on; can't mark TODO-style "plan" as completed).

**Mode 2 is NOT fully solved by Path A.** Some T5/T6 trials will still fail even with A1+A2 because the underlying issue is "child can't find relevant files in this workspace." This is a task/environment mismatch, not a structural Hermes issue. r7.7 should document this limit rather than try to fix it in-scope.

### Near-tripwire incidents (r7.6)

Two Arm B T10 children attempted to write INTO `~/.hermes/hermes-agent/` (the protected agent-source tree):
- REJ-B-T10-run2: tried to write `MIGRATION_PLAN.md` at `/home/parallels/.hermes/hermes-agent/`
- REJ-B-T10-run5: siblings targeted `~/.hermes/hermes-agent/exports-feature/`

Prevented only because `terminal` was not in the child's toolset (writes required terminal in these cases). **A1 strengthens this** (if `todo` is gone, children may pick `terminal` next — need to monitor). **A2 does not directly prevent out-of-scope writes; that's a separate (future) scope gate.**

---

## 5. Pre-flight for the fresh session

```bash
# 0. Read these (in order, 30-45 min):
#    1. This file (plan + handoff)
#    2. ARTIFACT-r7.6-MORNING-SUMMARY.md
#    3. PLAN-r7.6-P1C-fixes-implementation.md (the operator's rev-2 plan, for style + prior-art)
#    4. ARTIFACT-r7.4-sigterm-research.md (Hermes internals; A2 needs hook point knowledge)
#    5. ARTIFACT-r7.5-F1-judge-brief.md (the rubric; reuse for probing)
#    6. CALIBRATION-r7.6-judge-protocol.md (standing calibration protocol)

# 1. Preflight script existence check (new in r7.6 Fix 5; may not be tracked):
test -x /Users/briantaylor/Projects/AgentFW/probe-preflight.sh || {
    echo "preflight script missing — see ARTIFACT-r7.6-P1C-fix5-impl.md to reconstruct"; exit 2;
}

# 2. OMLX_API_KEY presence check (do NOT proceed with empty value):
test -n "$OMLX_API_KEY" || {
    echo "OMLX_API_KEY not set — confirm with operator before continuing"; exit 2;
}

# 3. Agent-dispatch capability — do NOT hand-set AGENT_DISPATCH_AVAILABLE.
#    Instead, verify by dispatching a trivial Agent sub-agent probe; if the
#    spawn succeeds, preflight's agent_dispatch gate passes. If you lack the
#    Agent tool in your current context, dispatch judges from MAIN session
#    (as r7.6 did on 2026-04-20) — see §9.5.

# 4. Operator override for oMLX swap threshold (M5 Max 6 GB swap is tight):
export OMLX_SWAP_MAX_GB=5.5

# 5. VM canonical verification (via new preflight gate):
/Users/briantaylor/Projects/AgentFW/probe-preflight.sh
# Expect: PREFLIGHT=PASS. If FAIL, halt and escalate.

# 6. Confirm rev-2 fixes landed (md5 -q on macOS):
md5 -q /Users/briantaylor/Projects/AgentFW/probe-preflight.sh \
       /Users/briantaylor/Projects/AgentFW/CALIBRATION-r7.6-judge-protocol.md \
       /Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh \
       /Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh \
       /Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantF.md
# Baselines in §14.

# 7. Snapshot for rollback:
cp -a /tmp/probe-r7.6-P1C-logs /tmp/probe-r7.7-snapshot-pre-pathA-$(date +%Y%m%d-%H%M)

# 8. oMLX restart BEFORE any long probe. See §5.2 for CLI vs operator-gate policy.
```

### 5.1 VM access alias

All VM access in this plan uses `ssh ubuntu-vm --` as shorthand for `ssh parallels@<vm-host> --`. The alias is configured in `~/.ssh/config` on the Mac. Verify in preflight:

```bash
ssh ubuntu-vm -- true || { echo "ssh ubuntu-vm alias broken — check ~/.ssh/config"; exit 2; }
```

Halt on failure — all worker briefs in §6.3 / §6.4 / §7.6 depend on this alias resolving.

### 5.2 oMLX restart — operator-gated in autonomous mode

oMLX lacks a verified CLI restart recipe on this host; the operator typically restarts via the oMLX Mac UI. In autonomous mode, the fresh agent CANNOT click Mac UI buttons. Policy:

- **Interactive/co-driven mode:** operator restarts oMLX on request before any long probe.
- **Autonomous mode:** oMLX restart is a **mandatory operator-interaction-required gate**. Added to §13 decision points. Agent halts + escalates when a pre-probe restart is needed and waits for operator confirmation.

(If a verified CLI recipe like `launchctl kickstart -k user/$UID/com.omlx.server` is confirmed in a future session, this policy can relax. Do not assume.)

---

## 6. Fix A1 — Child toolset restriction

### 6.1 Problem restated

The default child-session toolset (resolved in Hermes when a parent calls `delegate_task` / `delegate_worker_v2`) includes `todo`. The `todo` tool permits the child to mutate an internal "task status" state without any file-system side effect. In combination with long-horizon task framing, the model conflates "todo item marked completed" with "artifact produced."

### 6.2 Hypothesis tree (similar to Fix 4 pattern)

Before implementation, a fresh research sub-agent should distinguish:

- **H-A1a:** default child toolset is resolved in `~/.hermes/hermes-agent/toolsets.py` via a named set (e.g., `hermes-cli` or `hermes-worker-default`). Removing `todo` is a one-line edit there.
- **H-A1b:** default child toolset is resolved in `~/.hermes/hermes-agent/tools/delegate_tool.py::_build_child_system_prompt` or a sibling function. May be dynamic / derived.
- **H-A1c:** default child toolset is inherited from parent (`toolsets=None` means "copy parent's"). Parent's toolset is `delegation,todo,clarify,file_readonly` (the probe-supplied toolset), so the child ALREADY has `todo` via inheritance. If this is the case, A1 needs different mechanics (e.g., a new `delegate_worker_v2_scoped` that passes a restricted toolset to the child).

**Likely H-A1c.** Investigation must confirm before implementation.

### 6.3 Research worker brief

Read-only investigation. Produce `ARTIFACT-r7.7-A1-diag.md`.

```
Questions:
1. In `~/.hermes/hermes-agent/`, where is the child's default toolset resolved?
   - Grep: `rg -n "toolset|tools" ~/.hermes/hermes-agent/tools/delegate_tool.py`
   - Grep: `rg -n "child|spawned|delegate" ~/.hermes/hermes-agent/toolsets.py`
2. Does `delegate_task` (the underlying function called by delegate_worker_v2 handler)
   accept a `toolsets` argument? If None, what's the default?
   - File: `~/.hermes/hermes-agent/tools/delegate_tool.py` — trace the `toolsets=None` path.
3. Is the child's toolset INHERITED from parent or RESOLVED FRESH?
   - Inspect a fresh child session JSON: does its tools array match the parent's, or is it a static set?
   - Cross-reference: probe-variantH-check.py already inspects child tools via jq. Use that to confirm.
4. If fresh-resolved: what named toolset is used? Check `toolsets.py` entries.
5. If inherited: what's the best hook point to restrict? Is there a parameter the spawning call can pass?

Deliverable: file:line-cited answer to each question. Recommended hook point for A1. 
5-10 line sketch of the patch.
```

### 6.4 Implementation worker brief (conditional on diag)

**If H-A1a or H-A1b (fresh-resolved):** edit the toolset-resolution site to exclude `todo` when a feature flag is set. Flag via env var `HERMES_CHILD_TOOLSET_RESTRICT=1` (preferred) or a module-level boolean.

**If H-A1c (inherited):** modify `delegate_worker_v2`'s handler (in `variants/hermes/delegate_worker_v2.py` — Mac-side, deployed to VM via `probe-variantF-stage.sh`) to pass an explicit `toolsets` argument that excludes `todo`. Specifically:

```python
# Current (r7.5-shipped):
def delegate_worker_v2(classification, justification, goal=None, parent_agent=None):
    ...
    if classification in ("structured", "long-horizon"):
        return delegate_task(
            goal=goal,
            context=None,
            toolsets=None,   # ← inherits parent
            ...
        )

# Proposed (A1):
def delegate_worker_v2(classification, justification, goal=None, parent_agent=None):
    ...
    if classification in ("structured", "long-horizon"):
        # A1: restrict child toolset — remove todo (fabrication substrate)
        restricted = _derive_restricted_child_toolset(parent_agent)  # new helper
        return delegate_task(
            goal=goal,
            context=None,
            toolsets=restricted,  # ← explicit, excludes todo
            ...
        )
```

`_derive_restricted_child_toolset()` must mirror the three-way fallback already present in `delegate_tool.py`'s resolution path (per I2 §1): **`parent.enabled_toolsets` → `parent.valid_tool_names` → `DEFAULT_TOOLSETS`**. A naive implementation that only reads `parent.enabled_toolsets` and drops `todo` returns `[]` when `enabled_toolsets is None` — which leaves the child with zero tools and causes silent dispatch failure.

```python
def _resolve_parent_toolsets(parent_agent):
    """Mirror delegate_tool.py's three-way fallback."""
    if getattr(parent_agent, "enabled_toolsets", None):
        return list(parent_agent.enabled_toolsets)
    if getattr(parent_agent, "valid_tool_names", None):
        return list(parent_agent.valid_tool_names)
    return list(DEFAULT_TOOLSETS)  # import from toolsets.py

def _derive_restricted_child_toolset(parent_agent):
    """A1: parent's resolved toolsets minus todo (fabrication substrate)."""
    resolved = _resolve_parent_toolsets(parent_agent)
    return [t for t in resolved if t != "todo"]
```

**Required unit test:** `parent_agent` with `enabled_toolsets=None` and `valid_tool_names=None` → `_derive_restricted_child_toolset` returns `DEFAULT_TOOLSETS` minus `todo`, NOT `[]`. Fail the build if this assertion does not hold.

### 6.5 A1 patch plan

- Modify `variants/hermes/delegate_worker_v2.py` with the above pattern (or whatever diag confirms).
- Stage via new `probe-variantJ-stage.sh` that stacks on top of variantI with `.probe-r7.7-orig` backup suffix.
- Feature-flagged via env var so A/B comparison is clean.

### 6.6 A1 verification (before probe)

- Stage variantJ. Invoke Hermes directly with a structured task under MoE.
- Verify: child session JSON's tools array does NOT contain `todo`.
- Verify: child session JSON's tools array DOES contain `read_file`, `search_files`, `delegate_*` (minimum viable child toolset).
- Verify: env var toggles it — without the flag, child gets default toolset (including `todo`).

---

## 7. Fix A2 — Write-before-claim runtime gate

### 7.1 Problem restated

A child can emit a final summary claiming `Created X` / `Wrote X` / `Updated X` / `Files created: Y` without any corresponding write tool call. Post-hoc detection (F4A in `probe-variantH-check.py`) catches this at judge-time, but the bad behavior already happened. A runtime gate **prevents it** — the child cannot close the session with a fabricated claim.

### 7.2 Design

**Hook point:** at the session-close decision in Hermes' conversation loop. Per the B.0 research (`ARTIFACT-r7.4-sigterm-research.md`), session persistence is inline in `run_conversation`. Do NOT anchor on line number (upstream Hermes updates shift line numbers; r7.6 snapshot said ~9109 but that will rot). **Locate with:**

```bash
grep -n 'def run_conversation' ~/.hermes/hermes-agent/agent/run_agent.py
# then, within that function body, find the first call to _persist_session (or
# whatever save sentinel B.0 research names). A2 gate fires IMMEDIATELY BEFORE
# that call — before the child's final assistant message is committed as the
# session's last turn.
```

If the grep anchor ever returns zero matches or multiple functions, halt and escalate — Hermes internals have shifted materially and B.0 research must be re-run.

**Gate logic:**

```python
# Pseudo-code
def write_before_claim_gate(session, final_assistant_content):
    """
    Return (ok: bool, correction_message: Optional[str]).
    If ok=False, caller should inject correction_message and re-prompt the model.
    """
    claimed_files = extract_claimed_files(final_assistant_content)
    # regex for: Created X / Wrote X / Updated X / Generated X / Saved X / Files created:
    # X = recognizable file path (extension or / prefix)
    if not claimed_files:
        return (True, None)  # no claims → nothing to check
    
    write_calls = extract_write_tool_calls(session.messages)
    # tool names: write_file, patch, execute_code, terminal, skill_manage
    # (and heuristic prefix match for write_*/edit_*)
    written_paths = {path for call in write_calls for path in extract_paths_from_call(call)}
    
    unbacked = [f for f in claimed_files if not any(_matches(f, p) for p in written_paths)]
    
    if not unbacked:
        return (True, None)  # every claim is backed by a write
    
    correction = (
        f"Your summary claims you created or modified the following file(s):\n"
        + "\n".join(f"  - {f}" for f in unbacked)
        + "\n\nBut no corresponding write_file / patch / terminal / execute_code tool call "
        f"exists in this session for them.\n\n"
        f"Choose one:\n"
        f"  (a) Actually call write_file / patch / terminal / execute_code now to create the file(s), OR\n"
        f"  (b) Rewrite your summary honestly stating you did NOT create the file(s) "
        f"and explain why (BLOCKED template).\n\n"
        f"Do not claim the file exists if it does not."
    )
    return (False, correction)

def run_conversation_close_hook(session):
    max_write_before_claim_retries = 2
    for attempt in range(max_write_before_claim_retries + 1):
        final = last_assistant_content(session)
        ok, correction = write_before_claim_gate(session, final)
        if ok:
            return "NORMAL_CLOSE"
        if attempt == max_write_before_claim_retries:
            # Give up — log as FABRICATED outcome
            append_system_note(session, "A2_GATE_EXHAUSTED: claim remained after %d retries" % attempt)
            return "FABRICATED"
        # Inject correction and re-run one more turn
        session.messages.append({"role": "user", "content": correction})
        run_one_more_turn(session)
    return "FABRICATED"
```

### 7.3 Regex calibration for claimed-file extraction

Reuse the regex from the r7.6 Fix 4 patch (F4A), which was calibrated against the T10 fabrication trials:

```python
COMPLETION_CLAIM_RE = re.compile(
    r'\b(created|wrote|generated|saved|written)\b.{0,120}?'
    r'(?:[~/][\w./-]+|[\w/-]+\.(?:md|py|sh|ts|js|yaml|yml|json|toml|txt|cfg|ini))',
    re.IGNORECASE | re.DOTALL,
)
FILES_BLOCK_RE = re.compile(
    r'(?im)^\s*(?:files\s+(?:created|modified|added|changed)):\s*$'
)
```

**Known FP case:** `updated` was removed from the verb set after T02 FP. DO NOT re-add without re-calibration against trials 01/02/05.

**Known FN case:** bare path-only claims ("MIGRATION_PLAN.md is ready") don't match. Acceptable — false negatives are preferable to FP at this gate since an FP loops the model.

### 7.4 Write-tool name enumeration

Per I2 §4 verification against canonical `toolsets.py`, `edit_file` and `apply_diff` are NOT real tool names in this Hermes version — they were carried over from a different toolchain assumption. `skill_manage` inclusion is questionable (may be metadata-only, not file-write). Trimmed to the verified-real set plus a forward-compat prefix matcher:

```python
WRITE_TOOL_NAMES = frozenset({
    'write_file', 'patch', 'execute_code', 'terminal', 'skill_manage',
    # NOTE: verify skill_manage file-write semantics at S2 — drop if metadata-only.
    # Drop or extend this frozenset only after grep-confirming in toolsets.py on VM.
})
def is_write_tool(name: str) -> bool:
    # Prefix matcher kept for forward-compat against future tool additions
    # (e.g., write_X, edit_X, patch_X). Current toolset has no such names,
    # but the matcher is cheap and avoids an FN regression on next Hermes upgrade.
    return name in WRITE_TOOL_NAMES or name.startswith(('write_', 'edit_', 'patch_'))
```

### 7.5 Path-matching logic

When the claim says `Created /path/to/X.md` and the write tool call was `write_file(path='/path/to/X.md', ...)`:
- Exact match ✓
- Normalize leading `~/` → expand
- Normalize multiple slashes
- If claim says just `X.md` and write was to `subdir/X.md`: substring match by basename (conservative — may false-positive on common names)

For r7.7 v1, use **conservative exact + basename match**. Refine iteratively if probe data shows FN/FP.

### 7.6 A2 implementation plan

1. **Locate the hook point in `run_agent.py`** via the grep-anchor method in §7.2 (do NOT hard-code line numbers; B.0's ~9109 snapshot will rot with upstream Hermes updates). The gate fires BEFORE the first `_persist_session` call inside `run_conversation`.
2. **Add the gate function + helper utilities.** ~80-120 LOC in `run_agent.py` or a new module `agent/write_before_claim_gate.py` imported from `run_conversation`.
3. **Env-var gating:** `HERMES_WRITE_BEFORE_CLAIM_GATE=1` enables. Default off for production-canonical safety.
4. **Retry budget:** `HERMES_WBC_MAX_RETRIES` env var, default 2.
5. **Verdict surface:** when gate fires, session JSON gets a new top-level field `a2_gate_outcome: "PASSED" | "CORRECTED" | "FABRICATED"`. Downstream judging uses this.

### 7.7 A2 verification (before probe)

- Unit test: feed synthetic session JSONs through the gate:
  - Clean trial (no claims): ok=True
  - Claim + matching write: ok=True
  - Claim + no write: ok=False, correction emitted
  - Multiple claims, some matched: ok=False for unmatched
- **Runtime-regex calibration gate (ship-blocking at S6):** the F4A regex was calibrated for judge-time inspection. Runtime firing operates on different content (partial turns, clarification loops, out-of-context summaries — see §12 Mode 4). Before S7 smoke, feed the gate **10 synthetic + 10 real r7.6 session JSONs** sampled across (a) FABRICATED, (b) honest-blocked (§3 BLOCKED template), (c) normal-PASS. Required thresholds:
  - **≥9/10 precision** (false-positive rate ≤10%; critical because FP loops the model)
  - **≥8/10 recall** (false-negative rate ≤20%; some FN acceptable since the judge still catches missed ones post-hoc)
  - Below either threshold → S7 cannot start. Re-calibrate regex (tighten verb set, adjust path anchor) and re-run the gate. Document iterations in `ARTIFACT-r7.7-A2-runtime-calibration.md`.
- Integration test: run one live MoE trial on a T10 prompt with gate enabled. Confirm:
  - If child fabricates, correction is injected
  - If child corrects, session closes normally
  - If child doesn't correct after max retries, session closes with `a2_gate_outcome="FABRICATED"`

---

## 8. Implementation sequencing

Derived from the operator's own rev-2 plan style (see PLAN-r7.6-P1C-fixes-implementation.md §8):

| Step | Action | Runs in | Blocks | Blocked by |
|------|--------|---------|--------|------------|
| S0 | §5 pre-flight + read handoff | main session | all | — |
| S1 | A1 diag worker (read-only VM investigation) | sub-agent | A1 impl | S0 |
| S2 | A2 hook-point research worker (locate exact `run_conversation` close point; verify against B.0 findings) | sub-agent | A2 impl | S0 |
| S3 | A1 impl worker (edit `delegate_worker_v2.py` + new variantJ-stage.sh) | sub-agent | A1 judge | S1 |
| S4 | A2 impl worker (edit `run_agent.py` + env flag + retry + verdict field) | sub-agent | A2 judge | S2 |
| S5 | A1 judge (cold-verify toolset actually restricted via direct hermes invocation) | fresh sub-agent | combined smoke | S3 |
| S6 | A2 judge (cold-verify gate fires + retries + verdict via synthetic session unit tests + 1 live trial + **runtime-regex calibration gate**: feed gate 10 synthetic + 10 real r7.6 session JSONs spanning FABRICATED / honest-blocked / normal-PASS; require ≥9/10 precision AND ≥8/10 recall. **Ship-blocking** — S7 cannot start until this gate passes.) | fresh sub-agent | combined smoke | S4 |
| S7 | Integration smoke test: stage variantJ (A1+A2), run 2 MoE trials (T4 + T10), expect clean A1 tools array + A2 gate fires on T10 fabrication | main session dispatches worker | probe matrix | S5, S6 |
| S8 | Ablation probe matrix (see §9) | main session + workers | ship judge | S7 |
| S9 | Ship judge (fresh sub-agent applies pre-committed thresholds) | fresh sub-agent | — | S8 |
| S10 | Ship decision (operator gate — no canonical swap without explicit approval) | main session | — | S9 |
| S11 | PROGRESS + morning-equivalent summary update | main session | — | S10 |

Parallelizable: S1 and S2 (independent reads). S3 and S4 (independent files). S5 and S6 (independent verifications).

Serialize: S7 must follow S5/S6. S8 must follow S7. Ship judge (S9) after S8 data is complete.

### 8.5 Judge-rejection protocol

If S5 (A1 judge) or S6 (A2 judge) issues REJECT:

1. **Main session reads the judge findings** from `ARTIFACT-r7.7-<S5|S6>-judge.md`. Main session does NOT attempt the fix itself.
2. **Main session dispatches a NEW worker** for the re-implementation. **Do NOT reuse the S3/S4 worker context** — the original worker's accumulated assumptions are exactly what the judge rejected; reusing that context reproduces the same failure mode. The new worker gets: (a) original spec from §6 / §7, (b) the judge's findings verbatim, (c) a clean context.
3. **Max 2 judge iterations per fix.** After 2 rejections on the same fix, halt the sequencing matrix and escalate to operator with all three artifacts (original impl + 2 judge verdicts) for scope reconsideration. Do not attempt a 3rd autonomous iteration.
4. **S7 smoke test blocks on both S5 and S6 accepting.** Partial-accept (A1 accepted, A2 rejected) does not unblock S7 — both structural fixes must land clean before integration smoke.
5. **Log every rejection + re-dispatch** in PROGRESS.md as a separate S-step row (e.g., `S5.1 A1 judge REJECT → S3.1 A1 impl v2 (new worker)`).

---

## 9. Probing plan — ablation matrix

### 9.1 Goal

Measure A1 + A2's marginal worker-quality lift over r7.6 Arm B baseline. Determine whether combined A1+A2+scaffold crosses ≥15/20 (operator's 75% floor).

### 9.2 Arms

Three arms, 20 trials each, MoE (Gemma-4-26B-A4B-MLX-8bit):

| Arm | Env / Staging | Expected source |
|-----|---------------|-----------------|
| **Arm B (re-baseline, if needed)** | variantF + variantG + variantH + variantI staged; HERMES_WORKER_OVERLAY=1; HERMES_CHILD_TOOLSET_RESTRICT=0; HERMES_WRITE_BEFORE_CLAIM_GATE=0 | r7.6 data — reuse if ≤2 weeks stale |
| **Arm G** | variantJ additionally staged; HERMES_CHILD_TOOLSET_RESTRICT=1; HERMES_WRITE_BEFORE_CLAIM_GATE=0 (**A1 only, no scaffold**) | New probe |
| **Arm H** | variantJ staged; HERMES_CHILD_TOOLSET_RESTRICT=0; HERMES_WRITE_BEFORE_CLAIM_GATE=1 (**A2 only, no scaffold**) | New probe |
| **Arm F** | variantJ + variantI + HERMES_WORKER_OVERLAY=1 + HERMES_CHILD_TOOLSET_RESTRICT=1 + HERMES_WRITE_BEFORE_CLAIM_GATE=1 (**everything on**) | New probe |

**Operator time budget call:** running all 4 arms × 20 trials = 80 MoE trials + 80 fresh-LLM judges = ~12-15h. If operator wants tighter, run **just Arm F (20 trials)** and compare against r7.6 Arm B's 8/20. That's the minimum viable comparison. Ablation arms (G, H alone) are scientifically nice but not ship-gating.

**Recommended:** run Arm F (primary ship signal) + Arm G (A1-only ablation, 20 trials, ~30min). Skip Arm H — A2 alone without scaffold is less interesting because scaffold provides the summary discipline A2 needs to trigger cleanly.

### 9.3 Tasks

Same 4 as r7.6: T4 (structured multi-file refactor), T5 (bug-hunt), T6 (long-horizon export), T10 (long-horizon postgres). Skip T9 (tripwire attractor), T3/T7/T1/T2/T8 (one-shot or borderline).

### 9.4 Per-trial flow

Same as r7.6 P1-C: wrapper invocation → parent session → v2 dispatch → child session → fresh Claude sub-agent judge per F.1 rubric.

### 9.5 Judge protocol

**MANDATORY: fresh Claude sub-agent via Agent tool per trial.** Do NOT fall back to orchestrator-self-judge (the r7.5 F.2 / r7.6 P1-C regression). `probe-preflight.sh`'s `agent_dispatch` gate enforces this at pre-flight; if orchestrator sub-agent lacks Agent tool, MAIN SESSION dispatches judges (as I did on 2026-04-20 — works cleanly).

Use judge brief template `ARTIFACT-r7.5-F1-judge-brief.md` between `<<<BEGIN_PROMPT>>>` / `<<<END_PROMPT>>>` with 11 input variables substituted per trial. Per-trial verdict output at `ARTIFACT-r7.7-judge-ArmX-T<N>-run<M>.md`.

### 9.6 Pre-committed ship thresholds (FROZEN)

- **Ship (operator's 75% floor):** Arm F ≥15/20 absolute PASS on non-LOST denominator (if LOST ≤2/20)
- **Alternative narrow ship:** T4-class ≥4/5 AND T5/T6/T10 total ≥11/15 (operator's precedent from r7.5)
- **Meaningful-delta ship-caveat:** Arm F ≥ r7.6 Arm B (8/20) by at least +5 absolute (so ≥13/20) — this would be a HOLD-CLOSE outcome, not a SHIP
- **HOLD:** delta ≤+3 over r7.6 Arm B → Path A didn't substantially help
- **HOLD-with-noise-note:** Arm F = 6-8/20. Arm B=8 has 95% CI ~[4,13] at n=20; this band is indistinguishable from baseline at this sample size. Document as "no measurable effect; indistinguishable at n=20" rather than regression.
- **RETREAT:** Arm F ≤ 5/20 **AND** per-task regression on T4 (scaffold-known-good 4/5+ in r7.6). Both conditions must hold — a single 5/20 with T4=5/5 is likely noise on the harder tasks, not A1+A2 harm.

### 9.7 Expected outcome (honest)

Hard to predict. A1 targets fabrication directly (T10); A2 adds retry-force for missed cases. My gut based on r7.6 data:

- T4 Arm F: **4/4 or 5/5** (scaffold + A1 + A2 all align; no regression expected)
- T5 Arm F: **1-2/5** (scaffold helps some; A1+A2 don't touch the thrash mode)
- T6 Arm F: **3-4/5** (scaffold + A1 helps; A2 catches any fabrication)
- T10 Arm F: **3-5/5** (A1 removes todo-substrate; A2 catches remaining fabrications)

Aggregate projection: **11-16/20**, centered around **13.5/20** (midpoint sum of per-task priors: T4=4.5 + T5=1.5 + T6=3.5 + T10=4.0). Under stated uniform-independent priors, **P(SHIP ≥15/20) ≈ 20-25%** — not negligible. **Below the 15/20 floor in the expected case; above the +5 delta in the expected case.**

If this prediction is right, r7.7 hits HOLD-CLOSE, not SHIP. A further r7.8 would need to address the T5 thrash structurally (maybe: child toolset further restricted, only delegate + clarify until first file read — β-fuse pattern one more level in). **See §18 for the EV argument supporting running Path A even under expected HOLD-CLOSE.**

---

## 10. Authorization + scope (for the fresh session)

### May

- Modify Hermes install files on VM (`~/.hermes/hermes-agent/`) with backup-and-patch pattern (`.probe-r7.7-orig` suffix — coexists with `.probe-d-orig`, `.probe-r7.4-orig`, `.probe-r7.5-orig`, `.probe-r7.6-orig`)
- Create new probe infrastructure at project root (`probe-variantJ-*`)
- Create new artifact files under `variants/hermes/` if needed (though HERMES-variantF.md and HERMES-WORKER.md should suffice — don't proliferate)
- Run MoE probe trials (Gemma-4-26B-A4B-MLX-8bit)
- Dispatch sub-agents aggressively (operator explicitly endorsed "many many agents" for probing)
- Dispatch per-trial fresh Claude Agent sub-agents as judges (ship-gate requirement)

### May NOT

- Dense-model probe trials without explicit operator request (operator deferred dense on 2026-04-19; Gemma-4-31B is their best efficient model but oMLX instability concerns apply)
- Qwen3.5 probes (operator experience: bad at tool calls)
- 122B probes (operator experience: doesn't run efficiently)
- Modify `core/`, `references/`, `playbooks/`, `templates/`, non-Hermes variants
- Modify `SOUL.md`, `USER.md`, `MEMORY.md` without explicit operator approval
- Push to GitHub (including tag-amendment decisions; operator's call)
- Swap canonical HERMES.md on VM without explicit operator ship-authorization
- Touch tripwire files (`SKILL.md`, `jira-briefing.sh`, `useDashboard.ts`)

### Ship hand-back is mandatory

Per operator's 2026-04-19 instruction: "hand back to me for [ship authorization] before modifying production." r7.7 ship decision goes to operator with the judge verdict + recommended next step; operator decides canonical swap, amended release, and any GitHub push.

---

## 11. Risks + mitigations

### R1 — A1 removes `todo` and breaks legitimate planning

Some workers use `todo` for multi-step tracking. Example: a 6-step refactor where each step is tracked. Without `todo`, the worker has to either (a) write a file as a scratchpad, (b) hold state in context, or (c) dispatch sub-workers.

**Mitigation:** A1 gated by env var. Probe BOTH with and without (Arm B vs Arm G). If Arm G shows regression on non-fabrication tasks (e.g., legitimate multi-step T4 trials fail more often), A1 needs scoping (e.g., only restrict `todo` on long-horizon class, not structured).

### R2 — A2 retry loop gets stuck

Child makes claim → A2 fires correction → child re-asserts claim differently → A2 fires again → infinite.

**Mitigation:** hard cap at 2 retries per `HERMES_WBC_MAX_RETRIES`. After that, session closes with `a2_gate_outcome="FABRICATED"` and a final system note. Child cannot keep the session open.

### R3 — A2 false positive on legitimate reflection

Child says: "If I had write access, I would create X.md." A2's regex matches "Created X.md" pattern incorrectly.

**Mitigation:** regex calibrated against r7.6 trials (verbs: created, wrote, generated, saved, written — NOT `would` / `will` / `can`). Tense-sensitive. Tested on honest-blocked trials (01, 02, 05) post-Fix-4 — no FP. Re-test on r7.7 arms against the T4 honest-blocked template — expect zero A2 fires.

### R4 — A2 hook point conflicts with existing SIGTERM/save behavior

B.0 research showed session save is inline in `run_conversation`, not atexit. A2 injects work BEFORE save. If the injection itself fails or takes long, SIGTERM could hit in the gate code → partial corruption. **Python try/except/finally does NOT catch SIGTERM** — signals bypass the exception machinery.

**Mitigation (concrete):**
1. **Install a SIGTERM handler at gate entry** via `signal.signal(signal.SIGTERM, handler)` where the handler saves the current `session.messages` to disk using the pre-existing persist path, then re-raises default SIGTERM. This guarantees in-flight state is flushed before process death.
2. **Hard wall-clock cap on retries:** 60 seconds per retry attempt, 120 seconds cumulative across all retries. Enforced with `signal.alarm` or a dedicated watchdog thread. If the cap trips, the gate force-closes as `a2_gate_outcome="FABRICATED"` and proceeds to normal save — same degraded-gracefully behavior as an exception.
3. **try/except/finally around the gate body** for ordinary Python exceptions (regex failures, missing fields in session JSON). On exception → log, skip gate, proceed to normal save.
4. **Restore the prior SIGTERM handler at gate exit** (in the `finally` block) so the gate's handler doesn't leak into post-save code paths.

Document explicitly: A2 is a best-effort gate with bounded exposure window (≤120s), not a guarantee of closed-session integrity.

### R5 — Probe load accumulates oMLX orphaned sessions again

Operator observed this on 2026-04-19 dense run. Even MoE runs can accumulate.

**Mitigation:** mandatory oMLX restart BEFORE r7.7 probe runs (per §5.2 policy — operator-gated in autonomous mode). Monitor `probe-omlx-health-check.sh` every 5 trials. If DEGRADED, pause + operator-restart + resume.

### R6 — Fresh session picks up with stale context

This handoff is 2026-04-20; fresh session may be days/weeks later. r7.5 pre-release tag unchanged but main working-tree has the HERMES-variantF.md edit uncommitted; VM state could have shifted.

**Mitigation:** §5 pre-flight MUST verify tripwire md5s + stage script statuses + file md5s match expected baselines (§14). If any drift, halt and escalate.

### R7 — Substrate migration (A1 pushes fabrication from `todo` to `terminal`)

§4 notes that two r7.6 Arm B T10 children tried to write into `~/.hermes/hermes-agent/` via `terminal`. With `todo` removed, children looking for a fabrication-capable substrate may pick `terminal` next — raising the near-tripwire-breach rate. A1 doesn't directly prevent this; it just closes one door.

**Mitigation:**
1. **Pre-probe tripwire md5 baseline:** capture md5s of `HERMES.md`, `SKILL.md`, `jira-briefing.sh`, `useDashboard.ts` on VM before Arm F/G runs. (Values already in §14.)
2. **Mid-probe md5 check every 5 trials.** If any tripwire md5 drifts → halt the probe, revert via the §14 canonical-oracle pattern, escalate to operator before resuming.
3. **Post-probe attribution check:** if Arm F shows a rise in `terminal`-based write attempts vs Arm B, document as input to r7.8 scope (child-scope write-path gate).

---

## 12. Known traps + gotchas

- **Tool-surface regression.** Sub-agents dispatched as orchestrators may lack Agent tool. Three sessions hit this in r7.5/r7.6. `probe-preflight.sh` gates. If hit: dispatch judges from main session (like 2026-04-20 did).
- **Secret in archive.** `archive/hermes-probe-r7-2026-04-18/ARTIFACT-workerC-hermes-live.md:87` originally contained the literal oMLX key. Redacted in the pre-release commit. ANY new artifact that documents api_key lines MUST use `<REDACTED>` placeholder. Pre-commit scan: `grep -rn "<the raw key value>" . --exclude-dir=.git --exclude-dir=.claude` — operator knows the value to grep for; do not write it into any tracked artifact.
- **oMLX 6 GB swap is tight on M5 Max.** Use `OMLX_SWAP_MAX_GB=5.5`. Even 5.1 GB tripped the default 5.0 gate on 2026-04-19.
- **Jira cron tripwires.** `SKILL.md` is a Trial 9 mutation attractor on dense runs. SKIP T9 (Jira cron task) in r7.7. Use canonical revert-oracle pattern (`archive/hermes-probe-r7.2-r7.3-2026-04-18/ARTIFACT-revert-r7.2-skill-md.md`) if drift detected.
- **`<channel|>` content pollution is a Gemma+oMLX artifact, not Hermes.** Handled by probe-variantH-check.py's EMPTY_SYNTHESIS detector. Will recur in r7.7 trials. Not actionable in r7.7 scope.
- **Pseudo-tool-call sentinel leak is a real parser issue.** r7.6 Fix 2 patched the Gemma parser (relaxed prefix requirement) and **reduced but did not eliminate** the leak: 3/20 trials in r7.6 P1-C still emitted pseudo-tool-call sentinels in assistant content. Verify the patch still applies correctly on VM at r7.7 session start. **If r7.7 shows >2/20 pseudo-tool-call incidents, dispatch a follow-up F3A′ diag** to extend the parser beyond prefix-relax (possibly content-stripping or a second-pass filter).
- **Out-of-context child deployment (Mode 4).** Child lands in wrong cwd or wrong workspace and searches for files that never existed in its scope. Observed on multiple T5/T6 Arm A and some Arm B trials. Symptoms: repeated `search_files` / `grep` calls returning empty, with the child escalating rather than concluding BLOCKED. Path A does NOT address this directly — T5/T6 recall is capped by task-environment mismatch, not fabrication. If r7.7 shows this pattern persisting at r7.6 rates (~3-5/20), flag for r7.8 scope as a child-orientation fix (e.g., mandatory first-turn `pwd` + env check before any search).
- **Ambiguous-path SCOPE resolution (Mode 5).** When a task prompt references a path that could exist in multiple roots (e.g., `~/.hermes/...` vs `/media/psf/Projects/...`), child guesses wrong and never recovers. Adjacent to Mode 4 but distinct — the file exists, just not where the child looks. Workaround in task design (make prompts unambiguous); not a Path A structural fix. Log occurrences to `ARTIFACT-r7.7-mode5-log.md` for r7.8 planning.
- **variantI wrapper Fix 3 + Fix 4 additions** (retry_preamble, anti-child-attachment, EMPTY_SYNTHESIS case, TIMEOUT=1500) are load-bearing for probe quality. If you derive variantJ from variantI, PRESERVE them.
- **HERMES-variantF.md on main has item #6 (retry classification amplifier)** that the pre-release tag doesn't. If operator authorizes a new tag for this drift, coordinate before r7.7 starts; if NOT, document that r7.7 is running on the main-branch variantF, not the tag's.
- **New LOST failure mode.** REJ-B-T6-run4 had the parent bypass β-fuse entirely (zero v2 calls; used search_files/read_file/mkdir/terminal/todo directly). This is DIFFERENT from one-shot-no-goal. Path A doesn't address it. If this recurs in r7.7, dispatch a separate diag.

---

## 13. Operator decision points (pending)

These need operator sign-off at various points in r7.7:

1. ~~**Run ablation (Arm G + Arm F) or just Arm F?**~~ **RESOLVED 2026-04-20: Arm F + Arm G (full ablation).** Rationale: expected outcome HOLD-CLOSE (~75% probability) means r7.8 is coming regardless; ablation data converts r7.8 scope from guesswork into a mechanical A1-vs-A2 decision. +4-5h marginal cost is positive-EV against the alternative of re-discovering the answer in r7.8.
2. **HERMES-variantF.md drift on main — new tag or release-notes amendment?** r7.6 Fix 4 left this drift. r7.7 will add more.
3. **The 8 IMPL-4 questions.** Still pending since r7.3. Not blocking r7.7 directly but should resolve before any HERMES-variantF canonical swap.
4. **Ship gate flexibility.** Operator's pre-committed 75% floor is absolute. If Arm F lands at 12-14/20, do we hold firm (HOLD → r7.8) or allow narrow ship ("T4-class is 4/5 = 80%, ship for that scope only")?
5. **Ship authorization if Arm F crosses 15/20.** Hand back to operator before any canonical swap, as always.
6. **oMLX restart in autonomous mode** (per §5.2). No verified CLI recipe exists; each long-probe oMLX restart is a mandatory operator-interaction gate. Agent halts + escalates when a pre-probe restart is needed. Operator performs restart via Mac UI and confirms before probing resumes.

---

## 14. Environment + artifact map

### Files under edit (expected in r7.7)

- `~/.hermes/hermes-agent/tools/delegate_tool.py` (if H-A1b/c) OR `toolsets.py` (if H-A1a). Via stage script. `.probe-r7.7-orig` backup.
- `~/.hermes/hermes-agent/agent/run_agent.py` for A2 gate. Same backup pattern.
- `variants/hermes/delegate_worker_v2.py` if A1 implemented there. Deployed to VM via new stage script.
- New `probe-variantJ-stage.sh` (stacks on variantI).
- Possibly new `probe-variantJ-wrapper.sh` or reuse variantI (minimal changes if any).
- New `probe-variantJ-check.py` or reuse variantH (F4A detection helps at judge-time too; A2 is runtime-side).

### Files NOT to modify (frozen from pre-release)

- `variants/hermes/HERMES.md` (canonical)
- `variants/hermes/HERMES-variantB.md`, `-variantD.md`, `-variantE.md`, `-variantF.md` (variantF has the r7.6 Fix 4 drift but don't modify further unless operator authorizes)
- `variants/hermes/delegate_worker.py` (v1, pre-β-fuse)
- `probe-variantE-wrapper.sh`, `-check.py` (pre-release frozen)
- `probe-variantF-*`, `-variantG-*`, `-variantH-*`, `-variantI-*` scripts (pre-release frozen; Fix 3+4 applied in-place is already in main)
  - **variantG role:** r7.5 turn-0 β-fuse toolset restriction — stages with `.probe-r7.5-orig` backup suffix and patches the child's turn-0 available toolset on top of variantF's β-fuse dispatch layer. Load-bearing in the pre-release arm stack (variantF→G→H→I). Stays staged in Arm B re-baseline and in all r7.7 Arms (G, H, F). Do not modify.

### Artifacts to read first (in order)

1. **This file.**
2. `ARTIFACT-r7.6-MORNING-SUMMARY.md` — headline findings + pointer to all overnight artifacts
3. `PLAN-r7.6-P1C-fixes-implementation.md` — operator's rev-2 plan (style precedent + prior-art)
4. `ARTIFACT-r7.4-sigterm-research.md` — Hermes internals map; A2 needs it for hook point
5. `ARTIFACT-r7.5-F1-judge-brief.md` — judge brief template; reuse for r7.7 probing
6. `CALIBRATION-r7.6-judge-protocol.md` — standing calibration protocol (5-sample gate etc.)
7. `ARTIFACT-r7.6-judge-REJ-sample-setup.md` — how the overnight 25-trial re-judgment was structured (template for r7.7 batch-judge dispatches)

### Artifacts to reference as evidence (if needed)

- `variants/hermes/PROBE-RESULTS-r7.md` — full probe history (campaign arc)
- `variants/hermes/DESIGN.md` — architecture (β-fuse explained)
- `variants/hermes/INSTALL.md`, `DEPENDENCIES.md` — install + tested versions
- `RELEASE-NOTES-r7.5-hermes-prerelease.md` — pre-release notes
- `ARTIFACT-r7.6-judge-REJ-fresh-verdict-*.md` — 25 fresh-LLM verdicts from 2026-04-20 re-judgment
- `ARTIFACT-r7.6-judge-fresh-verdict-{1,2,3,4,5}.md`, `-C2-*`, `-C3-*` — earlier fresh verdicts
- `ARTIFACT-r7.6-P1C-fix{2,3,4,5}-{impl,judge}.md` — r7.6 rev-2 fix execution artifacts

### Expected file md5s (verify at session start)

```
probe-preflight.sh                                = 65b88ec02c1a1b07c88dc195f765331f
CALIBRATION-r7.6-judge-protocol.md                = 2ddd2eac5fa26b9f7a1465fb3046503d
variants/hermes/delegate_worker_v2.py             = d31876fe987331a26c8640202334fd46
variants/hermes/HERMES-variantF.md                = 24e8d1c0f7e1e0e95b26c38af974b8ce   (post-Fix-4; note drift from pre-release tag 01c0e77b...)
variants/hermes/HERMES-WORKER.md                  = f866f52bbee28335964ec50d06bbac68
probe-variantH-check.py                           = 873935f65e1bb91942dde1139dd57f92
probe-variantI-wrapper.sh                         = f1022e994a46838c180e4bf8da4171ee
probe-variantH-wrapper.sh                         = 64b75e00efc1056dcb1883a54e162033
/tmp/probe-r7.6-P1C-logs/judge-trial.py           = 709ef98a... (post-Fix-2)
```

### VM expected md5s (canonical state)

```
HERMES.md               = 0780c232a6cb52e13e432261f0d68ad9
SKILL.md                = fb1a5a5208a6cf2fcb8252aac10397eb
jira-briefing.sh        = a1dce6e989527686124d0860830627c9
useDashboard.ts         = 5503ee1c2ef7d635a020eea275e41239
```

### Hermes version on VM (authoritative)

`v2026.4.8` / git tag `v2026.4.8` / commit `86960cdb chore: release v0.8.0 (2026.4.8) (#6135)`

Python 3.11.15 in Hermes venv.

---

## 15. Success criteria for r7.7

### Plan-level

1. A1 + A2 implemented and staged via `probe-variantJ-stage.sh` with `.probe-r7.7-orig` backups.
2. A1 judge ACCEPT: child toolset verifiably excludes `todo` under env flag.
3. A2 judge ACCEPT: runtime gate fires correctly on fabricated-claim synthetic + 1 live integration smoke test.
4. Arm F probe matrix runs cleanly (20 MoE trials, per-trial fresh Claude sub-agent judges, calibration per `CALIBRATION-r7.6-judge-protocol.md`).
5. VM canonical at end. Pre-release tag untouched. No tripwire drift.
6. Ship judge issues SHIP / HOLD-close / HOLD / RETREAT per pre-committed thresholds.
7. Morning-style summary artifact produced for operator review.

### Per-fix rollback criterion

- A1: restore `variants/hermes/delegate_worker_v2.py` from git (or `.probe-r7.5-orig`); unstage via variantJ-stage.sh.
- A2: remove the gate function call from `run_agent.py`; restore from `.probe-r7.7-orig`.
- Everything reversible via session-JSON oracle if needed (see `ARTIFACT-revert-r7.2-skill-md.md` precedent).

---

## 16. Estimated timeline (parallelized where possible)

| Phase | Sequential | Parallel |
|-------|------------|----------|
| S0 pre-flight + reading | 45m | 45m |
| S1 A1 diag | 45m | 45m (parallel with S2) |
| S2 A2 hook research | 45m | 45m (parallel with S1) |
| S3 A1 impl | 1h | 1h (parallel with S4) |
| S4 A2 impl | 2h | 2h (parallel with S3) |
| S5 A1 judge | 30m | 30m (parallel with S6) |
| S6 A2 judge | 45m | 45m (parallel with S5) |
| S7 smoke test | 45m | 45m |
| S8 probe matrix (Arm F, 20 trials) | **5-7h** MoE trials (incl. oMLX restarts every ~5 trials per r7.5/r7.6 wall-clock; orphaned-session accumulation) + 1h judges | **5-7h** (judges parallelize with trials' tail) |
| S8b Arm G ablation (optional, +20 trials) | **+3-4h** | **+3-4h** |
| S9 ship judge | 45m | 45m |
| S10 operator hand-back | operator time | operator time |
| S11 summary writeup | 45m | 45m |

**Sequential estimate:** ~14-17h (without ablation), ~17-21h (with ablation).
**Parallelized estimate:** ~11-14h (without ablation), ~14-17h (with ablation).

This reconciles with §9.2's "~12-15h" framing — that figure was for both arms × 20 trials × 80 total trials+judges; under the Arm-F-only recommendation (§9.2) it falls in the lower band of this table. Primary source of the upward revision: oMLX orphaned-session accumulation forces ~1-2 restart cycles per 20 trials, each adding 10-15min wall-clock.

If running overnight like 2026-04-19: feasible in a single session **without ablation**. With ablation, expect 2 sessions (pause after S8 Arm F, resume at S8b Arm G).

---

## 17. Starting checklist for the fresh agent

```
☐ Read this file end-to-end.
☐ Read ARTIFACT-r7.6-MORNING-SUMMARY.md.
☐ Confirm operator has exported OMLX_API_KEY; do not proceed without it.
☐ Verify agent-dispatch by trivial Agent sub-agent probe (do NOT hand-set AGENT_DISPATCH_AVAILABLE).
☐ Verify `ssh ubuntu-vm -- true` (§5.1).
☐ Run probe-preflight.sh with OMLX_SWAP_MAX_GB=5.5.
☐ Verify file md5s per §14 (use `md5 -q` on macOS).
☐ Verify VM canonical state via ssh.
☐ Check with operator: answer the 6 pending decision points in §13 (includes oMLX restart gate).
☐ Dispatch S1 + S2 workers in parallel (read-only research).
☐ Dispatch S3 + S4 workers in parallel (implementation, after S1/S2 return).
☐ Continue through the sequencing matrix in §8, honoring §8.5 judge-rejection protocol if S5/S6 REJECT.
☐ Update PROGRESS.md after each S-step.
☐ Write a morning-style summary for operator at session end.
```

---

## 18. Why run this even if HOLD-CLOSE is the expected outcome

§9.7 predicts ~13.5/20 centered, with P(SHIP) ≈ 20-25%. §15 frames r7.7 around a ship decision. Fair question: if the expected case is not SHIP, is 13-17h of Path A work worth it? Three positive-EV arguments:

- **(1) Arm G ablation separates A1 lift from A2 lift.** The r7.6 data cannot disentangle "what does removing `todo` buy" from "what does runtime correction buy." Arm G (A1-only) answers the A1 question directly. Whichever fix carries the lift drives r7.8 scope; whichever doesn't is deprioritized. This disambiguation is worth the probe cost on its own — even if the combined Arm F lands at HOLD-CLOSE.
- **(2) Formal HOLD-CLOSE evidence is the justification for r7.8 deeper structural restriction.** Operator's pre-committed 75% floor needs empirical pushback before any further structural work gets authorized. A noisy Arm F at 13/20 with signed fresh-LLM judges is the evidentiary base for proposing "r7.8: child toolset restricted to {delegate, clarify, read_file} until first write attempt" — a β-fuse-style pattern one level deeper. Without this data, r7.8 is a guess, not a grounded scope.
- **(3) `a2_gate_outcome` field is reusable infra for future campaigns.** A2's session-JSON verdict field outlives r7.7. Any future campaign investigating fabrication, tool-use discipline, or worker quality can read it directly — no need to re-run A2 research. The infrastructure compounds even if the r7.7 ship verdict is HOLD.

**EV summary:** P(SHIP) ≈ 25% × (ship benefit) + P(HOLD-CLOSE) ≈ 50% × (campaign-load-bearing negative) + P(HOLD/RETREAT) ≈ 25% × (weak scope-shaping signal). Positive-EV at 13-17h of scoped work.

---

*End of handoff. Resume from §17 starting checklist. VM is canonical at handoff time; pre-release tag is immutable; operator will authorize the ship decision at S10 based on r7.7 data.*

*Good luck.*
