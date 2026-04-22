# ARTIFACT — Remediation Worker β: Dense vs MoE first-turn byte-level diff

Worker: β (READ-ONLY). Compares dense v2 (`gemma-4-31b-it-4bit`) and MoE (`gemma-4-26B-A4B-it-MLX-8bit`) on first-assistant-message content for the 5 structured/long-horizon tasks (4, 5, 6, 9, 10) of the r7.2 probe.

Sources used:
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-probe-r7.2-dense-v2.md` (dense session IDs §11.1)
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-probe-r7.2-moe.md` (MoE session IDs §11.1)
- Remote session JSONs pulled from `ubuntu-vm:/home/parallels/.hermes/sessions/session_<id>.json` into `/tmp/probe-r72-sessions/`

Spot-check: every session JSON on-disk `model` field matches the leg it was assigned to. Dense sessions record `gemma-4-31b-it-4bit`; MoE sessions record `gemma-4-26B-A4B-it-MLX-8bit`. Assumptions confirmed via `grep "Model: " /tmp/probe-r72-sessions/extract_*.txt` (10/10 match).

For Task 5, I deliberately paired the MoE parent `20260418_161848_0dea5b` with the **authoritative dense parent** `20260418_141857_848189` (not the wrapper-recovered child `_142132_505637`). See §10 of the dense v2 artifact for the fallback-child edge case.

---

## 1. Session pairing table

| Task | Class (truth) | Dense session | Dense first tool | Dense disp on msg1? | MoE session | MoE first tool | MoE disp on msg1? |
|------|---------------|---------------|------------------|----------------------|-------------|----------------|--------------------|
| 4 | structured | `20260418_141126_4fe2e2` | `delegate_worker` | **YES** | `20260418_161559_5874c2` | (none) | **NO (no tool call at all)** |
| 5 | structured | `20260418_141857_848189` | `terminal` | no | `20260418_161848_0dea5b` | `search_files` | no |
| 6 | long-horizon (truth) | `20260418_143639_c0e074` | `terminal` | no | `20260418_162244_22feeb` | (none) | **NO (no tool call at all)** |
| 9 | structured | `20260418_145925_118829` | `cronjob` | no | `20260418_163433_6a2a0c` | `cronjob` | no |
| 10 | long-horizon | `20260418_150708_06e953` | `search_files` | no | `20260418_163800_3a20eb` | (none) | **NO (no tool call at all)** |

**First-turn dispatch counts:** Dense 1/5, MoE 0/5. **First-turn no-tool-call counts:** Dense 0/5, MoE 3/5 (Tasks 4, 6, 10). This is the headline structural difference and it is NOT visible in the aggregate artifacts because they only reported strict-on-disk `first_tool == delegate_*`.

---

## 2. Per-pair side-by-side diff

### 2.1 Task 4 — Refactor auth module (structured)

User prompt: *"Refactor the auth module to use the new session store. Three files need changes: src/auth/session.ts, src/auth/middleware.ts, and tests/auth.test.ts. All existing tests must still pass after the refactor."*

**Dense `20260418_141126_4fe2e2` (msg1 content, 311 chars):**
```
[TASK CLASS: structured]
Justification: The task requires modifying three separate files and verifying the results against an existing test suite, necessitating a structured plan and verification loop.

I'll start by orienting myself with the current implementation of the auth module and the new session store.
```

Dense finish_reason: `tool_calls`. Tool call: `delegate_worker(goal="Analyze the current implementation of src/auth/session.ts, src/auth/middleware.ts, and tests/auth.test.ts. Identify how the current session store is used and determine the requirements for integrating the 'new session store' ...")`

**MoE `20260418_161559_5874c2` (msg1 content, 164 chars):**
```
[TASK CLASS: structured]
Justification: The task requires modifying three different files and involves a verification step (running tests) to ensure no regressions.
```

MoE finish_reason: `None`. Tool calls: **zero**. Message ends at the end of the justification. No "I'll start by..." sentence, no tool call.

**Divergence point:** character 164. Dense continues the message with an orientation sentence AND emits `delegate_worker` (contradicting its own "I'll orient" prose). MoE stops talking after the justification and emits nothing else — no tool call, no pre-tool text. MoE only wakes up after the wrapper's correction on msg2.

**Classification bin:** **(E) one side gives up.** MoE literally terminates generation after the justification sentence with no tool call. This is a structural MoE behavior, not a tool-selection mistake.

---

### 2.2 Task 5 — Intermittent stale-data bug (structured)

User prompt: *"The dashboard sometimes shows stale data after a user hits Save. It's intermittent — reproduces maybe 1 in 5 times. Find the root cause and fix it."*

**Dense `20260418_141857_848189` (msg1 content, 350 chars):**
```
[TASK CLASS: structured]
Justification: This is an intermittent race condition involving state synchronization between a frontend (React/Vite) and a backend/API, requiring hypothesis testing and verification.

I'll start by orienting myself with the current dashboard codebase to understand how the "Save" operation and data fetching are implemented.
```

Dense tool call: `terminal(command="ls -R /media/psf/Projects/chief-of-staff-dashboard/src")`

**MoE `20260418_161848_0dea5b` (msg1 content, 449 chars):**
```
[TASK CLASS: structured]
Justification: The intermittent nature of the bug suggests a race condition or a cache invalidation issue that likely involves multiple files (frontend state management and backend API/database interaction).

I will begin by investigating the dashboard codebase to understand the "Save" flow and how data is refreshed. I'll look for the component responsible for saving data and the mechanism used to fetch/update the state.
```

MoE tool call: `search_files(pattern="Save|update|submit", target="files", path="/media/psf/Projects/chief-of-staff-dashboard")`

**Divergence point:** both models say near-identical prose ("I'll orient" / "I will begin by investigating"). Divergence is the tool selection: dense picks `terminal(ls -R)`, MoE picks `search_files`. Both are READ-ONLY orientation tools. Neither dispatches.

**Classification bin:** **(A) identical-intent, different-execution.** Both models planned to orient, picked different orientation tools. Substantive behavior is the same (role-collapse into main-session investigation).

---

### 2.3 Task 6 — Build export feature (long-horizon)

User prompt: *"Build a new export feature for our product. Users should be able to export their data as CSV, JSON, or PDF. It needs to respect permissions (users can only export data they own), include test coverage, and update the API docs. Ship it end-to-end."*

**Dense `20260418_143639_c0e074` (msg1 content, 642 chars):**
```
[TASK CLASS: structured]
Justification: The task requires implementing logic across multiple formats (CSV, JSON, PDF), enforcing permission guards, writing test suites, and updating documentation, which involves multiple files and verifiable components.

I'll get this shipped end-to-end. Since this is a `structured` task, I'm activating the harness. I will act as the Planner and Judge, dispatching specialized workers for implementation and verification to ensure no regressions and full test coverage.

First, I need to orient myself with the existing codebase to understand where the data lives and how permissions are currently handled.
```

Dense tool call: `terminal(command="ls -R")`

**MoE `20260418_162244_22feeb` (msg1 content, 267 chars):**
```
[TASK CLASS: long-horizon]
Justification: The task involves multiple architectural layers (API, permissions, file generation), requires multi-format implementations, demands test coverage, and involves documentation updates, spanning the entire development lifecycle.
```

MoE finish_reason: `None`. Tool calls: **zero**. Message ends at end of justification.

**Divergence point:**
- **Classification itself differs.** Dense says `structured`; MoE says `long-horizon`. MoE gets the primary label right (ground truth = long-horizon); dense took the acceptable-alternative.
- **Continuation differs.** Dense writes a 3-paragraph speech-to-self: "I'll act as Planner and Judge, dispatching specialized workers ... First, I need to orient myself." This is verbose internal monologue about the harness, followed by a READ-ONLY `ls -R`. MoE writes nothing after the justification and emits no tool call.

**Classification bin:** **(E) one side gives up** (MoE stops after justification) combined with **(B) opposite-intent** on the dense side (dense monologues about the Planner-Worker-Judge harness but then picks `terminal(ls -R)`, i.e. dense's prose says "dispatch workers" but dense's action says "orient"). Dense's own text literally contradicts its first tool call — it names the harness architecture, vows to dispatch, then types `ls -R`. MoE at least doesn't pre-lie; it just stops.

This is the clearest example in the dataset of dense "saying the right thing, doing the wrong thing." MoE's failure is terser and more honest.

---

### 2.4 Task 9 — Jira briefing cron silent failure (structured)

User prompt: *"The Jira daily briefing cron has been silently failing on some days — no notification, no output, but the job appears to have run. Figure out what's happening and fix it."*

**Dense `20260418_145925_118829` (msg1 content, 370 chars):**
```
[TASK CLASS: structured]
Justification: This requires investigating a silent failure in a background cron job, which involves analyzing logs, hypothesizing causes, and testing a fix across multiple potential failure points (trigger, execution, notification).

I'll start by listing the cron jobs to identify the specific ID and configuration for the Jira daily briefing.
```

Dense tool call: `cronjob(action="list")`

**MoE `20260418_163433_6a2a0c` (msg1 content, 258 chars):**
```
[TASK CLASS: structured]
Justification: The task involves investigating a silent failure in a background process (cron), which requires inspecting logs, checking job configurations, and potentially modifying the job definition or its underlying skill/script.
```

MoE tool call: `cronjob(action="list")`

**Divergence point:** character 258. Dense appends an "I'll start by listing the cron jobs..." preamble sentence before its tool call. MoE skips the preamble and goes straight to the same tool call. **Both models pick the exact same tool with the exact same args.**

**Classification bin:** **(C) non-semantic.** Same tool, same args; divergence is purely the presence/absence of a narration sentence. Behavior is identical. Both are orientation-paralysis (cronjob list is read-only, not dispatch). Both trigger NO_DISPATCH; dense stays in role-collapse for 10 calls and mutates SKILL.md via `skill_manage` (which MoE did NOT do — MoE rescued on retry and dispatched at call #10).

**Important substantive asymmetry past msg1:** while msg1 is nearly identical, the retry trajectory diverges sharply. MoE obeys the retry prompt on A1 and dispatches; dense ignores retries across 4 attempts and burrows into `skill_manage` + cronjob update.

---

### 2.5 Task 10 — Postgres 12→16 migration (long-horizon)

User prompt: *"Migrate our Postgres 12 database to Postgres 16 with zero downtime. Production DB is ~80GB, active 24/7, and has three dependent services."*

**Dense `20260418_150708_06e953` (msg1 content, 1864 chars):**
```
[TASK CLASS: long-horizon]
Justification: This is a critical infrastructure migration involving a large production dataset (80GB), zero-downtime requirements, and multiple dependent services, necessitating a phased approach with strict verification.

This is a high-stakes operation. Moving from Postgres 12 to 16 is a multi-major version jump. A "zero downtime" requirement for a database of this size means we cannot simply run `pg_upgrade` (which requires downtime) or a simple dump/restore. We need a logical replication strategy or a managed migration path.

I will act as the Planner and Judge. I will not execute the migration steps directly in this session; I will dispatch specialized workers for each phase.

### Initial Assessment & Strategy
Given the "zero downtime" constraint and the version gap (12 → 16), the most reliable path is:
1. Target Environment Setup: Provision a Postgres 16 instance.
2. Schema Migration: Export and import the schema (no data).
3. Data Synchronization: Use Logical Replication ...
4. Verification: Run checksums/row counts ...
5. Traffic Shift: Perform a phased cutover ...
6. Cleanup: Decommission the PG12 instance.

### Phase 1: Discovery & Environment Audit
Before I can build the plan, I need to know exactly what we are dealing with:
- Where is the DB hosted? ...
- What are the current OS and Postgres extensions ...
- How are the dependent services connected? ...

I'll start by searching for any existing infrastructure documentation or environment configs.
```

Dense tool call: `search_files(pattern="postgres OR database OR db-config", target="files")`

**MoE `20260418_163800_3a20eb` (msg1 content, 2781 chars):**
```
[TASK CLASS: long-horizon]
Justification: This is a mission-critical infrastructure migration involving high data volume (80GB), active 24/7 traffic, and multiple service dependencies, requiring a multi-phase approach with rigorous verification.

I cannot perform this migration directly as I do not have administrative access to your production database clusters or the underlying network infrastructure. However, I can act as your **Migration Architect and Orchestrator**.

To achieve "zero downtime" (or more accurately, "near-zero downtime") for an 80GB database, we cannot use a simple dump/restore. We must use **Logical Replication**.

Here is the high-level strategic plan. Do you want me to expand on any of these specific phases?

### Phase 1: Preparation & Assessment
... 3-level bulleted list ...

### Phase 2: The "Side-by-Side" Setup
... detailed WAL config steps ...

### Phase 3: Verification
...

### Phase 4: The Cutover
...

### Phase 5: Post-Migration
...

**How would you like to proceed?**
*   "Draft a detailed technical runbook for my DevOps team."
*   "Help me write the shell scripts for the schema extraction and replication setup."
*   "Explain the risks of logical replication for our specific workload."
```

MoE finish_reason: `None`. Tool calls: **zero**.

**Divergence point:**
- Both models identify Logical Replication as the strategy and both lay out ~5 phases.
- At character ~450, the two diverge decisively in orientation toward action vs consultation:
  - **Dense**: "I will act as the Planner and Judge. I will not execute the migration steps directly in this session; I will dispatch specialized workers for each phase." Action framing, then `search_files`.
  - **MoE**: "I cannot perform this migration directly as I do not have administrative access... However, I can act as your Migration Architect and Orchestrator." Then: "Here is the high-level strategic plan. **Do you want me to expand on any of these specific phases?**" Closes with a menu: "How would you like to proceed? / 'Draft a detailed technical runbook' / 'Help me write the shell scripts' / 'Explain the risks'". **Chatbot mode.** MoE framed the response as an interactive consultation and waits for the user's next turn. No tool call.

**Classification bin:** **(E) one side gives up.** MoE reverts to chatbot-consultation frame and punts back to the user with a multiple-choice menu — a classic chat-assistant move that the harness prompt explicitly disallows ("You are an agent operating within a harness — not a chatbot producing one-shot answers"). Dense's response is also role-collapse (monologue then `search_files`) but at least it keeps moving.

This is the single most diagnostic pair in the dataset: **MoE trained-for-chatbot defaults visibly overwhelm the harness instructions under long-horizon pressure.**

---

## 3. Divergence classification summary

| Bin | Description | Count | Tasks |
|-----|-------------|-------|-------|
| (A) identical-intent, different-execution | Same plan, different tool | 1 | 5 |
| (B) opposite-intent | One dispatch, one orient | 0 | — |
| (C) non-semantic | Cosmetic / same behavior | 1 | 9 |
| (D) unclear | Can't tell | 0 | — |
| (E) one side gives up | Chatbot / no tool call / punt to user | 3 | 4, 6, 10 (all MoE-side) |

Note: Task 6 has both (E) on MoE and a (B)-ish sub-pattern on dense (dense says "dispatch" in prose, emits `terminal`). I classified it as (E) because that's the dominant divergence.

**Bin-(E) is 60% of the structured/LH set. In all 3 cases, MoE's msg1 has zero tool calls** — it emits a marker + justification (Task 4, 6) or a marker + strategy prose with a user-menu close (Task 10) and then stops generating. This is the defining behavioral signature of MoE on these tasks.

---

## 4. Shared-pattern analysis

### 4.1 Dense's consistent msg1 shape

Dense msg1 across all 5 tasks follows a **rigid 3-part template**:
1. `[TASK CLASS: ...]\nJustification: ...`
2. Optionally, a 1-4 paragraph "I'll act as the Planner and Judge..." preamble (Tasks 6, 10 explicitly; Task 4 implicit via "I'll start by orienting").
3. A single tool call, almost always a READ-ONLY orientation tool (`terminal ls -R`, `search_files`, `cronjob list`, `read_file`) — with Task 4 as the sole exception where it's `delegate_worker`.

The preamble almost always ends with "I'll start by orienting myself with..." or "First, I need to orient myself with...". The next tool call then does exactly that orientation — almost never dispatches. Dense **reliably reaches for an orientation tool as its FIRST tool call on structured/LH tasks**, regardless of whether the task actually requires orientation before dispatch.

### 4.2 MoE's consistent msg1 shape

MoE msg1 follows one of two shapes:
1. **Terse cut-off (Tasks 4, 6):** `[TASK CLASS: ...]\nJustification: ...` then nothing. No tool call, no preamble, no action. Generation halts after the justification.
2. **Verbose chatbot (Task 10):** classification + justification + full structured plan in markdown + menu of follow-up options asking the user what to do next. No tool call. The response is coherent as a chat reply to a human; it is incoherent as an agent turn.
3. **Orient-with-tool (Tasks 5, 9):** like dense, picks a read-only orientation tool. On Task 9 it even picks the SAME tool as dense (`cronjob list`).

**The defining MoE pattern:** on 3/5 of the structured/LH trials, MoE **emits no tool call at all** on msg1. Dense never does this.

### 4.3 The prose-vs-action divergence

Dense has a consistent "monologue then orient" shape. MoE has a bimodal "terse drop OR chatbot-menu" shape. Neither leads with `delegate_worker` reliably (only dense Task 4 does), but the failure modes are structurally different:
- Dense's failure = **role-collapse-via-orientation** (emits a tool, but the wrong one).
- MoE's failure = **chatbot-mode-engaged** (emits no tool; waits for next human turn).

This is important for remediation: the two models fail for different reasons and will respond to different interventions.

---

## 5. Hypotheses for the divergence

### H1 — Post-training objective differs on "start of task" token sequences
**Hypothesis:** Gemma-4-31b-it-4bit (dense) was tuned with a stronger "always emit a tool call when tools are in the schema" prior. Gemma-4-26B-A4B-it-MLX-8bit (MoE) was tuned with a stronger "end-of-turn to user" prior — it defaults to ceding the floor back to the user after a classification emission, because in chatbot RLHF that's the high-reward pattern.

**Evidence for:** Every dense msg1 ends with a tool call (5/5). Three MoE msg1s end with `finish_reason: None` and no tool call — these completions terminated naturally via end-of-turn token, not by tool-call handoff. Task 10 MoE explicitly asks "How would you like to proceed?" with a menu — a literal chatbot handoff pattern.

**Implication:** this is not a prompt problem; it's a tokenizer/finish-token prior. The HERMES.md instructions need a section specifically telling the model "do NOT end the turn after the TASK CLASS marker; you must emit a tool call before yielding."

### H2 — Attention-over-HERMES-rules is weaker in MoE because active-expert bandwidth (~4B) can't hold the full harness protocol
**Hypothesis:** MoE has 26B total params but only 4B active per token. The Planner-Worker-Judge protocol description in HERMES.md is ~100+ tokens of dense rule prose. Dense keeps all 31B worth of attention on every token; MoE's routed 4B subset on any given token may not have attended to the "DISPATCH workers" rule during justification-writing, so the model finishes its sentence and stops.

**Evidence for:** Dense has uniform msg1 shape (monologue-then-tool). MoE is bimodal (terse-stop OR chatbot-menu) — suggesting the harness rule is sometimes present in active experts and sometimes not. Task 9 MoE obeys the "short, then tool" shape (cronjob call); Task 4 MoE omits even the preamble. That inconsistency is consistent with router noise.

**Evidence against:** MoE retry rate is 5/5 (per artifact §6.4) — the correction prompt DOES activate the right behavior reliably. So MoE isn't missing the rule entirely; it just doesn't act on it first-turn. This suggests the gap is closer to "MoE needs a pointer to the dispatch rule at decode time" than "MoE forgets the rule."

### H3 — Token-level bias at the "first tool call position"
**Hypothesis:** After emitting `[TASK CLASS: structured]\nJustification: <prose>.\n\n`, the next token's log-prob distribution differs sharply between the two models:
- Dense: heavy mass on `I` / `First` / `Let me` (continue-the-turn tokens), leading into a `tool_calls` finish.
- MoE: heavy mass on `<|endoftext|>` / `<eot>` (end-of-turn) OR on `How would you like` / `Do you want` (chatbot-menu tokens).

**Evidence for:** The Task 10 MoE response shows an explicit chatbot-menu close. The Task 4 and 6 MoE responses show clean end-of-turn after the justification. Dense never shows either pattern.

**Implication:** a prompt-level fix could be "after emitting the TASK CLASS marker, your NEXT token must be a tool call — do not emit end-of-turn and do not emit a question back to the user." This specifically targets the first-tool-call token-selection position where MoE diverges.

### H4 — Classification and tool-emission are two separate generations in MoE's training distribution
**Hypothesis:** Gemma MoE may have been RLHF'd on data where classification-like outputs were END-of-turn events (chat-style labeling), while tool use was a separate turn type. In MoE's prior, emitting `[TASK CLASS: ...]` IS the turn. In dense's prior, emitting the marker is preamble to the tool call.

**Evidence for:** MoE's three no-tool-call msg1s all look like "label-and-stop" — exactly the shape of a standalone classification response. Task 10's menu close is a stronger form of the same thing (a "what next?" chat-style close).

**Implication:** either (a) reword the marker so it doesn't look like a complete classification response (e.g. inline it into a sentence rather than as a free-floating bracketed label), or (b) add a scaffolding token after the marker that signals "continuation expected" (e.g. require the format "`[TASK CLASS: structured]\nJustification: <one line>\n<DISPATCH:>` ..." where the `<DISPATCH:>` prefix forces a continuation).

---

## 6. Actionable signal

### 6.1 What this data tells us

1. **The first-turn dispatch gap between dense (1/5) and MoE (0/5) is one trial wide and comes from Task 4 alone.** On Tasks 5, 6, 9, 10 both models fail to dispatch on msg1. The narrative that "dense leads with dispatch, MoE doesn't" is overstated; the real narrative is "dense always emits some tool, MoE sometimes emits no tool."
2. **The MoE failure mode is structurally different from dense's.** Dense role-collapses into orientation tools (4/5 of its msg1 tool calls are read-only orientation). MoE in 3/5 cases doesn't emit any tool and waits for the wrapper's correction turn (which works — 5/5 retry rescue).
3. **Task 9 shows both models are tool-wise-indistinguishable when they do emit a tool.** Same tool, same args. The difference reappears only on retry trajectory where dense dives into `skill_manage` mutation and MoE cleanly dispatches.
4. **Task 10 MoE is the diagnostic case.** It's the only first-turn where any model explicitly punts to the user via a menu ("Do you want me to expand on any of these specific phases? / How would you like to proceed?"). This is chatbot-RLHF behavior leaking through the harness, and it's the strongest single data point for training-distribution drift as the root cause.

### 6.2 Targeted interventions

Ranked by expected efficacy against the observed first-turn data:

1. **HERMES.md: add a "First tool call" rule immediately after the Classification Gate section.** Draft:
   > After emitting the `[TASK CLASS: ...]` block for a structured or long-horizon task, your NEXT action in the same turn MUST be a `delegate_worker` tool call. Do not end the turn. Do not ask the user a question. Do not emit an orientation tool call. The marker and the dispatch are a single unit — both must appear in the first assistant turn.
   
   Expected to specifically fix MoE's "label-and-stop" and "chatbot-menu" failure modes (Tasks 4, 6, 10). Won't directly fix role-collapse-into-orientation on dense (but may nudge).

2. **Schema/marker redesign.** Make the marker a prefix of a tool-call argument rather than a free-floating content block. For example, require the first dispatch to have a `classification` field: `delegate_worker(classification="structured", justification="...", goal="...")`. This fuses classification and dispatch at the schema level so the model cannot emit one without the other. 
   
   Expected to structurally eliminate the "no tool call" failure mode on MoE entirely. Requires HERMES.md + tool-schema changes coordinated.

3. **Retry prompt tuning to exploit MoE's high rescue rate.** MoE retry-rescues 5/5 (vs dense 1/4). Given the low cost of retry on MoE (per-trial wall-clock ~130s median), a tighter retry prompt that immediately orders `delegate_worker` would move MoE's effective final dispatch rate close to 100%. Not a first-turn fix; just a way to monetize the asymmetry.

4. **Check.py hardening to accept msg1-missing-marker when later msgs fix it.** Addresses the Task 1 & 7 check-script artifact, not the core dispatch divergence — but relevant for MoE overall.

5. **Log first-turn tool-call distribution per model at finer grain.** This analysis worked from 10 sessions. A follow-up should aggregate first-tool-call frequencies across larger N (≥20 per model) and check whether the `none` bucket on MoE is stable at ~60% or whether it's a sampling blip.

### 6.3 What NOT to do based on this data

- **Do not** try to fix dense by rewording the orientation prose — dense's prose says "dispatch workers" in Task 6 and it still emits `terminal(ls -R)`. The prose→action disconnect is structural, not linguistic.
- **Do not** infer from aggregate metrics that MoE "almost dispatches but picks the wrong tool." That framing fits dense (which always picks a tool). MoE's actual failure in 3/5 is *not emitting a tool at all*.
- **Do not** assume the Task 9 first-turn dead heat is representative. It's 1 of 5 and both models happen to reach for the same tool; the deeper retry trajectory on dense still mutates a tripwire (SKILL.md) while MoE's stays clean.

---

## 7. Artifact provenance

- All session JSONs pulled via `scp` from `ubuntu-vm:/home/parallels/.hermes/sessions/` into `/tmp/probe-r72-sessions/`.
- Extraction script: `/tmp/extract_first_assist.py` (Python 3, reads `messages[0]` for first user, first `role==assistant` message, prints `content`, `reasoning_content`, `tool_calls[0]`).
- Extracts cached at `/tmp/probe-r72-sessions/extract_<session_id>.txt` (one per session, 10 total).
- Spot-check confirmed via `grep "Model: " /tmp/probe-r72-sessions/extract_*.txt`:
  - Dense 5/5 sessions record `gemma-4-31b-it-4bit`.
  - MoE 5/5 sessions record `gemma-4-26B-A4B-it-MLX-8bit`.
- Message-sequence verification for MoE Tasks 4/6/10 confirmed msg1 tool_calls is `None` and msg2 is the wrapper's correction prompt — MoE genuinely emits no tool on the first turn.
- No AgentFW files modified. No HERMES.md edits. No sessions re-run. Read-only throughout.

End of artifact.
