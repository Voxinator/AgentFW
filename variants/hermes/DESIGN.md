# Hermes-flavored AgentFW — Design Spec

**Status:** pre-release (r7.5-hermes-prerelease). Dispatch-layer thesis validated; worker-quality ship gate not yet met. See `/RELEASE-NOTES-r7.5-hermes-prerelease.md`.
**Scope:** How the AgentFW harness runs on Hermes Agent (`github.com/NousResearch/hermes-agent`) with Gemma-4 (dense or MoE) as the local orchestrator, using the r7.4 β-fuse dispatch architecture plus the r7.5 turn-0 toolset restriction hook.
**Audience:** An agent or human picking up this work cold. You can read this doc without having seen the probe trajectory. For empirical numbers see `PROBE-RESULTS-r7.md`; for install/rollback see `INSTALL.md`.

---

## 1. What this variant is (and is not)

**Is:** A Hermes-specific deployment of AgentFW that lets a local Gemma-4 model operate the Planner-Worker-Judge harness end-to-end. Gemma classifies the task, dispatches fresh-context child Gemma sessions as workers via a β-fuse tool call, optionally dispatches a separate child Gemma as judge, evaluates results, iterates. 100% local inference. No Anthropic cloud, no Python orchestrator wrapping the agent loop.

**Is not:**
- A replacement for AgentFW's canonical `core/harness-core.md` or any non-Hermes variant. The claude-code, claude-projects, and generic variants continue to work exactly as before; they are untouched.
- A fork of the AgentFW core. The Hermes variant lives entirely under `variants/hermes/` plus five small edits to Hermes's own source (with backup files preserved at every stage).
- Production-ready. The r7.4 β-fuse dispatch layer is validated (MoE 17/20 first-attempt strict, 11.5×–17× lift over pre-intervention baselines). The r7.5 worker-quality ship gate is not yet met (3/20 PASS vs ≥15/20 floor); that is r7.6 scope.

---

## 2. The binding constraint that drove the design

The operator's explicit requirement: **"Gemma as the Planner/Orchestrator, workers = separate Gemma sessions, judges = separate Gemma sessions, all reporting back to parent, 100% local inference."**

This rules out:
- Cloud inference for any role (Gemma must be the parent, not Claude/GPT-delegating-to-Gemma).
- A Python driver running the agent loop and calling Gemma just to format responses. The orchestration logic itself must live inside Gemma's tool-calling behavior.
- Any dependency on `claude --acp` or external CLI sub-agents that would route a subtask to a non-local model.

This allows:
- A thin retry wrapper AROUND `hermes chat` CLI invocations that re-prompts on contract violations. Gemma still emits the dispatch tool call — the wrapper just nudges on role collapse and handles SIGTERM mis-attribution. The wrapper does not execute any model inference itself.

---

## 3. Why base Hermes + Gemma doesn't work as-is (the diagnosis)

The r7 probe measured what happens when Gemma runs canonical `variants/hermes/HERMES.md` against structured/long-horizon tasks. The strict on-disk dispatch rate under base Hermes was **~0–7% first-attempt** across multiple remediation attempts. Gemma did the work itself in the main session the overwhelming majority of the time. Investigation across r7, r7.2, and r7.3 identified four compounding causes:

- **`delegate_task`'s tool surface is too complex for Gemma.** Two-mode union schema (`goal` XOR `tasks`-array), nested arrays of objects, anti-dispatch text in the description ("WHEN NOT TO USE: Single tool call → just call the tool directly"). Gemma handles flat scalars well; struggles with conditional shape selection.
- **HERMES.md sits in the prompt's attention valley** (slot 10 of 12 in `_build_system_prompt`). The classification rules compete for attention with 11 KB of skills-index and a trailing CLI markdown hint.
- **HERMES.md and the r7.3 wrapper correction text both contained escape clauses** inviting the model to rationalize a re-classify-to-one-shot path.
- **Dense and MoE fail at mechanically different decode steps.** Dense role-collapses to read/orient tools (`search_files`, `read_file`, sometimes mutating tools); MoE goes chatbot-mode and emits no tool call at all.

r7.3 shipped Layers 1+2 (toolset restriction + escape-hatch removal) and produced **1/15 dispatch on each model — failing both gates.** The conclusion was structural: language-only remediation cannot force a behavior that the model's tokenizer can work around. Something in the tool surface itself had to change.

r7.4 shipped that change: **β-fuse.**

---

## 4. Architecture — β-fuse + turn-0 restriction

### 4.1. `HERMES-variantF.md` — the system prompt

Replaces canonical `HERMES.md` when the harness is active. md5 `01c0e77bb2a6e753a8ea9063784a25e0`. Teaches `delegate_worker_v2` exclusively (v1 retained for backwards-compat but marked deprecated). Retains the r7.3 hard output contract (classification marker as first line) as defense-in-depth — the β-fuse tool argument is the primary contract; the marker is a fallback detectable at the check-script layer.

### 4.2. `delegate_worker_v2.py` — the β-fuse dispatch tool

md5 `d31876fe987331a26c8640202334fd46`. The structural fusion:

- **Required argument `classification: enum["one-shot", "structured", "long-horizon"]`.** Server-side validated.
- **Required argument `justification: str (≥30 chars)`.** Server-side validated.
- **Conditionally required `goal: str`** for `structured` and `long-horizon` classifications.
- **Schema description leads with the imperative:** *"Call this tool as your FIRST action on every task."* High-attention first token of the tool description; validated in the r7.4 phase-A ζ-worker finding.

The design principle: **classification becomes a payload that the model cannot emit without calling the dispatch tool.** Under β-fuse you cannot satisfy the contract by emitting a marker and then proceeding to `patch` or `search_files` — the dispatch call IS the marker.

v1's `delegate_worker(goal: str)` remains registered side-by-side and returns a `deprecation_warning` string in its response when called. HERMES-variantF.md does not teach v1; it is there only to keep backwards-compat for edge cases.

#### 4.2.1. How HERMES.md lands in the assembled prompt

`HERMES.md` is not alone in the system prompt — it is injected alongside the operator's Hermes-native `SOUL.md`, `USER.md`, and `MEMORY.md` files by `_build_system_prompt` in `run_agent.py`. Current assembly order places `SOUL.md` near the sink zone (slot ~2) and `HERMES.md` in the `context_files_prompt` block (slot ~10, behind the ~11.8 KB skills index). A `SOUL.md` that biases toward conversational/prose-first output can compete with `HERMES.md`'s first-tool-call contract, which matters when installing the variant onto an existing customized Hermes.

For operator-facing guidance on this interaction — slot-by-slot assembly order, red-flag `SOUL.md` directives, and the dogfooding recommendation before swapping canonical — see `INSTALL.md § HERMES.md, SOUL.md, and the prompt assembly`. For the prompt-builder edit that would move `HERMES.md` into the recency zone (IMPL-4 Option A2, not landed), see `archive/hermes-probe-r7.2-r7.3-2026-04-18/ARTIFACT-impl-4-soul-restructure.md`.

### 4.3. The r7.5 turn-0 toolset restriction hook

Closes the dense `todo` / `search_files` escape observed in r7.4: 3 of 13 dense structured/LH trials bypassed v2 by calling `todo` or `search_files` as their first tool, then exhausting retries without reaching v2.

**Mechanism:** a new method `_resolve_tools_for_turn_r75a` in `run_agent.py` wired into both API branches of `_build_api_kwargs`. When the session's `enabled_toolsets` is **exactly** `{delegation, todo, clarify, file_readonly}` (the β-fuse probe composition) AND no assistant message in `api_messages` has yet called `delegate_worker_v2`, the tool list sent to the LLM is filtered down to `{delegate_worker_v2, clarify}`. Once any prior assistant turn has emitted a v2 tool call (successful OR errored), the full declared toolset is bound for subsequent turns.

Critical scoping property: the comparison is **order-insensitive equality** against the exact β-fuse set. Any other composition (canonical `hermes-cli`, cron sessions, hermes-telegram, interactive chat) bypasses the hook entirely. This means the r7.5 change is side-effect-free for non-harness flows — a hard requirement of the deployment model.

### 4.4. Hermes source patches

Total surface: 5 edits across 3 files, all with `.probe-*-orig` backups. Idempotent staging via `probe-variantF-stage.sh` (r7.4) + `probe-variantG-stage.sh` (r7.5). See `INSTALL.md` for exact commands and `IMPLEMENTATION.md` for historical r7 patches.

- **`model_tools.py`** — +1 line, import `tools.delegate_worker_v2`.
- **`toolsets.py`** — register `delegate_worker_v2` in `_HERMES_CORE_TOOLS` and the `delegation` bundle.
- **`run_agent.py`** — extend `delegate_task` dispatch sites to route `delegate_worker_v2`; insert the turn-0 toolset restriction method + two `_build_api_kwargs` call-sites.

### 4.5. Optional: the runtime wrapper

`probe-variantG-wrapper.sh` + `probe-variantG-check.py`. Load-bearing for the r7.5 probe; optional for ship. Implements:

1. Trial runner — `hermes chat -Q -q "<task>" --max-turns 20 --checkpoints -t delegation,todo,clarify,file_readonly`
2. Session analysis — parses the persisted parent session JSON, reads classification from `tool_calls[0].function.arguments.classification` directly (not a text marker), filters hallucinated-tool-name calls that Hermes rejected (the r7.3 P1 analyzer fix), and emits COMPLIANT / VIOLATION:* / ERROR:* verdicts.
3. Retry loop — on violation, sends a corrective re-prompt via `hermes chat --resume`. Loops up to 3 retries.
4. **Tier-1 SIGTERM content-match recovery** — when the parent's stdout `session_id:` line is lost to SIGTERM, the wrapper content-matches a candidate session's `messages[0]` against the prompt's first 80 bytes (base64-encoded through SSH to survive newlines/quotes). A mis-attached child session is correctly classified as `ERROR:WRONG_SESSION` (wrapper problem) rather than `NO_ASSISTANT_RESPONSE` (model problem).

The wrapper is a thin process-level gate around CLI invocations. Orchestration still lives inside Gemma's tool-calling behavior. The wrapper is the equivalent of a lint-and-retry loop around a compiler — the compiler does the real work.

---

## 5. The Planner-Worker-Judge flow on Gemma

End-to-end, with variantF + variantG + wrapper active:

```
[1] User: "Refactor the auth module to use the new session store.
         Three files: src/auth/session.ts, src/auth/middleware.ts,
         tests/auth.test.ts. Tests must pass."

[2] Parent Gemma (main session, β-fuse toolset {delegation,todo,clarify,file_readonly}):
      Turn 0 — tool list filtered to {delegate_worker_v2, clarify} by r7.5 hook.
      Model emits:

      <tool_call>
      {"name": "delegate_worker_v2", "arguments": {
         "classification": "structured",
         "justification": "Touches three files with cross-file dependencies
                         and requires test verification to ensure no
                         regressions.",
         "goal": "Refactor src/auth/{session,middleware}.ts to use the new
                session store. Update tests/auth.test.ts. Run
                `npm test tests/auth.test.ts`; all tests must pass."}}
      </tool_call>

[3] Hermes runtime intercepts delegate_worker_v2 → calls
    _delegate_task(goal=<above>, parent_agent=self, …)
    → spawns child AIAgent with fresh context.
    Turn 1+ in parent: full toolset re-bound (hook sees v2_called=True).

[4] Child Gemma (worker session, no memory of parent, inherits full Hermes toolset):
      - reads files, makes edits, runs tests
      - returns summary: "49/49 tests pass. Files modified: …"
      [Known r7.5 caveat: child-session execution quality is below floor.
       4 primary failure modes, tracked as r7.6 scope.]

[5] Parent Gemma receives summary. Optionally dispatches a verification judge
    via another delegate_worker_v2 call.

[6] Parent Gemma: "Task complete."
```

Every arrow that crosses a process boundary (→) is a spawned child Gemma with fresh context. The parent only sees final summaries. Role separation is enforced by the process model.

---

## 6. What this variant does and does not change

### Changes (all inside the Hermes install + repo)

- Adds two tool files: `tools/delegate_worker.py` (legacy), `tools/delegate_worker_v2.py` (β-fuse)
- Patches three Hermes files: `model_tools.py`, `toolsets.py`, `run_agent.py` (5 edits total)
- Swaps `HERMES.md` for `HERMES-variantF.md` when harness is active
- Adds `file_readonly` toolset bundle (r7.3, additive)

### Does NOT change

- `core/harness-core.md`, `references/*`, `playbooks/*`, `templates/*` — AgentFW core is untouched.
- `variants/claude-code/`, `variants/claude-projects/`, `variants/generic/` — other variants unaffected.
- `delegate_task` — still registered, still functional, still available. Not deprecated.
- Existing Hermes skills (Jira-daily-briefing, etc.) — all continue to work under canonical HERMES.md; the r7.5 turn-0 hook is scoped to the exact β-fuse toolset composition and does not fire on canonical flows.
- Hermes configuration — no changes to `config.yaml`, `settings.json`, or model routing.

### Cross-model integrity guarantee

r7, r7.2, r7.3, r7.4, and r7.5 probe work did NOT touch any AgentFW file outside `variants/hermes/` and top-level `probe-*` scripts. Canonical `core/harness-core.md` md5 is unchanged. The claude-code, claude-projects, and generic variants continue to pass their golden tasks. Any future iteration MUST preserve this isolation — if a change requires touching `core/`, stop and escalate.

---

## 7. Design constraints / non-goals

### Hard constraints (any future change must respect)

- No Python orchestrator wrapping the agent loop. A thin retry wrapper around `hermes chat` CLI invocations IS allowed. A Python state machine that "decides when to dispatch" based on classification IS NOT.
- Gemma must remain the entity that emits `delegate_worker_v2` calls. Any mechanism that auto-injects dispatch calls bypasses the operator's binding constraint.
- Must coexist with existing Hermes workflows. The `HERMES.md` swap is operator-controlled; it does not apply to cron-triggered sessions or canonical CLI flows (the r7.5 turn-0 hook is composition-scoped and short-circuits on any toolset that isn't exactly the β-fuse set).
- AgentFW core and non-Hermes variants stay byte-identical.

### Non-goals

- 100% dispatch reliability. Gemma-4 has behavioral ceilings; MoE 17/20 (85%) is the current validated dispatch rate. The variant targets "reliable enough for real work," not "perfect."
- Worker quality — the r7.5 ship gate failure. Children currently fail on search_files thrash, SIGTERM truncation, pseudo-tool-call text emission, and fabricated completion. These are r7.6 scope; β-fuse's contract was never designed to address child execution quality (those are downstream of the dispatch hand-off).
- Deterministic reproducibility. Gemma runs at T=0.8 in production (from `~/.omlx/model_settings.json`). Run-to-run variance is significant. Probe data is indicative, not exhaustive.

---

## 8. Failure modes addressed vs residual

### Addressed by β-fuse + r7.5 turn-0 hook

- **Marker emission.** Was 0/10 under base Hermes (r7 variant A). Now 20/20 (marker derived from `tool_calls[0].function.arguments.classification`).
- **Dispatch emission — format layer.** Variant D's simpler tool surface fixed the "Gemma can't emit complex nested JSON" problem; variant F's β-fuse fixed "marker without dispatch." MoE 17/20 (r7.4) / 16/20 (r7.5).
- **Cascading main-session mutations.** 0 tripwire mutations across r7.4 + r7.5 aggregate probe runs under the restricted β-fuse toolset.
- **The `todo` / `search_files` escape (dense-specific).** r7.5 turn-0 hook closes this at the mechanism layer — the model is mechanically unable to call `todo` or `search_files` at turn 0.
- **Hallucinated-tool-name probe-analyzer artifact.** Filtered in `probe-variantF-check.py` + `probe-variantG-check.py` (the r7.3 "terminal leak" was an analyzer artifact; 34-trial verification in `ARTIFACT-r7.4-p1-terminal-binding.md`).
- **SIGTERM mis-attribution (parent).** r7.5 Tier-1 content-match recovery with `--expected-prompt-prefix-b64`; `ERROR:WRONG_SESSION` verdict.

### Residual (r7.6 scope)

- **Worker-quality floor (3/20 vs 15/20).** Four failure modes enumerated in `ARTIFACT-r7.5-SHIP-judge-verdict.md` Part 5; r7.6 scope includes child-session scaffolding, child-toolset restriction, turn-budget tuning, anti-fabrication guardrail, pseudo-tool-call format enforcement, child-side SIGTERM research.
- **MoE empty-first-turn quirk (~20% base rate).** 4/20 r7.5, 3/20 r7.4. Within Poisson variance; wrapper retry loop recovers cleanly. Keep under observation across future probes.
- **Upstream Hermes SIGTERM handler (Tier 3).** Designed but not applied. `ARTIFACT-r7.4-sigterm-research.md`.
- **Pre-existing slice error in the v2 handler.** Latent; doesn't block dispatch but can surface on specific tool-call shapes.

---

## 9. Why the Jira-skill pattern generalizes (empirical basis)

The Jira-daily-briefing skill (pre-existing, production-reliable) achieves high tool-call accuracy via three moves:

1. **Narrow tool surface.** Uses `terminal` only — one tool, one string arg.
2. **Worked format example in the skill prompt.** Literal `<tool_call>{...}</tool_call>` example.
3. **Deterministic fallback.** If Gemma's tool calling fails, `jira-briefing.sh` handles it.

The Hermes variant of AgentFW applies the same moves, now extended to β-fuse:

1. **Narrow tool surface.** `delegate_worker_v2` with a small enum + one string. Turn-0 hook further narrows at the runtime layer to `{delegate_worker_v2, clarify}`.
2. **Structural fusion of the contract into the tool signature.** β-fuse extends the "worked example" pattern — classification isn't a hint, it's a required argument.
3. **Runtime retry + wrapper gating.** `probe-variantG-wrapper.sh` detects role collapse / no-dispatch / fabrication / pseudo-tool-call text and re-prompts.

Gemma-4's capability ceiling is "execute well-defined procedures with simple tool surfaces and unambiguous contracts." Give it β-fuse's shape and dispatch fires >80%. Give it upstream `delegate_task`'s shape and it silently skips.

---

## 10. Versioning and the ship candidate

**Current state (r7.5 pre-release):**
- Canonical `variants/hermes/HERMES.md` — upstream Hermes base (md5 `0780c232…`). Unchanged throughout r7.x.
- `variants/hermes/HERMES-variantB/D/E.md` — historical probe siblings. Retained for re-probe.
- `variants/hermes/HERMES-variantF.md` — **the r7.4 ship candidate (SHIP-WITH-CAVEAT).** Loaded into live `HERMES.md` position on the VM when the harness is active.
- `variants/hermes/delegate_worker_v2.py` — the β-fuse tool.
- r7.5 turn-0 hook in `run_agent.py` — currently unstaged on VM by default.

**Ship options:**
1. **Keep variantF as opt-in.** Current state. Operator stages via `probe-variantF-stage.sh` + `probe-variantG-stage.sh`. Cleanest separation.
2. **Canonicalize variantF.** Replace upstream `HERMES.md` with variantF's contents. r7.4 judge supports this independent of r7.5's worker-quality hold. Operator decision.
3. **Promote to upstream Hermes.** Submit `delegate_worker_v2` as a minimal upstream PR with v1 coexistence. Deferred; see NEXT-STEPS.md Priority 4.

**Recommended:** option 1 until r7.6 closes the worker-quality gate, or option 2 if the operator's production use case is dispatch-only (not child-quality-sensitive). See `/RELEASE-NOTES-r7.5-hermes-prerelease.md` for the decision tree.

---

## 11. References

- **Install + rollback:** `INSTALL.md` (authoritative; supersedes `IMPLEMENTATION.md`)
- **Tested versions + hardware:** `DEPENDENCIES.md`
- **Empirical validation:** `PROBE-RESULTS-r7.md` (historical), `ARTIFACT-r7.4-ship-judge-verdict-v2.md` (r7.4 SHIP-WITH-CAVEAT), `ARTIFACT-r7.5-SHIP-judge-verdict.md` (r7.5 HOLD-narrow)
- **β-fuse design:** `ARTIFACT-impl-3-beta-fuse-spec.md`
- **r7.5 turn-0 hook:** `ARTIFACT-r7.5-A1-impl-notes.md`
- **r7.5 wrapper/check hardening:** `ARTIFACT-r7.5-B1-impl-notes.md`, `ARTIFACT-r7.5-B2-impl-notes.md`
- **r7.5 worker-quality data:** `ARTIFACT-r7.5-F2-probe-results.md`, `ARTIFACT-r7.5-worker-quality-trial-{01..20}.md`
- **Follow-up work:** `NEXT-STEPS.md`
- **Release notes:** `/RELEASE-NOTES-r7.5-hermes-prerelease.md`
- **Upstream Hermes:** `github.com/NousResearch/hermes-agent` (v0.8.0 / commit `86960cdb`)
- **The Jira skill this pattern was inspired by:** `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/` on the Hermes install
