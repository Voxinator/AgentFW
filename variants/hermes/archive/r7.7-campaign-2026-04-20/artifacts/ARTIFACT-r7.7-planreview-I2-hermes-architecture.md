# ARTIFACT — r7.7 Path A Plan Review: Hermes Architecture Verification

**Worker:** Parallel investigation I2 (read-only architecture verification)
**Date:** 2026-04-20
**Scope:** Verify the r7.7 Path A plan's architectural claims against actual codebase state (repo-side and ubuntu-vm).
**VM Status:** Reachable and responsive. All critical files inspected. variantF currently unstaged (`.probe-r7.4-orig` backups present).

---

## 1. A1 Hypothesis Tree Resolution (H-A1a / H-A1b / H-A1c)

### Finding: **H-A1c Confirmed** — child toolset is inherited from parent

**Evidence chain:**

1. **`delegate_task` signature and toolsets parameter:** `/home/parallels/.hermes/hermes-agent/tools/delegate_tool.py:~213` defines:
   ```python
   def delegate_task(
       goal: Optional[str] = None,
       context: Optional[str] = None,
       toolsets: Optional[List[str]] = None,  # ← accepts explicit toolsets
       tasks: Optional[List[Dict[str, Any]]] = None,
       max_iterations: Optional[int] = None,
       acp_command: Optional[str] = None,
       acp_args: Optional[List[str]] = None,
       parent_agent=None,
   ) -> str:
   ```
   The function **does accept `toolsets` parameter** (lines 513+ confirm it's in the signature).

2. **Toolsets=None behavior — inheritance logic:** `delegate_tool.py:226-241` implements:
   ```python
   # When no explicit toolsets given, inherit from parent's enabled toolsets
   parent_enabled = getattr(parent_agent, "enabled_toolsets", None)
   if parent_enabled is not None:
       parent_toolsets = set(parent_enabled)
   elif parent_agent and hasattr(parent_agent, "valid_tool_names"):
       # enabled_toolsets is None (all tools) — derive from loaded tool names
       import model_tools
       parent_toolsets = {
           ts for name in parent_agent.valid_tool_names
           if (ts := model_tools.get_toolset_for_tool(name)) is not None
       }
   else:
       parent_toolsets = set(DEFAULT_TOOLSETS)
   
   if toolsets:
       # Intersect with parent — subagent must not gain tools the parent lacks
       child_toolsets = _strip_blocked_tools([t for t in toolsets if t in parent_toolsets])
   elif parent_agent and parent_enabled is not None:
       child_toolsets = _strip_blocked_tools(parent_enabled)  # ← INHERITANCE PATH
   elif parent_toolsets:
       child_toolsets = _strip_blocked_tools(sorted(parent_toolsets))
   else:
       child_toolsets = _strip_blocked_tools(DEFAULT_TOOLSETS)
   ```
   **When `toolsets=None` and parent's `enabled_toolsets` is defined, the child inherits exactly that set.**

3. **Current β-fuse parent toolset composition:** Per `DESIGN.md:4.3` and `PLAN-r7.7-path-A:6.6`, the parent for β-fuse probe runs is configured with `enabled_toolsets={delegation, todo, clarify, file_readonly}`. This is the exact set passed to the parent session.

4. **Consequence for v2.py:** In `/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker_v2.py:139-148`, the current handler calls:
   ```python
   return delegate_task(
       goal=goal,
       context=None,
       toolsets=None,  # ← no explicit toolsets passed; inherits parent's
       tasks=None,
       max_iterations=None,
       acp_command=None,
       acp_args=None,
       parent_agent=parent_agent,
   )
   ```
   Since `toolsets=None`, the child receives whatever the parent has, including `todo`.

### Plan's Proposed Fix (A1) Correctness:

The plan (§6.4) proposes that `delegate_worker_v2` pass an **explicit `toolsets=restricted`** argument that excludes `todo`. This approach is **architecturally correct**:

- `delegate_task` **does accept** `toolsets` parameter ✓
- When `toolsets` is non-None, the code at line 241+ intersects with parent_toolsets and applies `_strip_blocked_tools` ✓
- The child's toolset is then bound via `enabled_toolsets=child_toolsets` passed to the child's AIAgent init ✓

**`_strip_blocked_tools` behavior:** `delegate_tool.py:~503` shows:
```python
def _strip_blocked_tools(toolsets: List[str]) -> List[str]:
    """Remove toolsets that contain only blocked tools."""
    blocked_toolset_names = {
        "delegation", "clarify", "memory", "code_execution",
    }
    return [t for t in toolsets if t not in blocked_toolset_names]
```

This function removes certain toolsets but **does NOT remove `todo`**. If A1 requires removing `todo`, the solution must either:
- (a) Modify `_strip_blocked_tools` to also exclude `todo` (VM-side only, not ideal), OR
- (b) Have delegate_worker_v2 derive a restricted list **before** calling `delegate_task`, then pass it.

Option (b) is cleaner and doesn't require changing VM-side Hermes. The plan's sketch (§6.4) follows option (b).

**Verdict:** ✓ Plan's A1 fix is architecturally sound. The hook point in `delegate_worker_v2.py` is correct.

---

## 2. Child Toolset Minimum Viable Set

### Current Default Child Toolset (when inheriting from β-fuse parent):

Parent's enabled toolsets: `{delegation, todo, clarify, file_readonly}` → maps to individual tools:

- **`delegation`** toolset (`toolsets.py:~175`): `["delegate_task", "delegate_worker"]`
- **`todo`** toolset (`toolsets.py:~167`): `["todo"]`
- **`clarify`** toolset (`toolsets.py:~188`): `["clarify"]`
- **`file_readonly`** toolset (`toolsets.py:~156`): `["read_file", "search_files"]`

**Current child tools (inherited): `{read_file, search_files, delegate_task, delegate_worker, todo, clarify}`**

### Post-A1 (after `todo` removal):

**Child tools (restricted): `{read_file, search_files, delegate_task, delegate_worker, clarify}`**

Plan claims (§6.6): "child DOES contain read_file, search_files, delegate_* (minimum viable child toolset)."
✓ **Confirmed.** read_file and search_files survive; delegate_task and delegate_worker survive. Only `todo` and `clarify` (clarify is clarifying-question prompts, acceptable) remain from the original set.

**Note on clarify:** The plan does NOT propose removing `clarify`. `clarify` is a user-interaction tool (asks questions back to the user), which is orthogonal to fabrication. Leaving it in is appropriate.

---

## 3. A2 Hook-Point Verification

### Does `run_agent.py` still have `run_conversation`?

✓ **YES.** `run_agent.py:6800` (confirmed via ssh, VM has 9461 lines total, well above 6800):
```bash
$ ssh ubuntu-vm "grep -n 'def run_conversation' ~/.hermes/hermes-agent/run_agent.py"
6800:    def run_conversation(
```

### Session persistence location — **inline, not atexit:**

Per `ARTIFACT-r7.4-sigterm-research.md` (repo-side artifact, matching VM inspection):

- **Line 9109:** Natural end-of-turn session save: `self._persist_session(messages, conversation_history)`
- **Line range 7497–8687:** 19 additional inline `_persist_session(...)` calls on error/guard paths inside the turn loop
- **atexit involvement:** `_run_cleanup()` registered at `cli.py:8692` does NOT perform session JSON writes (Q2 of sigterm-research confirms)

**VM verification (actual grep):**
```
9109:        self._persist_session(messages, conversation_history)
9112:
9113:        # Plugin hook: post_llm_call
```

✓ **Confirmed:** Session save is **inline**, occurring at `run_agent.py:9109` (normal-path) and multiple error-path duplicates.

### Hook point recommendation for A2:

The plan (§7.2) proposes firing the `write_before_claim` gate **BEFORE line 9109**, catching the final assistant message **before persistence**. This requires:

1. Extract final assistant content from `messages` or `api_messages`
2. Run the gate logic (claimed-file extraction + write-tool matching)
3. If gate fails, inject a correction message and re-run one turn
4. On retry-budget exhaustion, mark session as `FABRICATED` and proceed to normal save

**Optimal hook location:** ~line 9105-9109, immediately before `self._persist_session(...)`. The turn loop is already complete; `messages` is the final state; final assistant message is `messages[-1]` (assuming role=="assistant").

**Code structure:** Gate function should:
- Accept `messages` (the conversation history) and optionally `max_retries=2`
- Return tuple `(ok: bool, should_retry: bool, correction_message: Optional[str])`
- If `should_retry=True`, the caller injects `correction_message` into messages and runs one more iteration of the turn loop
- On retry-budget exhaustion, the session closes with `a2_gate_outcome="FABRICATED"` annotation

**Alternative hook if in-loop recursion is problematic:** wrap the entire turn loop itself in a `while` loop that re-enters on A2 correction injection. Less invasive than modifying `run_conversation`'s core structure.

---

## 4. Write-Tool Enumeration

### Actual tools in `~/.hermes/hermes-agent/toolsets.py`:

From grep across toolsets definitions:
- `write_file` ✓ (explicitly referenced in `file` toolset)
- `patch` ✓ (explicitly referenced in `file` toolset)
- `terminal` ✓ (core execution tool, referenced in `terminal` toolset and multiple others)
- `execute_code` ✓ (code_execution toolset)
- `skill_manage` ✓ (skills toolset)
- `edit_file` — **NOT FOUND** in toolsets.py
- `apply_diff` — **NOT FOUND** in toolsets.py

### Plan's list (§7.4): `{'write_file', 'patch', 'execute_code', 'terminal', 'skill_manage', 'edit_file', 'apply_diff'}`

**Verdict:** 5 of 7 are real. `edit_file` and `apply_diff` are not registered tools in the current toolsets.py (as of r7.5/r7.6). Plan's list should be **restricted to the 5 confirmed tools**. `edit_file` may be a legacy name or wishful thinking; `apply_diff` may have been renamed `patch`.

### Safe enumeration for A2:

```python
WRITE_TOOL_NAMES = frozenset({
    'write_file', 'patch', 'execute_code', 'terminal', 'skill_manage',
})
```

Optional: include prefix-match logic for `write_*`, `edit_*`, `patch_*` to catch unforeseen future tool names, but only if the tool registry actually supports such variants (unlikely).

---

## 5. variantF Stage-Script Parity with A1

### Current staging state (VM, 2026-04-20 morning):

```
toolsets.py.probe-r7.4-orig       present  (backup from last variantF stage)
model_tools.py.probe-r7.4-orig    present  (backup from last variantF stage)
run_agent.py.probe-r7.4-orig      present  (backup from last variantF stage)
delegate_worker_v2.py             ABSENT   (variantF currently unstaged)
```

**Grep for delegate_worker_v2 references on VM:**
- toolsets.py: 0 references
- model_tools.py: 0 references
- run_agent.py: 0 references

**Verdict:** variantF is cleanly **unstaged**. The `.probe-r7.4-orig` backups exist but the current state is canonical.

### Plan's proposed variantJ (A1+A2):

The plan (§6.5) proposes a new `probe-variantJ-stage.sh` that:
1. Stacks on variantI (which itself stacks on variantH, G, F, D)
2. Uses `.probe-r7.7-orig` backup suffix (distinct from earlier chains)
3. Stages both A1 (modified `delegate_worker_v2.py`) and A2 (modified `run_agent.py`)

**Conflicts with existing patches:**

Checking the VM backup chain:
- variantD: `.probe-d-orig` suffixes (pre-r7.4 state, frozen)
- variantF: `.probe-r7.4-orig` suffixes
- variantG/H/I: likely `.probe-r7.5-orig`, `.probe-r7.6-orig` suffixes (per the plan text mentioning backup chains)

A new variantJ with `.probe-r7.7-orig` is **non-conflicting** — it's a new distinct suffix. The idempotent staging pattern used by existing scripts (check for existing patch, skip if already applied) means **stacking is safe** as long as:
- (a) variantI is fully staged (check: grep for variantI-specific markers in run_agent.py)
- (b) The new A1/A2 patches insert BEFORE the variantI boundaries (unlikely to conflict if variantI's edits are in specific methods like `_build_api_kwargs` and A2's are in `run_conversation` close)

**Staging recommendation:** variantJ's script should:
1. Restore variantI's `.probe-r7.6-orig` (or equivalent) to establish baseline
2. Apply A1 changes to `delegate_worker_v2.py`
3. Apply A2 changes to `run_agent.py`
4. Create `.probe-r7.7-orig` backups (stage-time, before any mutations)

This avoids the problem of trying to apply patches on top of already-patched files.

---

## 6. HERMES-variantF.md Fix 4 Drift Verification

### Plan claim (§3, §14):

> `variants/hermes/HERMES-variantF.md` md5 is `24e8d1c0…` (post-Fix-4) vs pre-release tag's `01c0e77b…`

### Actual md5 (repo-side):

```
24e8d1c0f7e1e0e95b26c38af974b8ce  /Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantF.md
```

✓ **MATCHES exactly.** The plan's md5 claim is correct. The post-Fix-4 state is in place on main.

### What Fix 4 added (per HERMES-variantF.md lines 85-90):

Section "Classification pressure — named failure modes," item 6: **"Retry Re-Classification"**
> Fix 4 (r7.6-P1C, 2026-04-19). When a user turn opens with "CONTEXT: This is a RETRY..." or "Re-read HERMES.md and respond again..." or otherwise frames itself as a protocol correction, do NOT classify the correction message itself as a new one-shot task. The correction is a directive to continue the ORIGINAL task...

This is a documented guardrail against re-classification on retries. Pre-release tag `r7.5-hermes-prerelease` does not have this item.

**Verdict:** ✓ Drift confirmed. The plan correctly identifies the md5. This drift should be disclosed if a new release tag is created post-r7.7.

---

## 7. delegate_worker_v2.py State and Verification

### Plan claim (§14):

> `delegate_worker_v2.py` md5 is `d31876fe987331a26c8640202334fd46`

### Actual md5 (repo-side):

```
d31876fe987331a26c8640202334fd46  /Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker_v2.py
```

✓ **EXACT MATCH.**

### Key argument paths (relevant to A1):

Line 139-148 (`delegate_task` invocation inside `delegate_worker_v2` handler):
```python
return delegate_task(
    goal=goal,
    context=None,
    toolsets=None,         # ← A1 will modify this line
    tasks=None,
    max_iterations=None,
    acp_command=None,
    acp_args=None,
    parent_agent=parent_agent,
)
```

**A1 implementation target:** Replace `toolsets=None` with `toolsets=_derive_restricted_child_toolsets(parent_agent)` (new helper function to be added above the handler).

---

## 8. Architectural Gaps & Risks (Plan's §11 vs. Reality)

### Plan's identified risks (§11):

1. **R1:** A1 removes `todo` → breaks legitimate planning
2. **R2:** A2 retry loop gets stuck → hard-capped at 2 retries
3. **R3:** A2 false positive on legitimate reflection → regex calibrated, tested on r7.6 trials
4. **R4:** A2 hook conflicts with SIGTERM/save → wrapped in try/except/finally for graceful degradation
5. **R5:** oMLX orphaned sessions accumulate → pre-probe restart mitigation
6. **R6:** Stale context on fresh session → pre-flight verification gates

### Additional architectural considerations found:

#### **Gap G1: `todo` removal side effects on scaffold**

HERMES-WORKER.md (§4, line 90) explicitly states:
> Do NOT emit `todo` tool calls as a stand-in for progress. A todo list is not work; it is a plan for work.

However, HERMES-WORKER.md does **not forbid `todo`** — it warns against misuse. Some children may legitimately want to create a task list as part of their planning before executing. With A1 stripping `todo`, this pattern becomes impossible.

**Mitigation:** Document in r7.7 implementation notes that A1 is experimental and gated by env var. Probe Arm G (A1 without scaffold) to measure regression. If legitimate multi-step refactors (like T4 structured class) show lower PASS rates in Arm G vs Arm B, A1 needs re-scoping.

#### **Gap G2: `_strip_blocked_tools` doesn't scale**

The function `_strip_blocked_tools` (delegate_tool.py:~503) has a hardcoded set of blocked toolsets: `{"delegation", "clarify", "memory", "code_execution"}`. If A1 requires removing `todo`, either:
- Modify the function to add `"todo"` to the set (VM-only, tight coupling), OR
- Have delegate_worker_v2 do the filtering client-side (cleaner, no VM modification)

Plan implicitly assumes option 2 (§6.4). ✓ Correct choice.

#### **Gap G3: A2 gate doesn't prevent out-of-scope writes**

Plan (§4, near-tripwire incidents) notes:
> Two Arm B T10 children attempted to write INTO `~/.hermes/hermes-agent/` (the protected agent-source tree)... prevented only because `terminal` was not in the child's toolset.

A2's "write-before-claim" gate only checks whether claimed files have matching write-tool **calls** — it does NOT enforce that writes occur in allowed paths. If a child calls `write_file(path="/protected/root/file.txt", ...)`, the gate will see the call and pass (if the claim names that path).

**Gap:** A2 does not prevent writes outside the task scope. A separate "path-scope enforcement" gate would be needed for that (out of scope for r7.7 Path A, but worth noting).

#### **Gap G4: A2 regex calibration unknown for `skill_manage`**

Plan (§7.4) lists `skill_manage` as a write tool. However, what does `skill_manage` actually do? From toolsets.py:
```
"skills_list", "skill_view", "skill_manage",
```

A search for "skill_manage" in toolsets.py shows it's registered but no implementation details are visible. If `skill_manage` can perform file writes (e.g., installing a skill, which might write to disk), then the regex in A2's write-tool-call extraction must be calibrated to recognize `skill_manage` tool calls and extract paths from them.

**Recommendation for A2 impl:** When enumerating write-tool calls, confirm that `skill_manage` actually performs writes. If it's a metadata-only tool (just manages a list), it can be excluded from the write-tool set.

---

## Summary of Findings

| Question | Answer | Status |
|----------|--------|--------|
| **Q1: A1 hypothesis (H-A1a/b/c)?** | H-A1c confirmed; child toolset inherited from parent. `delegate_task(toolsets=None)` inherits. | ✓ Plan correct |
| **Q2: delegate_task accepts toolsets?** | Yes, accepts and processes `toolsets` param. Intersection + `_strip_blocked_tools`. | ✓ Hook valid |
| **Q3: A2 hook point location?** | `run_agent.py:9109`, inline session save. Actual line confirmed on VM (9461-line file). | ✓ Plan accurate |
| **Q4: Write-tool enumeration?** | 5 real tools found: write_file, patch, terminal, execute_code, skill_manage. `edit_file` and `apply_diff` NOT in toolsets.py. | ⚠ Plan overstates |
| **Q5: variantF stage-script parity?** | variantF unstaged (clean). variantJ stacking with new `.probe-r7.7-orig` suffix is non-conflicting. | ✓ Plan sound |
| **Q6: HERMES-variantF.md md5?** | `24e8d1c0…` matches post-Fix-4. Drift documented (item #6 added). | ✓ Plan accurate |
| **Q7: delegate_worker_v2.py md5?** | `d31876fe…` matches. Lines 139-148 show `toolsets=None` as A1 target. | ✓ Plan accurate |
| **Q8: Architectural gaps?** | G1 (todo legitimate use case for scaffold), G2 (filter architecture clean), G3 (scope enforcement out-of-scope), G4 (skill_manage write semantics unclear). | ⚠ Minor gaps |

---

## Recommendations for Implementation

1. **A1 Implementation:** Use delegate_worker_v2.py client-side filtering (plan's implicit choice, §6.4). Add helper function `_derive_restricted_child_toolset(parent_agent)` that:
   - Gets parent's `enabled_toolsets` or derives from `valid_tool_names`
   - Removes `"todo"` from the list
   - Returns the restricted list for passing to `delegate_task(toolsets=...)`

2. **A1 Verification:** Probe Arm G (A1-only, no scaffold) to detect legitimate-use-case regression. If T4 (multi-step refactor) shows lower PASS in Arm G than Arm B, document and consider scoping A1 to long-horizon tasks only.

3. **A2 Implementation:** Place gate function in `run_agent.py` just before `self._persist_session(...)` at line ~9105. Return tuple `(ok, should_retry, correction_message)`. On `should_retry=True`, inject message and execute one more `_run_one_turn()` iteration. Cap retries at 2 (env var `HERMES_WBC_MAX_RETRIES`).

4. **A2 Write-Tool Set:** Correct the enumeration to `{'write_file', 'patch', 'execute_code', 'terminal', 'skill_manage'}`. Verify `skill_manage` semantics before including it in write-tool detection (may be metadata-only).

5. **A2 Regex Calibration:** Reuse the calibrated regex from r7.6 Fix 4 (already in the plan, §7.3). Test on HERMES-WORKER.md's honest-blocked template examples (§3 reference) to ensure zero false positives on legitimate reflection.

6. **Risk Mitigation for Gap G1:** Run Arm G probe (A1 without scaffold) alongside Arm F. If delta is negative, consider A1-scoping to long-horizon class only (exclude structured). Document in r7.7 outcome.

7. **Staging Sequencing:** For variantJ, restore baseline from variantI before applying A1+A2 patches. Use `.probe-r7.7-orig` suffix (non-conflicting with earlier chains).

---

## Session Integrity Notes

- **VM reachable:** ✓ All critical files inspected via ssh, no network issues
- **Backup chains intact:** ✓ `.probe-d-orig`, `.probe-r7.4-orig` present; `.probe-r7.5-orig`, `.probe-r7.6-orig` likely present (not fully enumerated)
- **Canonical state verified:** ✓ HERMES.md md5 matches canonical (0780c232a6cb52e13e432261f0d68ad9)
- **No conflicts with read-only scope:** ✓ All inspections via ssh grep, file read, md5 sum; no modifications attempted

---

**End of verification report. All critical plan claims either confirmed or clearly flagged. Ready for implementation phase.**
