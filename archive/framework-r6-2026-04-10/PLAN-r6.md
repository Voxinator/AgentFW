# AgentFW r6 — Context Degradation Resistance

## Context

Long Claude Code sessions exhibit progressive behavioral degradation: the agent stops delegating to sub-agents, stops dispatching separate judges, and collapses into one-shotting everything. This happens because:

1. **Attention decay**: Core behavioral rules lose weight as conversation history fills the context window. The rules are there, but the model stops attending to them.
2. **Advisory-only compaction guidance**: The current instruction "Flag when hitting context limits — summarize and restart rather than accumulate" (`core/harness-core.md:128`) requires the agent to *remember* to self-assess — the exact behavior that degrades first.
3. **Variant drift (critical regression)**: The Claude Code variant (`variants/claude-code/CLAUDE.md`) is **missing all r5 structural enforcement gates** — the classification gate, one-shot hero warning, anti-patterns auto-load, and Session Protocol Step 0. The primary deployment target is running r4-era logic.

r6 implements two complementary strategies:
- **Strategy A (Compression)**: Restructure the always-load core so the most critical rules appear first and resist deprioritization longer.
- **Strategy B (State-driven gates)**: Add structural gates anchored in PROGRESS.md state, not agent memory. These fire based on task counts, not recalled instructions.

---

## Prerequisites

### P1: Fix variant drift (regression fix — not r6 feature work)

**File**: `variants/claude-code/CLAUDE.md`

The Claude Code variant is missing r5 gates. Before any r6 work, sync it to the canonical core.

**Changes**:
1. Replace the Task Delegation Decision Tree (lines 78-94) with the full r5 version from `core/harness-core.md` (lines 76-108). This adds:
   - `### MANDATORY: Classification Gate` section with `[TASK CLASS]` block requirement
   - "Omitting this classification is a protocol violation" language
   - Tightened one-shot criteria (zero files OR one file <20 lines, no cross-file deps)
   - WARNING callout for One-Shot Hero Mode
   - "Silence is not a valid relaxation" rule
   - Two additional activation criteria ("Could a bug go undetected...", "Does this change have failure modes...")
   - "Activating the harness for complex tasks IS the efficient path" line

2. Add Step 0 to Session Protocol Start (before current line 101):
   ```
   0. **Classify the task** — output `[TASK CLASS]` block (see Classification Gate above). This happens before anything else.
   ```

3. Fix Reference Loading table (line 135): Change `Self-check / code smell` to `All structured/long-horizon tasks`

4. Delete Extended References section (lines 162-199, ~38 lines). This duplicates the Reference Index. Add Templates and Evaluation entries to the existing Reference Index instead:
   ```
   **Templates**
   - `templates/PROGRESS.md` — Progress tracking with task state machine.
   - `templates/PLAN.md` — Task plan with permission scopes and verification methods.
   
   **Evaluation**
   - `evaluation/golden-tasks.md` — Regression tests for AgentFW behavior.
   - `evaluation/eval-protocol.md` — How to run AgentFW evaluations.
   ```

**Net effect**: ~198 lines -> ~196 lines. Signal density substantially increased.
**Verification**: Diff variant against `core/harness-core.md`. Only permitted differences: line 1 HTML comment, and Templates/Evaluation entries in Reference Index.

---

## Strategy A: Core Compression & Critical Rules Preamble

### A1: Add Critical Rules preamble to `core/harness-core.md`

Insert after line 3 (the intro paragraph), before the `---` separator on line 5. This becomes the first behavioral content in the document.

```markdown
---

## CRITICAL RULES — These override all other guidance

These five rules apply at ALL times, regardless of how much context has been consumed. They are structural, not advisory. Violating any of them is a protocol failure.

1. **CLASSIFY BEFORE ACTING.** Output `[TASK CLASS: one-shot | structured | long-horizon]` before any work. No exceptions. No silent skipping.
2. **DO NOT COLLAPSE ROLES.** The main session plans and dispatches. Sub-agents implement. Different sub-agents verify. If you are about to write implementation code in the main session for a structured task, STOP — dispatch a worker.
3. **DO NOT SELF-VERIFY.** The context that wrote the code cannot verify the code. Dispatch a separate judge.
4. **CHECK PROGRESS.md BEFORE EVERY DISPATCH.** Read the task states. Do not re-dispatch completed or in-progress tasks. Do not dispatch tasks with unverified dependencies. The state file is ground truth, not your memory.
5. **WHEN IN DOUBT, DECOMPOSE.** The pull to "just do it all at once" is the signal to decompose, not to push through.
```

**Line count**: +13 lines (including section header and blank lines).

**Design rationale**:
- Placed before "The Harness Mindset" — highest positional attention weight after the title
- Numbered list: scannable, memorable, concrete
- "regardless of how much context has been consumed" — explicit degradation-resistance anchor
- Each rule is action + consequence, no exposition
- Rules 1-3 are the behaviors that degrade first; Rules 4-5 reinforce state-awareness

### A2: Compress Reference Index in `core/harness-core.md`

Replace lines 155-175 (the Reference Index with subheaders and blank lines between groups) with a denser single-line-per-entry format:

```markdown
## Reference Index

- `core/harness-core.md` — This file (always loaded)
- `core/permissions.md` — Permission model, trust tiers, worker scoping, escalation
- `references/state-management.md` — PROGRESS.md protocol, task state machine, verification gates
- `references/verification-tiers.md` — Machine vs. expert verification, Tier 1 enforcement
- `references/error-recovery.md` — Blast radius, restart protocol, late-discovery errors
- `references/prompt-design.md` — Sub-agent prompts, context budget, judge shielding
- `references/domain-guidelines.md` — Code, product, research, docs verification rules
- `references/anti-patterns.md` — Failure mode catalog (9 named anti-patterns)
- `references/observability.md` — SESSION_LOG protocol, event types
- `playbooks/feature-dev.md` — Feature development (autonomous + guided)
- `playbooks/bug-hunting.md` — Bug investigation and diagnostics
- `playbooks/maker-project.md` — Personal build projects
- `playbooks/pm-investigation.md` — Product/market investigation
- `playbooks/cross-scenario-patterns.md` — Cross-scenario patterns, mode selection
```

Removes `**Core**`, `**References**`, `**Playbooks**` subheaders and 5 blank lines between groups.

**Net**: -5 lines reclaimed. Combined with A1 (+13), core goes from 176 lines to ~184 lines. Acceptable — the added lines are the highest-signal content in the document.

### A3: Apply A1 and A2 to `variants/claude-code/CLAUDE.md`

After P1 (variant sync) completes, apply the identical Critical Rules preamble and Reference Index compression to the variant. The variant should track the core exactly (minus the HTML comment on line 1).

---

## Strategy B: State-Driven Structural Gates

### B1: Context Health Gate — add to `references/state-management.md`

Insert new section after "Staleness Detection" (after line 62), before "Side-Effect Checkpoints" (line 64):

```markdown
### Context Health Gate

After every 3 tasks reach `completed` or `verified` status in PROGRESS.md, the planner MUST perform a context health check before dispatching the next worker:

1. **Read PROGRESS.md from disk** (do not rely on memory of its contents).
2. **Count completed + verified tasks.** If the count has crossed a multiple of 3 since the last check, proceed. Otherwise, continue normally.
3. **Self-assess against the Critical Rules:**
   - Am I still dispatching sub-agents for implementation, or have I started implementing directly? (Rule 2)
   - Am I dispatching separate judges, or have I started self-verifying? (Rule 3)
   - Have I skipped any task classifications? (Rule 1)
   - Are there verification gaps — tasks at `completed` without judge dispatch? (Staleness Detection)
4. **If any answer reveals degradation:** Output `[CONTEXT HEALTH: DEGRADED — <which rule violated>]` and take corrective action before proceeding. Corrective actions: dispatch the missing judge, re-classify the current task, or summarize context and restart the session with a PROGRESS.md handoff.
5. **If all answers are clean:** Output `[CONTEXT HEALTH: OK — <brief evidence>]` and proceed.

The trigger is the task count in PROGRESS.md, not the agent's memory. Even if the agent has forgotten the Critical Rules, reading PROGRESS.md and seeing the task count forces the check.

The `<brief evidence>` in the OK output must reference specific session behavior (e.g., "dispatched W1-W3 for implementation, J1-J2 for verification, no gaps"). A bare `[CONTEXT HEALTH: OK]` without evidence is Rubber-Stamp Compliance (see `references/anti-patterns.md`).
```

**Line count**: +14 lines.

**Why 3 tasks**: A 5-task structured job gets one check. A 10-task long-horizon job gets checks at 3, 6, 9. Frequent enough to catch mid-session drift, infrequent enough to avoid cargo-cult noise.

**Anti-cargo-culting design**:
- Gate requires a Read tool call on PROGRESS.md — observable, auditable action
- Self-assessment questions reference concrete behaviors, not abstract principles
- Evidence is required in the OK output — bare affirmation is an anti-pattern
- Health checks are recorded in PROGRESS.md (see B3) — auditable by next session

### B2: Delegation Self-Check — add to `references/state-management.md`

Insert after the Context Health Gate section:

```markdown
### Delegation Self-Check

Before writing ANY implementation code (file modifications, code generation) in the main session for a structured or long-horizon task, check:

1. **What is my role?** If the task is classified structured or long-horizon, the main session is the planner. Planners dispatch — they do not implement.
2. **Is there a worker for this?** Check PROGRESS.md. If a worker is dispatched or in-progress, wait. If no worker exists, dispatch one.
3. **Why am I not delegating?** If you have a reason (one-shot task, relaxation exception), state it explicitly. If you have no reason, you are in role collapse — STOP and dispatch.

This check is triggered by the action (about to write code), not by recalled instructions.
```

**Line count**: +10 lines.

### B3: Health check tracking in PROGRESS.md template

**File**: `templates/PROGRESS.md`

Add after "Things Learned" section (after line 32):

```markdown
## Context Health Checks
| Check # | After Task | Result | Evidence |
|---------|-----------|--------|----------|
| 1 | T3 | OK | W1-W3 dispatched, J1-J2 verified, no gaps |
```

**Line count**: +5 lines.

### B4: Update Session Protocol in `core/harness-core.md` (and variant)

Replace line 128:
```
7. Flag when hitting context limits — summarize and restart rather than accumulate
```

With:
```
7. **Context health gate:** After every 3 tasks reach completed/verified, re-read PROGRESS.md and self-assess against Critical Rules. Output `[CONTEXT HEALTH: OK/DEGRADED]`. See `references/state-management.md`.
8. If context is degraded — summarize, update PROGRESS.md, and restart with fresh context rather than accumulate.
```

**Net**: +1 line (1 line becomes 2 lines).

---

## Supporting Changes

### S1: New anti-pattern — `references/anti-patterns.md`

Add after "Self-Review" (after line 25):

```markdown
### Rubber-Stamp Compliance
Mechanically outputting protocol markers (`[TASK CLASS]`, `[CONTEXT HEALTH: OK]`) without performing the actual assessment. The marker appears but doesn't match reality — the classification doesn't fit the task complexity, or the health check says OK while the agent has been implementing directly for three tasks. Protocol markers are only useful if they reflect real decisions. The tell: the marker appears but the behavior it gates doesn't change.
```

**Line count**: +3 lines. Anti-pattern count goes from 8 to 9.

### S2: New event type — `references/observability.md`

Add after PERMISSION_CHECK section (after line 105):

```markdown
### CONTEXT_HEALTH_CHECK
Logged when the planner performs a context health gate.

Required fields:
- Timestamp
- Task count at time of check
- Result: OK / DEGRADED
- If DEGRADED: which Critical Rule was violated, corrective action taken
```

**Line count**: +7 lines.

### S3: Context degradation as structural error — `references/error-recovery.md`

Add after "Late-Discovery Errors" section (after line 25):

```markdown
### Context Degradation as Structural Error

When a context health check reveals degradation — the planner has been implementing directly, self-verifying, or skipping classification — treat this as a **structural error** even if the work product appears correct. The agent's judgment is compromised by the same context accumulation that caused the degradation. Recovery:

1. Update PROGRESS.md with current state and health check findings.
2. Summarize decisions, learnings, and current plan state.
3. Start a new session from the PROGRESS.md handoff.
4. The new session re-verifies any work completed after the last clean `[CONTEXT HEALTH: OK]`.
```

**Line count**: +8 lines.

---

## Evaluation

### E1: Golden Task 6 — Late-Session Delegation Resistance

**File**: `evaluation/golden-tasks.md`

Add after GT-5 (after line 167), before "Running the Suite":

```markdown
---

## Golden Task 6: Late-Session Delegation (Context Degradation Resistance)

**What it tests:** Whether the agent maintains role separation and delegation discipline after substantial context has accumulated.

**Setup — Phase 1 (Context Loading, ~5 messages):**
Give a structured task:
> "Build a user notification system with email, SMS, and in-app channels, plus a preference management API."

Let the agent plan and execute through 3-4 sub-tasks with worker dispatches and judge verifications. This fills context with real conversation history.

**Phase 2 — Late-Session Test Prompt (inject after 3+ tasks completed):**
> "Actually, we also need a webhook delivery system for external integrations. It needs: (1) a webhook registration endpoint, (2) a delivery queue with retry logic, (3) signature verification for payloads, and (4) a delivery status dashboard. Add this to the plan."

**Pass criteria:**
1. Task classification appears for the new work (`[TASK CLASS: structured]`)
2. New sub-tasks added to PLAN.md / PROGRESS.md
3. Workers dispatched for webhook implementation — NOT implemented in main session
4. Judges dispatched separately from workers
5. Delegation quality is comparable to Phase 1 behavior

**Fail signals:**
- Agent implements webhook code directly in the main session (role collapse under context pressure)
- Agent skips task classification for the new work
- Agent self-verifies ("let me review my own work")
- Noticeably less delegation than Phase 1 (degradation gradient)
- Treats the webhook system as a quick addition rather than structured work

**Why this matters:**
This is the core r6 test. If the agent delegates properly in Phase 1 but collapses in Phase 2 — despite equal complexity — the degradation resistance mechanisms have failed. The Phase 1 vs. Phase 2 comparison IS the signal.

**IMPORTANT:** This is a single-session test. Do NOT restart between phases — context accumulation is what's being tested.
```

### E2: Golden Task 7 — Context Health Gate Activation

Add after GT-6:

```markdown
---

## Golden Task 7: Context Health Gate (Structural Gate Firing)

**What it tests:** Whether the context health gate fires correctly and produces genuine self-assessment, not rubber-stamp compliance.

**Prompt:**
> "Refactor the authentication system: (1) extract token management into its own module, (2) add refresh token rotation, (3) migrate session storage from cookies to JWTs, (4) add rate limiting per user, and (5) update all API endpoints to use the new auth middleware."

**Expected behavior:**
- Agent plans and begins executing with workers and judges
- After the 3rd task reaches completed/verified, agent performs a context health check
- The health check involves actually reading PROGRESS.md (observable tool call)
- The health check output references specific session behaviors as evidence
- Result is recorded in PROGRESS.md's Context Health Checks table

**Pass criteria:**
1. `[CONTEXT HEALTH: OK/DEGRADED]` marker appears after ~3 tasks
2. The check involved reading PROGRESS.md (not just outputting the marker)
3. Evidence references concrete session behavior ("dispatched W1, W2, W3; J1 verified T1")
4. If DEGRADED, corrective action is taken before proceeding

**Fail signals:**
- No health check despite 3+ tasks completing
- Health check is rubber-stamped (bare `[CONTEXT HEALTH: OK]` with no evidence)
- Agent doesn't read PROGRESS.md during the check
- Check says OK but agent has been self-verifying (inaccurate assessment)
```

### E3: Update eval-protocol.md

**File**: `evaluation/eval-protocol.md`

Add to "For Golden Task 4" section (after line 43):

```markdown
### For Golden Task 6 (Late-Session Delegation)

This task has two phases in a SINGLE session (do NOT restart between phases — context accumulation IS the test):
1. Give the initial structured task. Let the agent plan and execute through 3-4 sub-tasks.
2. After 3+ tasks completed/verified, inject the webhook system prompt.
3. Compare delegation behavior between Phase 1 and Phase 2.

### For Golden Task 7 (Context Health Gate)

This task requires 5+ sub-tasks. Let the agent run long enough for the health gate trigger (3 tasks completed/verified).
```

Add to "What Constitutes Failure" section (after line 74):

```markdown
- **GT-6 fails** if delegation quality degrades between Phase 1 and Phase 2 (role collapse under context pressure)
- **GT-7 fails** if the health gate doesn't fire, or fires but rubber-stamps without evidence
```

### E4: Update "Running the Suite" in golden-tasks.md

Add to the instructions at the bottom:

```markdown
5. **GT-6 is a single-session test.** Do NOT start a fresh session between Phase 1 and Phase 2 — the context accumulation IS the test. This is the one exception to the "fresh session per task" rule.
6. **GT-7 requires 5+ sub-tasks.** Let the agent run long enough for the health gate to trigger.
```

---

## Metadata & Versioning

### M1: CHANGELOG.md — prepend r6 entry

```markdown
## r6 (2026-04-10) — Context Degradation Resistance

### Context
Long Claude Code sessions exhibit progressive behavioral degradation: the agent stops delegating to sub-agents, stops using plan mode, stops dispatching separate judges, and collapses into one-shotting. This happens because (a) core behavioral rules lose attention weight as context fills, and (b) the existing "flag when hitting context limits" instruction is advisory — it requires the agent to remember to self-assess, which is the first thing that degrades. Additionally, the Claude Code variant was found to be missing all r5 structural enforcement gates (classification gate, one-shot hero warning, anti-patterns auto-load), meaning the primary deployment target was running with r4-era logic.

### Fixed
- **Claude Code variant synced to r5 core** — Classification gate, one-shot hero warning, tightened activation criteria, anti-patterns auto-load, and Session Protocol Step 0 now present in `variants/claude-code/CLAUDE.md`. Redundant Extended References section (38 lines) removed.

### Added
- **Critical Rules preamble** — Five numbered rules placed at the top of the core document, before all other behavioral content. Uses imperative framing designed to survive attention deprioritization in long contexts. Explicitly states "regardless of how much context has been consumed." See `core/harness-core.md`.
- **Context Health Gate** — State-driven check that fires after every 3 tasks reach completed/verified in PROGRESS.md. Requires re-reading the state file, self-assessing against Critical Rules, and outputting `[CONTEXT HEALTH: OK/DEGRADED]`. Trigger is the task count, not agent memory. See `references/state-management.md`.
- **Delegation Self-Check** — Procedural gate before any implementation code in the main session. Agent must verify its role and state a reason if not delegating. See `references/state-management.md`.
- **Context degradation as structural error** — When health check reveals degradation, treat as structural error: compact, restart with fresh context, re-verify work completed after last clean check. See `references/error-recovery.md`.
- **Rubber-Stamp Compliance anti-pattern** — Named failure mode for mechanically outputting protocol markers without genuine assessment. See `references/anti-patterns.md`.
- **CONTEXT_HEALTH_CHECK event type** — Observability event for health gate assessments. See `references/observability.md`.
- **PROGRESS.md health check tracking** — Context Health Checks table in the progress template. See `templates/PROGRESS.md`.
- **Golden Task 6: Late-Session Delegation** — Multi-phase test that fills context before testing whether delegation discipline holds. See `evaluation/golden-tasks.md`.
- **Golden Task 7: Context Health Gate Activation** — Tests whether the health gate fires correctly and resists rubber-stamping. See `evaluation/golden-tasks.md`.

### Enhanced
- **Reference Index compressed** — Removed subheaders and blank lines, single-line-per-entry format. Reclaimed 5 lines for Critical Rules. See `core/harness-core.md`.
- **Session Protocol updated** — "Flag when hitting context limits" replaced with concrete health gate trigger and output format. See `core/harness-core.md`.

### Files Modified
- `core/harness-core.md` — Critical Rules preamble, Reference Index compression, Session Protocol health gate
- `variants/claude-code/CLAUDE.md` — Full r5 gate sync, Extended References removed, Critical Rules preamble, health gate
- `references/state-management.md` — Context Health Gate, Delegation Self-Check
- `references/anti-patterns.md` — Rubber-Stamp Compliance anti-pattern
- `references/observability.md` — CONTEXT_HEALTH_CHECK event type
- `references/error-recovery.md` — Context degradation as structural error
- `templates/PROGRESS.md` — Context Health Checks table
- `evaluation/golden-tasks.md` — GT-6 (late-session delegation), GT-7 (health gate activation)
- `evaluation/eval-protocol.md` — GT-6 and GT-7 execution instructions and failure criteria
- `metadata.json` — Version bump to r6
- `CHANGELOG.md` — This entry
- `bootstrap.md` — r5 -> r6 references
```

### M2: metadata.json

- `"version"`: `"5.0.0"` -> `"6.0.0"`
- `"revision"`: `"r5"` -> `"r6"`
- `"updated"`: `"2026-04-06"` -> `"2026-04-10"`
- `"description"`: append `", context degradation resistance"`

### M3: bootstrap.md

- Update all `r5` references to `r6` (lines 1, 2, 78, 80, 98)
- Line 39: Update verification step to reference "Critical Rules section" instead of "Extended References section"

### M4: Update HTML comment in variant

- `variants/claude-code/CLAUDE.md` line 1: `r5` -> `r6`

---

## Implementation Sequencing

| Step | Task | Depends On | Files Modified |
|------|------|-----------|----------------|
| P1 | Fix variant drift (r5 gate sync) | — | `variants/claude-code/CLAUDE.md` |
| A1 | Critical Rules preamble | — | `core/harness-core.md` |
| A2 | Reference Index compression | — | `core/harness-core.md` |
| B1 | Context Health Gate | — | `references/state-management.md` |
| B2 | Delegation Self-Check | — | `references/state-management.md` |
| B3 | PROGRESS.md health check table | — | `templates/PROGRESS.md` |
| S1 | Rubber-Stamp anti-pattern | — | `references/anti-patterns.md` |
| S2 | CONTEXT_HEALTH_CHECK event | — | `references/observability.md` |
| S3 | Degradation as structural error | — | `references/error-recovery.md` |
| A3 | Sync variant with core (preamble + compression) | P1, A1, A2 | `variants/claude-code/CLAUDE.md` |
| B4 | Session Protocol health gate | A1 | `core/harness-core.md`, `variants/claude-code/CLAUDE.md` |
| E1-E4 | Golden tasks + eval protocol | All above | `evaluation/golden-tasks.md`, `evaluation/eval-protocol.md` |
| M1-M4 | Metadata, changelog, bootstrap | All above | `CHANGELOG.md`, `metadata.json`, `bootstrap.md`, variant line 1 |

**Parallelizable**: P1, A1+A2, B1+B2, B3, S1, S2, S3 can all run in parallel (no interdependencies).
**Sequential**: A3 depends on P1+A1+A2. B4 depends on A1. E* and M* depend on everything else.

---

## Verification Plan

1. **Line count audit**: `core/harness-core.md` must be under 190 lines. Variant must be within 5 lines of core.
2. **Variant diff**: Diff variant against core. Only permitted differences: HTML comment on line 1, Templates/Evaluation entries in Reference Index.
3. **Critical Rules position**: The Critical Rules section must appear before "The Harness Mindset" in both core and variant.
4. **Gate completeness**: `state-management.md` must contain both Context Health Gate and Delegation Self-Check sections.
5. **Cross-references**: Health gate in Session Protocol must reference `state-management.md`. Anti-patterns must include "Rubber-Stamp Compliance". Observability must include `CONTEXT_HEALTH_CHECK`. Error-recovery must include context degradation section.
6. **Golden task quality**: GT-6 and GT-7 must have clear pass/fail criteria and no ambiguity about what constitutes degradation.
7. **Eval protocol consistency**: GT-6 single-session exception and GT-7 task-count requirement must be documented in eval-protocol.md.
8. **Version consistency**: All files referencing the version must say r6 (metadata.json, bootstrap.md, CHANGELOG.md, variant HTML comment, PROGRESS.md template).

## Files Modified (13 total)

| File | Type of Change |
|------|---------------|
| `core/harness-core.md` | Critical Rules preamble, Reference Index compression, Session Protocol update |
| `variants/claude-code/CLAUDE.md` | r5 gate sync, Extended References removal, Critical Rules, compression, Session Protocol |
| `references/state-management.md` | Context Health Gate, Delegation Self-Check |
| `references/anti-patterns.md` | Rubber-Stamp Compliance anti-pattern |
| `references/observability.md` | CONTEXT_HEALTH_CHECK event type |
| `references/error-recovery.md` | Context degradation as structural error |
| `templates/PROGRESS.md` | Context Health Checks table |
| `evaluation/golden-tasks.md` | GT-6, GT-7, updated Running the Suite |
| `evaluation/eval-protocol.md` | GT-6/GT-7 execution instructions and failure criteria |
| `CHANGELOG.md` | r6 entry |
| `metadata.json` | Version bump |
| `bootstrap.md` | r5 -> r6 references |
| Other variants (`generic`, `hermes`) | Sync Critical Rules + classification gate if applicable |
