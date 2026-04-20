# ARTIFACT — Judge θ — Remediation Playbook (ranked)

Judge: θ. Fresh context synthesis of seven parallel worker reports (α prompt anatomy, β first-turn diff, γ retry divergence, δ tool surface, ε toolset restriction, ζ prompt rewrites, η correction rewrites) plus the corrected baseline (drift step A re-tally) and current probes (r7.2 dense v2, r7.2 MoE).

Scope-of-change promise: every recommendation below stays inside `variants/hermes/` + probe infrastructure + Hermes install patches on ubuntu-vm. No `core/`, `references/`, `playbooks/`, `templates/`, or non-Hermes variants are touched.

Baseline (strict persisted-JSON criterion, structured/LH Tasks 4/5/6/9/10):

| Model | First-attempt dispatch | Final dispatch (after retries) |
|-------|------------------------|--------------------------------|
| Gemma-4-31B dense v2 | 1/5 (Trial 4) | 2/5 (Trials 4, 10) |
| Gemma-4-26B-A4B MoE | 0/5 | 5/5 |

Worker-claim spot checks performed before synthesis:
- **α's Slot 9 / HERMES.md-in-middle claim** against `variants/hermes/HERMES-variantD.md` line 109 (`## HOW TO DISPATCH WORKERS — CRITICAL`) — **confirmed**, with L82 escape hatch and L140–157 hedges at the exact lines ζ cited.
- **γ's correction-text escape clause** against `probe-variantE-wrapper.sh` lines 87–95 — **confirmed verbatim** ("If you truly believe dispatch isn't warranted, re-classify to `one-shot`…").
- **δ's delegate_worker description** against `variants/hermes/delegate_worker.py` lines 20–50 — **confirmed verbatim**; the "ALWAYS USE" clause is in paragraph 2 of a 3-paragraph block, not sentence 1 (ζ weak-spot F is correct).
- **β's Task 4 MoE empty-tool-call claim** against MoE session `20260418_161559_5874c2` metadata in the MoE probe artifact — **confirmed** (§2.2 table: msg1 first-tool "(no tool calls)", finish_reason `None`).
- **γ's dense Trial 9 re-classify-argument-is-factually-wrong claim** (§4.4, "SKILL.md + jobs.json = 2 files"): session `20260418_145925_118829` tool sequence in drift-step-A retally shows `cronjob, skill_view, terminal×7, skill_manage, cronjob×2` — at least two mutating surfaces (`skill_manage` on SKILL.md plus `cronjob action=update` on the job). γ's claim holds.

No worker claim flagged as inconsistent with source.

---

## 1. Executive summary

**Root cause in one paragraph.** Gemma's first-attempt dispatch rate is low because the harness asks the tool-selection head to make the right choice inside a pathologically unfavourable decision field: (1) the tool array is 29 schemas dominated by large orienting/mutating primitives (`terminal`, `search_files`, `read_file`, `patch`, `write_file`) and the larger anti-dispatch sibling `delegate_task` — with the actual dispatch primitive `delegate_worker` at index 13/29 and 3.6× smaller than the competitor immediately above it; (2) the HERMES.md rule lives at byte 29,839 of a 36,684-byte prompt, behind an 11.8 KB skills index, with the recency slot wasted on a CLI markdown hint; (3) HERMES.md and `delegate_worker`'s description both offer legitimate "re-classify to one-shot" / "single tool call — just run it" escape hatches that dense Gemma reads correctly and takes; (4) the retry-correction text repeats the same escape hatch at the end, which dense treats as a directive to argue back, while MoE reads it as a format scaffold and complies. Dense fails by role-collapsing into orientation tools (4/5 of its msg1 first-tool selections are read-only); MoE fails by going chatbot-mode (3/5 of its msg1s emit no tool call at all). The two models fail for mechanically different reasons and will only converge under structural enforcement, not wording changes.

**Top 3 fixes, priority order:**
1. **ε-T1 + δ-reorder: restricted toolset (`delegation,todo,clarify,file_readonly`) with delegate_worker promoted to array index 0.** Kills tool competition and role-collapse attractors in one move; cheapest experiment to run, fully reversible.
2. **η-C2 + ζ-R1: strip the escape clause from the correction message AND aggressive-imperative schema rewrite on `delegate_worker`.** Removes the dense "argue back" surface, front-loads the imperative on the schema read at every tool selection.
3. **β-fuse: add required `classification` + `justification` args to `delegate_worker` and make it the marker-emission primitive.** Structural nuclear option; targets MoE's chatbot-mode failure directly; adopt as endgame once (1) and (2) are measured.

**Single first action.** Run **ε Tier-1 restricted toolset on dense Task 4 + Task 6 + Task 9, N=5 each** (15 trials, ~60 min wall-clock). Committed pass threshold: dense first-attempt dispatch ≥ 3/5 pooled over the three tasks (baseline is 1/15). Detail in §9.

---

## 2. Consolidated root-cause picture

The seven workers converge on a single story in four layers, each of which alone would make first-attempt dispatch hard, and which together explain why both models fail at msg1.

**Layer 1 — the prompt geometry is hostile.** α shows the system prompt is 36,684 bytes across 11 slots. The dispatch scaffolding (`HOW TO DISPATCH WORKERS — CRITICAL`) sits at bytes 29,839–33,207 — 82% of the way through, past the worst of the "lost-in-the-middle" valley but still ~6 KB before the recency zone. The recency zone itself is spent on a markdown-formatting hint (`PLATFORM_HINTS["cli"]`). The single largest block is an 11.8 KB skills index the model doesn't need for any probe task. HERMES.md never reaches the attention peaks. For a 31B dense model with RoPE-scaled positional encoding, this means the rule is present but under-attended at decode time.

**Layer 2 — the tool array is actively adversarial.** δ and ε agree: 29 tool schemas are alphabetically sorted, so `browser_*` occupies indices 0–9 (the high-position-bias slots) on a VM where browser tools are never used. `delegate_task` at index 12 (3,721 B) precedes `delegate_worker` at index 13 (1,040 B); the larger sibling's description contains the anti-dispatch clause "WHEN NOT TO USE: Single tool call → just call the tool directly." `terminal` (3,564 B), `search_files` (1,786 B), and `read_file` (923 B) all have rich orienting-affordance language. δ's "20:1 description-dilution ratio" metric captures this: ~9,750 characters of competing pro-use framing against `delegate_worker`'s 488 characters of "ALWAYS USE." Gemma's function-calling head is making a local decision over a list in which orientation primitives are larger, more numerous, and framed without task-class gates; dispatch is one small voice in a crowd.

**Layer 3 — the text itself offers a legitimate exit.** ζ enumerates five escape hatches inside HERMES-variantD.md (L82 "stop and re-classify", L140–143 "WHEN NOT to use delegate_worker", L153–157 "Role separation can be relaxed ONLY when… quick lookups and orientation reads", L143 "single tool call — just run it", L156 "Quick lookups"). η confirms the wrapper's correction text repeats the same hatch ("If you truly believe dispatch isn't warranted, re-classify to `one-shot`"). γ's retry-forensics is the load-bearing evidence that this matters: dense on Trial 9 emits three consecutive retry responses that **quote the one-shot criteria back clause-for-clause** ("fewer than 20 lines", "no cross-file dependencies") as justification for not dispatching. This is instruction-*comprehension* intact with instruction-*compliance* broken. The model is following the literal letter of the harness (the exit clause is a legitimate path) while subverting its intent.

**Layer 4 — the two models fail at different points in the decoder.** β's first-turn byte diff is the most diagnostic single document. Dense's msg1 follows a rigid 3-part template (marker → "I'll orient…" preamble → read-only tool call); it reliably emits SOME tool, just not `delegate_worker`. MoE's msg1 is bimodal: in 3/5 structured/LH trials (Tasks 4, 6, 10) MoE emits **zero tool calls** — the message terminates cleanly after the justification via end-of-turn token, or (on Task 10) appends a chatbot-style "How would you like to proceed?" menu. MoE's failure is not wrong-tool; it is no-tool. This separation means any fix that lifts dense may not lift MoE and vice versa. Dense needs the competitor tools removed or the orientation-preamble closed; MoE needs the turn not to end after the marker.

**Weave.** The four layers compose multiplicatively: the rule is far from the attention peaks (Layer 1), the alternatives are louder (Layer 2), the rule itself offers a way out (Layer 3), and the two models each latch onto a different failure mode at the decode step (Layer 4). The current retry wrapper papers over Layer 4 for MoE (which treats correction as directive) and fails for dense (which treats correction as argument). Any fix that only touches one layer is fighting three other layers; that is why wording-only fixes (like ζ-R2 alone, or η-C1 alone) are not expected to carry. The highest-leverage interventions are the ones that collapse multiple layers at once — toolset restriction (Layers 1+2+3 partially, by deleting competitors and escape surface), schema-level imperative rewrite (Layers 2+3, by making the tool-read imperative impossible to escape), and classification-fused dispatch (Layer 4 structurally, by removing the possibility of a marker-without-dispatch turn).

**Load-bearing vs cosmetic.** Load-bearing: δ's tool-array dominance, ε's restricted-toolset design, β's MoE-chatbot-mode finding, γ's compliance-not-comprehension finding, ζ-R1's schema rewrite, η-C2's escape-clause removal. Cosmetic / secondary: α's HERMES.md reorder (H1–H3 in α are speculative without model-family data on Gemma-4's long-context bias), ζ-R3's additional worked examples (additive, low-risk, low-expected-lift), ζ-R4's section reorder (ζ itself flags this as highest-uncertainty), η-C4's cite-evidence (η itself rejects it). The `PLATFORM_HINTS` swap (α-E1) is cheap and worth trying but is not load-bearing against the tool-array dominance finding.

---

## 3. Convergence / divergence audit

### Convergent across multiple workers

- **"Remove the choice" across every layer.** α (toolset pruning), δ (tool reordering + competitor removal), ε (Tier 1/2/3 toolset restriction), ζ-R1 (extend the forbidden list in the schema to include reads), η-C2 (remove the escape clause from the correction). Five of seven workers independently land on some form of "eliminate the alternative to dispatch."
- **`delegate_task` is actively harmful.** α H5, δ §4 (schema-size 3.5× `delegate_worker`, explicit anti-dispatch language), ζ weak-spot E. All three recommend either shrinking or removing `delegate_task` from the bound tool set. δ goes further and names it as the "pick the big delegate_task by accident" risk.
- **Dense's msg1 is always a tool call; MoE's often isn't.** β direct observation. γ independently corroborates (retry-eligible N=4 for dense, N=5 for MoE — the difference is MoE failing to dispatch at all on A0, not MoE picking a different tool). This is the single most important behavioral fact in the dataset for prioritization.
- **Retries work for MoE, not dense.** γ's §3 pattern table (MoE 5/5 apologize-and-comply, dense 3/4 re-classify-and-argue). η picks up the same pattern from the wrapper side.
- **Escape hatches in text are load-bearing for dense.** γ §5.3, η §1, ζ §1a weak-spot B. Three workers coming from three different angles all identify the re-classify-to-one-shot escape as the dense rationalization path.

### Divergent / in tension

- **α's prompt-reorder hypotheses vs δ/ε's tool-array hypotheses.** α says the fix is to move HERMES.md earlier or the dispatch section later (H1/H2). δ and ε say the prompt text is not load-bearing; the tool array is. α's own E1 recommends a prompt-level reorder as cheapest first test; δ and ε both recommend toolset restriction. Pick δ/ε. Evidence: α's own section 5 acknowledges Gemma's function-calling head reads the tools list at decode time, and the tool array is 38,364 bytes — larger than the system prompt. Tool-array changes act at the decode point; prompt-reorder acts at the pre-read point with much less direct coupling to the function-calling head.
- **η-C1 (shorter + imperative) vs η-C2 (remove escape hatch).** η ranks C2 above C1. γ's analysis confirms: the escape hatch IS the load-bearing issue for dense, not wording brevity. Pick C2.
- **β's "fuse classification into delegate_worker" vs ζ's "refine escape-hatch language in the text."** β proposes architectural change (structured dispatch requires the tool call to include the classification). ζ proposes textual tightening. β is strictly more powerful (removes the failure mode mechanically), but also strictly more invasive (check.py changes, HERMES.md workflow revision). Treat as sequential: ζ first (cheap), β second (structural endgame).
- **γ's "dense is exercising a legitimate exit" vs η's "dense is rationalizing."** γ argues dense's re-classify argument is *literally rule-compliant* given the current text — the escape clause is there, dense takes it. η treats it as rationalization to be closed off. These are not actually in tension; they describe the same phenomenon from different angles. The fix is the same (η-C2 / ζ-R2: close the clause), but it matters for the framing: the fix is not "make dense argue less" but "remove the argument surface."

### Explicit contradictions — flagged

**None found that survived spot-checking.** Every apparent contradiction resolves to a sequencing or framing question.

---

## 4. Remediation taxonomy by layer — with per-fix scoring

Legend for scores:
- Impact on dense first-attempt: L (no change expected), M (+1/5–+2/5 pooled), H (+2/5–+4/5 pooled)
- Impact on MoE first-attempt: separately scored; MoE failure is chatbot-mode not wrong-tool
- Cost: S (minutes, single-file edit), M (hours, multi-file or new toolset/schema), L (day+, check.py / workflow changes)
- Risk: reversibility + what it could break

### 4.1 Tool binding layer

| Fix | Source | Dense first-attempt | MoE first-attempt | Cost | Risk | Stacks with |
|-----|--------|---------------------|-------------------|------|------|-------------|
| **Reorder: promote `delegate_worker` to index 0 of the tool array** | δ §5, α H4 | **M** (kills alphabetical-sort position penalty; frees the high-position-bias slot for the one tool we want the model to emit first) | L–M (MoE's failure is emitting no tool; promoting a tool to index 0 doesn't help if the model isn't emitting any tool) | S (one-line patch at tool-binding `sorted()` call) | Low. No behavior changed other than array order. Fully reversible. | ε (restriction), ζ-R1 (schema) |
| **Remove `delegate_task` from the bound tool set for Gemma** | δ §4, α H5 | **M** (eliminates the "pick delegate_task by accident" path; removes the in-schema anti-dispatch clause) | L (same as above — MoE isn't emitting delegate_task; it's emitting nothing) | S (toolset edit) | Low. `delegate_worker` internally calls `delegate_task`, so no capability is lost. | ε (restriction) |
| **Sort by priority field, not alphabetically** | δ §5 | M | L | S (tool-binding patch) | Low. | Same as reorder |

### 4.2 Schema layer

| Fix | Source | Dense first-attempt | MoE first-attempt | Cost | Risk | Stacks with |
|-----|--------|---------------------|-------------------|------|------|-------------|
| **ζ-R1: rewrite `delegate_worker` description — imperative in sentence 1, add "FIRST tool call MUST be", extend forbidden list to include `read_file` and `search_files`** | ζ §2 | **H** (targets the exact sentence the model reads at tool-selection time; closes the orientation-before-dispatch path by forbidding reads) | M (may get MoE to emit `delegate_worker` instead of nothing if the "FIRST tool call MUST be" language propagates into the function-calling head's prior) | S (single-file edit to `delegate_worker.py`) | **Medium.** Forbidding `read_file`/`search_files` in the schema may leak into non-dispatch contexts — could cause hallucinations when model genuinely does need to orient on a one-shot task. Mitigation: the forbidden clause is conditioned on "structured/long-horizon" in the prose. | η-C2, δ-reorder |
| **Shrink `delegate_task` schema or replace with a stub pointing to `delegate_worker`** | δ §4, ζ weak-spot E | M (removes the anti-dispatch clause from tokens the model reads) | L | S (schema edit) | Low — `delegate_task` is still callable internally; only the visible schema shrinks. | δ-remove, δ-reorder |
| **β-fuse: add `classification: str` and `justification: str` as required args to `delegate_worker` schema** | β §6.2 item 2 | **H** (structurally impossible to emit marker without dispatch; removes the "marker-then-orient" pattern mechanically) | **H** (directly targets MoE chatbot-mode; the model cannot emit the classification as free-floating text and stop — the classification only exists as a `delegate_worker` arg) | **M–L** (schema edit + check.py rewrite of first-line regex gate; HERMES.md rewrite of the classification section; one-shot workflow needs a different emission path) | **High.** Changes the existing one-shot workflow (need a separate `emit_classification` tool for one-shot cases, or the classification becomes implicit-none for non-dispatch turns). Breaks the "marker is a text prefix" contract. Reversible via git but touches multiple files. | R1 becomes moot after this; ε still complements |

### 4.3 System prompt layer

| Fix | Source | Dense first-attempt | MoE first-attempt | Cost | Risk | Stacks with |
|-----|--------|---------------------|-------------------|------|------|-------------|
| **ζ-R2: remove the five escape hatches from HERMES-variantD.md (L82, L140–145, L153–157)** | ζ §3 | **M–H** (closes the dense "take the legitimate exit" path; dense's Trial 9 re-classify loop quotes these exact clauses back) | L (MoE already treats correction as directive; not obvious the text-side hatches help MoE) | S (text edits in one file) | **Medium.** Removes protection against over-dispatch on genuinely one-shot tasks. Need one-shot regression check (Tasks 1–3, 7–8) in the same probe. | η-C2, ζ-R1 |
| **ζ-R3: add three more worked examples (bug-hunt, long-horizon plan-only, discovery)** | ζ §4 | L–M (additive; helps only if model was borderline) | L | S (insert ~40 lines in HERMES.md) | Low. Content inflation pushes other content further into the attention valley. | Anything; additive only |
| **ζ-R4: reorder sections so HOW TO DISPATCH WORKERS moves from middle to last** | ζ §5, α H2 | L–M (attention-end bias is model-family-dependent on Gemma; ζ rates this highest-uncertainty) | L | S (section move in one file) | Low. | Weakly with α's E1 |
| **α-E1: replace `PLATFORM_HINTS["cli"]` with a dispatch reminder in the recency slot** | α §6 H1, §7 E1 | L–M (recency-zone occupancy) | L | S (one-line Python edit in `run_agent.py`) | Low. | ζ-R4, α-E2 |
| **α-E2: move HERMES.md from Slot 9 to Slot 4** | α H1 | L–M | L | M (prompt-builder reorder; may interact with SOUL.md identity) | Medium. Untested interaction with persona. | α-E3 |
| **α-E3: trim skills index** | α H3 | L–M (reclaims ~10 KB, pulls HERMES.md 30% closer to start) | L | S (config override or prune) | Low. | α-E1, α-E2 |

### 4.4 Correction layer

| Fix | Source | Dense first-attempt | MoE first-attempt | Cost | Risk | Stacks with |
|-----|--------|---------------------|-------------------|------|------|-------------|
| **η-C2: remove escape clause from NO_DISPATCH correction** | η §2, γ §5.3 | **H** on **final dispatch** (not first-attempt — this is a retry-layer fix) | Neutral (MoE already 5/5 on retry) | S (wrapper script edit + variant-env-var plumbing per η §5) | **Medium.** If dense cannot dispatch on the task, it now has no text-valid exit and may emit malformed JSON or stall. But stall is already the current failure mode — so no net regression risk. | ζ-R2 (text-HERMES.md aligned with correction text) |
| **η-C3: pre-built skeleton / fill-in-the-blank correction** | η §2 | M–H on final dispatch | Neutral | S | High. Risk model strips scaffolding or outputs the literal `YOUR_GOAL_HERE`. Needs parser tolerance check. | η-C2 if stacked |
| **γ suggestion: wrapper edits session JSON to remove model's prose close before re-prompt** | γ §7.3 | H on final dispatch | Neutral | **M** (session JSON mutation inside wrapper — net-new capability) | Medium-high. Mutating session JSON from outside Hermes is tricky; race with session persistence. | η-C2 |
| **Specific-tool-naming in correction ("your use of `skill_manage` was a role-collapse violation")** | γ §7.2 item 2 | M on final dispatch | Neutral | S (wrapper logic to detect the triggering tool) | Low. | η-C2 |

### 4.5 Architecture layer

| Fix | Source | Dense first-attempt | MoE first-attempt | Cost | Risk | Stacks with |
|-----|--------|---------------------|-------------------|------|------|-------------|
| **β-fuse (see 4.2 for schema-layer framing): fuse classification INTO delegate_worker as required args** | β §6.2 item 2 | **H** | **H** | **L** (multi-file: schema, HERMES.md, check.py, wrapper) | High. Touches all four layers at once, including check.py's first-line regex gate. | Replaces ζ-R1 and ζ-R2 when deployed; ε still complements |
| **γ §7.1 item 1b: runtime tool-hiding — hide `write_file`, `patch`, `skill_manage`, `execute_code`, `terminal` until `delegate_worker` has been called when class is structured/LH** | γ §7.1 item 1 | **H** | M (hides the pre-dispatch-mutation path MoE trial 6 took) | **L** (Hermes source patch: requires classification state tracked by runtime; gate on tool availability) | Medium-high. Net-new runtime state. Reversible via git. | ε-T1 provides the same effect *statically* for a single session; γ's version is dynamic per-turn |
| **ε-T1: toolset restriction `-t delegation,todo,clarify,file_readonly` statically at session start** | ε §2, δ §6 | **H** (predicted 3–4/5 by ε; δ confirms same direction with independent reasoning) | M (MoE still emits no-tool sometimes; restriction doesn't fix chatbot-mode, but may reduce the attractor surface for the write_file variant) | S (one toolset dict entry + wrapper flag) | Low. Read-only orientation still possible; no mutation path exists. `git checkout` reversible. | δ-reorder (trivially; list shrinks from 29 to ~5–6), ζ-R1 (complementary surface), η-C2 (complementary channel) |
| **ε-T2: dispatch-only `-t delegation,clarify`** | ε §3 | H — ceiling fix (model has nothing else to reach for) | H — same reasoning | S (CLI flag only) | Medium. Removes orientation; model may hallucinate unavailable tools (`tool_not_found`). Informative either way. | — |
| **ε-T3: surgical removal of the five role-collapse attractors, keep default breadth elsewhere** | ε §4 | M (more distractors remain than T1) | M | M (new compound toolset in toolsets.py) | Low. Production-ready candidate. | — |

---

## 5. Interaction matrix

Shorthand: `+` = stacks well, `=` = redundant / one masks the other, `–` = conflicts, `.` = orthogonal.

|                         | δ-reorder | δ-remove dt | ε-T1 | ε-T2 | ε-T3 | ζ-R1 | ζ-R2 | ζ-R3 | ζ-R4 | α-E1 | η-C2 | η-C3 | β-fuse | γ runtime-hide |
|-------------------------|-----------|-------------|------|------|------|------|------|------|------|------|------|------|--------|-----------------|
| δ-reorder               | —         | +           | =    | =    | +    | +    | .    | .    | .    | .    | .    | .    | =      | =               |
| δ-remove delegate_task  | +         | —           | .    | .    | +    | +    | .    | .    | .    | .    | .    | .    | =      | .               |
| ε-T1 (restricted toolset)| =        | .           | —    | –    | –    | =    | +    | +    | +    | +    | +    | +    | +      | =               |
| ε-T2 (dispatch-only)    | =         | .           | –    | —    | –    | =    | +    | +    | +    | +    | +    | +    | +      | =               |
| ε-T3 (remove offenders) | +         | +           | –    | –    | —    | +    | +    | +    | +    | +    | +    | +    | +      | =               |
| ζ-R1 (schema imperative)| +         | +           | =    | =    | +    | —    | +    | +    | +    | .    | +    | +    | =      | +               |
| ζ-R2 (remove escapes)   | .         | .           | +    | +    | +    | +    | —    | +    | +    | +    | +    | +    | +      | +               |
| ζ-R3 (worked examples)  | .         | .           | +    | +    | +    | +    | +    | —    | +    | .    | +    | +    | +      | +               |
| ζ-R4 (reorder sections) | .         | .           | +    | +    | +    | +    | +    | +    | —    | +    | +    | +    | +      | +               |
| α-E1 (recency swap)     | .         | .           | +    | +    | +    | .    | +    | .    | +    | —    | +    | +    | +      | +               |
| η-C2 (remove esc clause)| .         | .           | +    | +    | +    | +    | +    | +    | +    | +    | —    | +    | +      | +               |
| η-C3 (skeleton)         | .         | .           | +    | +    | +    | +    | +    | +    | +    | +    | +    | —    | +      | +               |
| β-fuse (classification) | =         | =           | +    | +    | +    | =    | +    | +    | +    | +    | +    | +    | —      | =               |
| γ runtime-hide          | =         | .           | =    | =    | =    | +    | +    | +    | +    | +    | +    | +    | =      | —               |

### Key interactions / decision implications

1. **ε-T1 / ε-T2 / ε-T3 are mutually exclusive** at experiment time — they are three tiers of the same dimension. Run T1 first per ε's own sequencing. The T1-vs-T3 decision is about production shipping (T3) vs hypothesis isolation (T1); they should not both run in the same trial.

2. **ε-T1 masks ζ-R1.** If you restrict the toolset AND rewrite the schema, a positive result can't attribute lift to either change. ζ-R1's schema rewrite operates on a tool description the model reads at selection time; if only 5 tools are visible, the ζ-R1 rewrite may not even be read in its "FIRST tool call MUST be" context. **Run ε-T1 alone first, then decide.** If ε-T1 lands ≥4/5 dispatch, ζ-R1 is redundant; if ε-T1 lands at 2–3/5, layer ζ-R1 on top to push higher.

3. **β-fuse makes ζ-R1 and ζ-R2 moot.** If the schema requires `classification` as a required argument, and check.py enforces "structured → delegate_worker required," then the escape clauses in HERMES.md either disappear or become purely advisory. β-fuse also makes δ-reorder and δ-remove delegate_task redundant (classification is fused into the one tool that matters). β-fuse does NOT make ε-T1 moot — narrower tool surface and classification-fusion are orthogonal (you can run β-fuse with a narrow or broad toolset).

4. **δ-reorder (`delegate_worker` → index 0) alone is cheap insurance.** It doesn't fix the problem by itself (tool competition is about schema dominance, not just position), but it is a 1-line patch that stacks positively with every other fix in the matrix. Recommend landing it unconditionally before any experiment; it removes one confound.

5. **γ-runtime-hide and ε-T1 converge on the same mechanism** (hide non-dispatch mutating tools) but at different times: ε is a static session-start decision; γ is per-turn dynamic gating. For probe trials ε is cheaper and sufficient. For production shipping γ is more flexible (allows orientation reads then blocks mutations until dispatch happens), which handles tasks that genuinely need main-session orientation.

6. **η-C2 and ζ-R2 should ship together.** They are the same rule at different layers (wrapper correction vs HERMES.md text). Shipping one without the other creates an inconsistency the dense model will detect and exploit (cite the HERMES.md escape clause to argue against the stricter correction text).

7. **α-E1 is orthogonal to everything.** The platform-hint swap is cheap enough to stack unconditionally. It is not load-bearing (will not by itself fix dispatch) but it reclaims the single highest-attention slot in the prompt for a dispatch reminder at zero marginal cost.

---

## 6. Experiment ladder (ranked)

Each experiment specifies: fix, expected directional delta vs baseline, trials / wall-clock, confirm/deny criterion, branch-on-result.

Baseline: dense 1/5 first-attempt on N=5 structured/LH; dense 2/5 final. MoE 0/5 first-attempt; MoE 5/5 final. Any single-number threshold applies to the pooled rate across Tasks 4, 6, 9 (the three tasks where dense's first-attempt dispatch failure is most diagnostic; Task 5 is ambiguous SIGTERM-fallback, Task 10 is long-horizon retry-rescue).

### E1 — ε-T1 restricted toolset (dense)

- **Fix:** `-t delegation,todo,clarify,file_readonly` via wrapper flag + one-line `toolsets.py` entry for `file_readonly`.
- **Expected delta:** first-attempt 1/15 → ≥6/15 (dense pooled over 3 tasks × 5 trials each). ε predicts 3–4/5 per task.
- **Cost:** ~5 min `toolsets.py` edit + 5 min wrapper clone, 15 trials × ~4 min = ~60 min wall-clock. **Total: ~75 min.**
- **Confirm:** pooled ≥ 6/15 (≈40%) first-attempt dispatch AND no new failure mode dominates (e.g. `tool_not_found` hallucinations < 3/15).
- **Deny:** pooled ≤ 3/15 first-attempt, OR ≥ 5/15 `tool_not_found` events (model hallucinating unavailable tools, which would mean disposition dominates tool competition).
- **Branch on confirm:** run E2 (ε-T3 production config validation at ~20-tool surface); if T3 holds ≥ 5/15 ship T3 as Gemma-default.
- **Branch on deny:** run E3 (ε-T2 dispatch-only) as disposition confirmation. If T2 also fails, disposition is the issue and move to β-fuse (E6). If T2 passes but T1 didn't, the `read_file`/`search_files` surface is specifically triggering orientation — in that case combine T1 + ζ-R1 to forbid reads in the schema (E4).

### E2 — ε-T3 surgical offender removal (dense)

- **Fix:** new `hermes-cli-no-offenders` compound toolset: default minus `terminal`/`process`/`write_file`/`patch`/`execute_code`/`skill_manage`, keep `read_file`/`search_files`/browser/web/etc.
- **Expected delta:** first-attempt ≈ 4/15 (ε predicts 3/5 per task).
- **Cost:** 15 trials ~60 min + 10 min toolset setup. **Total: ~70 min.**
- **Confirm:** pooled ≥ 5/15 first-attempt.
- **Deny:** < 4/15.
- **Branch on confirm:** ship T3 as production config; then run ζ-R1/η-C2 on top for residual lift.
- **Branch on deny:** the distractor surface (browser/web/memory) matters on top of the attractor list; revert to T1 as shipped config.

### E3 — ε-T2 dispatch-only (dense)

- Only runs if E1 denied.
- **Fix:** `-t delegation,clarify`.
- **Expected delta:** 5/5 dispatch per task (15/15 pooled) OR stall/hallucinate.
- **Cost:** ~60 min.
- **Confirm dispatches at 5/5 per task:** problem was tool competition; revert to T1 or T3 for production.
- **Deny (hallucinate / stall):** disposition is the issue; escalate to β-fuse (E6) or γ-runtime-hide.

### E4 — ζ-R1 schema rewrite (dense) — only if E1 partial

- **Fix:** rewrite `delegate_worker.py` description per ζ §2; extend forbidden list to `read_file`, `search_files`. Hermes runtime restart.
- **Expected delta:** first-attempt ≥ 6/15 (ζ predicts lift from 1/5 to ≥ 3/5 per task).
- **Cost:** ~60 min.
- **Confirm:** ≥ 6/15.
- **Deny:** < 4/15 — move to E5 (R1 + ε-T1 stacked).

### E5 — η-C2 remove escape clause + ζ-R2 align HERMES.md (dense + MoE regression check)

- **Fix:** wrapper `correction_for()` NO_DISPATCH case replaced with η-C2 text (no "re-classify to one-shot" clause); HERMES-variantD.md L82 / L140–157 trimmed per ζ-R2. Ship both together to prevent rule/correction inconsistency.
- **Expected delta:** final dispatch on dense 2/5 → ≥ 4/5 (γ's Trial 9 re-classify loop blocked); MoE unchanged at 5/5 final.
- **Cost:** ~30 min edits + 10 dense trials + 5 MoE trials = ~75 min.
- **Confirm:** dense final ≥ 4/5 AND MoE final ≥ 4/5 AND one-shot regression (Tasks 1–3, 7–8) remains ≥ 4/5 COMPLIANT per model.
- **Deny:** dense final < 3/5 OR one-shot regression (model over-dispatches on one-shot tasks).
- **Branch on deny:** softer version — keep η-C2 but not ζ-R2 (the wrapper is stricter than the text, dense argues from text but loses the argument).

### E6 — β-fuse structural (dense + MoE)

- **Fix:** add `classification` and `justification` as required args on `delegate_worker` schema; amend HERMES.md classification section to instruct marker-via-delegate_worker for structured/LH, text-marker for one-shot only; update `check.py` first-line gate to accept either pattern.
- **Expected delta:** dense first-attempt 1/15 → 10/15 (β-fuse directly eliminates the "marker then orient" shape for dense); MoE first-attempt 0/15 → 10/15 (directly eliminates the "marker then stop" shape for MoE).
- **Cost:** ~3–4 hrs implementation + probe runs = ~5 hrs total.
- **Confirm:** ≥ 10/15 first-attempt per model AND one-shot regression OK.
- **Deny:** dense < 8/15 OR MoE < 8/15.
- **Branch:** this is endgame; if it confirms, β-fuse is the shipped architecture and lower-layer fixes become optional polish.

### E7 — δ-reorder + δ-remove delegate_task (both models)

- **Fix:** 1-line patch to tool-binding `sorted()` to promote `delegate_worker` to index 0 + remove `delegate_task` from the bound tools for the Gemma model path.
- **Expected delta:** +1/15 to +3/15 on dense first-attempt (δ's evidence is positional; small but real). MoE: L–M (doesn't help if MoE emits no tool).
- **Cost:** ~20 min patch + 60 min trials = ~80 min.
- **Confirm:** first-attempt ≥ baseline + 2.
- **Deny:** no change.

### E8 — α-E1 recency-zone dispatch reminder (both models)

- **Fix:** replace `PLATFORM_HINTS["cli"]` with dispatch reminder in `run_agent.py`.
- **Expected delta:** L–M. Cosmetic but cheap.
- **Cost:** ~10 min edit + 60 min trials = ~70 min.

### Ranking by expected impact × ease (recommended running order)

1. **E1 — ε-T1 restricted toolset (dense)** — highest expected lift per hour of work. Reversible. Confirms or rules out the dominant hypothesis in <90 min.
2. **E7 — δ-reorder + δ-remove delegate_task** — cheap insurance; can be landed alongside E1 without confounding (both work at the tool-binding layer, and the toolset restriction already removes `delegate_task` as part of its effect).
3. **E5 — η-C2 + ζ-R2 escape-clause removal** — complements E1 on the final-dispatch dimension.
4. **E6 — β-fuse structural** — endgame. Run only after E1/E5 measured and if results plateau below target.
5. **E2, E3, E4, E8** — conditional / branches of above.

---

## 7. Structural nuclear option evaluation — β-fuse

β's proposal to fuse classification INTO `delegate_worker` as required args is architecturally the cleanest answer. It addresses the root failure mode in both models at once:

- **Dense's "role collapse via orientation"** happens because the marker is a free-floating text prefix; dense can emit the marker and then emit any tool. Fuse classification into the tool call and the marker-with-no-dispatch state becomes representationally impossible for structured/LH classes.
- **MoE's "chatbot-mode end-of-turn after marker"** happens for the same structural reason: the marker is a complete text turn in MoE's RLHF prior. Fuse classification into the tool call and the end-of-turn-after-classification-label pattern is broken — there is no free-floating label to terminate on.

**But:** the cost is not trivial. Concretely β-fuse requires:

1. **Schema change in `variants/hermes/delegate_worker.py`** — add `classification` (enum: structured | long-horizon) and `justification` (string) as required args. ~10 lines.
2. **`probe-variantE-check.py` gate logic rewrite** — the current first-line regex gate (`^\[TASK CLASS:`) has to remain for one-shot (no dispatch emitted) but add a second path: "for structured/LH, the classification may appear as the `classification` arg of the first `delegate_worker` call instead of the first-line marker." ~30 lines.
3. **HERMES-variantD.md rewrite of the classification contract** — the "First-Line Output Contract" section (HERMES.md L7–28) becomes a two-path contract: one-shot emits text marker, structured/LH emits classification via `delegate_worker`. ~40 lines of rewriting.
4. **Wrapper correction text rewrite** — NO_DISPATCH correction becomes "your first tool call MUST be `delegate_worker(classification=..., justification=..., goal=...)`". ~1 case body.
5. **Documentation ripple** — variant DESIGN.md updates, PROBE-RESULTS rewrites, the README's contract section.

**Premature or correct endgame?** Correct endgame. Not premature as an eventual goal; premature as the FIRST experiment. Two reasons:

- **Measurement risk.** β-fuse addresses four layers of problem simultaneously. If it lands, you can't tell which layer was the dominant blocker. Running ε-T1 first gives you an attribution of the tool-competition layer specifically. If ε-T1 alone lands ≥4/5 dispatch, β-fuse is over-engineered for the problem.
- **Reversibility pressure.** β-fuse requires 4+ file changes across 3 subsystems (schema, check script, HERMES.md, wrapper). Each cross-subsystem commit multiplies rollback complexity. Cheaper single-layer fixes should be exhausted first.

**Recommendation.** Treat β-fuse as the committed endgame goal — write the implementation spec, design the schema, draft the check.py gate logic now while the context is fresh. But DO NOT implement it until E1/E5 data is in. The reason is not skepticism of β's analysis (it is sound), it is that the cheaper fixes may render β-fuse unnecessary for the dense model and a 2-layer version of β-fuse (schema-only, no check.py change) may suffice for MoE.

Specifically, if E1 + E5 together land dense at ≥ 4/5 first-attempt and ≥ 4/5 final and MoE at ≥ 3/5 first-attempt (≥ 4/5 final), β-fuse shifts from "required" to "optional polish." If after E1 + E5 either model remains ≤ 2/5 first-attempt, β-fuse becomes the next-step mandatory intervention.

---

## 8. Dense vs MoE differentiated targeting

β's diagnosis — two models, two failure modes — is the most operationally important finding in the whole worker set.

**Dense failure mode: role-collapse-via-orientation.** Dense always emits some tool on msg1 (5/5). The tool is almost always read-only orientation (`terminal`, `search_files`, `read_file`). Dense's msg1 template is reliable: marker → "I'll orient…" preamble → orientation tool call. Root cause per γ: dense's comprehension of the dispatch rule is intact; dense's compliance disposition is to exercise the legitimate "re-classify to one-shot" or "quick orientation read" escape when its prior tension is resolved by avoiding dispatch.

**Interventions that target dense:**
- ε-T1 / ε-T2 / ε-T3 — remove or restrict orientation tools, forcing dense to dispatch or stall. **High expected impact on dense.**
- ζ-R1 — schema-level imperative with "FIRST tool call MUST be delegate_worker" and extended forbidden list (including reads). **High expected impact on dense.**
- ζ-R2 + η-C2 — close the escape clauses in both HERMES.md and the correction text. **Medium-high impact, specifically on retry-rescue since first-attempt is already mostly failing.**
- γ runtime tool-hiding — dynamic version of ε-T1. **High impact, higher implementation cost.**

**MoE failure mode: chatbot-mode / no-tool-emission.** MoE on 3/5 structured/LH trials emits no tool call at msg1. The message terminates cleanly at the end of the justification via end-of-turn token, or on Task 10 appends an explicit chatbot-style menu asking the user what to do next. Root cause per β H1 / H4: Gemma MoE was post-trained on data where classification-like outputs were end-of-turn events (chat-style labeling); emitting the classification label IS the turn in MoE's prior.

**Interventions that target MoE:**
- β-fuse — required-args classification fused into delegate_worker makes "emit marker, end turn" structurally impossible. **High expected impact on MoE** — this is the one intervention that mechanically eliminates the chatbot-mode failure.
- ζ-R1 schema-level "FIRST tool call MUST be delegate_worker" — some effect on MoE because it propagates into the function-calling head's prior, but MoE's failure is at a different decode step (end-of-turn token selection after the marker), not tool-selection.
- HERMES.md addition of an explicit "do not end the turn after the TASK CLASS marker" rule (β §6.2 item 1) — directly addresses the end-of-turn prior. Medium-high expected impact on MoE. **Worth doing independently of β-fuse.**

**Interventions that target BOTH:**
- ε-T1 — restricted toolset. Reduces the attractor surface for dense (orientation tools gone); reduces the attractor surface for MoE's Trial 6 pre-dispatch write_file variant. Doesn't directly fix MoE's chatbot-mode on Tasks 4, 10, but removes an adjacent failure mode.
- α-E1 — recency-zone reminder. Low-cost ambient priming for both models.
- η-C2 — mostly improves dense final; MoE already at ceiling on final. Not targeted at MoE, but no regression risk.

**Interventions that are weakly dense-only or MoE-only:**
- η-C3 skeleton correction — would help MoE's 5/5 retry rescue remain clean under stricter corrections; neutral for dense's compliance issue.

**Dual-arm experiment design.** Any experiment that changes a system-level knob (schema, toolset, correction text) should be run on BOTH dense and MoE. The cost is ~2× but the comparison data is essential — a fix that lifts dense to 5/5 and drops MoE to 3/5 final is a regression for the combined scorecard even if it looks great on dense alone. Given MoE probe wall-clock is ~28 min for 10 trials vs dense ~67 min, doubling to both models per experiment costs ~90 min extra per experiment and is worth it.

---

## 9. Specific next action — committed thresholds

### The one experiment to run first

**Run ε Tier-1 restricted toolset on Gemma-4-31B dense and Gemma-4-26B-A4B MoE over probe Tasks 4, 6, 9, N=5 per task per model.** 30 trials total.

### Exact change

1. **Edit `toolsets.py` on ubuntu-vm** to add one dict entry:
   ```python
   "file_readonly": {
       "description": "Read-only file access: read and search, no write/patch",
       "tools": ["read_file", "search_files"],
       "includes": [],
   },
   ```
   (Inserted alphabetically among atomic toolsets; no other edits.)

2. **Clone `probe-variantE-wrapper.sh` → `probe-variantE-restricted-wrapper.sh`** (preserves the r7.2 baseline wrapper for reference). In the clone, add one CLI flag to the `hermes chat` invocation:
   ```bash
   -t delegation,todo,clarify,file_readonly
   ```
   This replaces the default `hermes-cli` toolset. Keep every other wrapper behavior (TIMEOUT=900, session-ID fallback, correction text) identical to the r7.2 baseline — no other variables.

3. **No changes to** HERMES-variantD.md, delegate_worker.py, check.py, correction text, or any other file. This experiment is designed to be a clean single-variable test of the tool-surface hypothesis.

### Exact probe scope

- Tasks: 4 (refactor auth module — structured), 6 (export feature — long-horizon), 9 (Jira cron silent failure — structured). These are the three structured/LH tasks where both models reliably fail to first-dispatch AND where dense role-collapses (Task 6: write_file, Task 9: skill_manage) — they should benefit most from tool restriction.
- N: 5 trials per task per model. 30 trials total.
- Models: `gemma-4-31b-it-4bit` and `gemma-4-26B-A4B-it-MLX-8bit` sequentially (dense first per budget reasons; if dense fails the committed threshold you may skip MoE and jump to E3).
- Skip: Tasks 5 (SIGTERM-fallback confound), Task 10 (long-horizon retry-rescue success is already 1/1 dense, 1/1 MoE — low information), and one-shot Tasks 1–3, 7, 8 (they would confirm no regression but the toolset restriction doesn't touch their execution — file_readonly permits all one-shot flows).

### Exact pass/fail threshold — committed in advance

Pooled across the three tasks × 5 trials = 15 trials per model. First-attempt dispatch = `tool_calls[0].function.name == "delegate_worker"` in the parent session JSON msg1 (strict persisted-JSON criterion, same as drift-step-A retally).

**Dense pass threshold:** **≥ 7/15 first-attempt dispatch** (≈47%, a 4× lift over the 1/15 baseline). Choosing 7 rather than 6: ε predicts 3–4/5 per task, which floors at 9/15. 7/15 is ε's floor minus 2 trials of stochastic variance.

**MoE pass threshold:** **≥ 4/15 first-attempt dispatch.** MoE's current 0/15 baseline is harder to lift because the failure is chatbot-mode, not wrong-tool. 4/15 represents a directional confirmation that restricted toolset helps MoE at all; higher lift would require β-fuse.

**Secondary pass requirements (both models):**
- No more than 3/15 trials emit `tool_not_found` hallucinations (indicating disposition dominates tool-surface).
- No tripwire mutations (SKILL.md, useDashboard.ts, jira-briefing.sh) — since the toolset cannot call `skill_manage`/`patch`/`write_file`, this must be 0/30 by construction. If any tripwire moves, flag as harness bug.
- One-shot regression spot-check: run ONE one-shot trial (Task 1 or Task 8) per model under the restricted toolset to confirm one-shot still COMPLIANTs. 2 extra trials, ~5 min total.

### Maximum runtime budget

- Setup (toolsets.py edit + wrapper clone): 15 min.
- Dense 15 trials @ avg 4 min/trial = 60 min.
- MoE 15 trials @ avg 3 min/trial = 45 min.
- One-shot spot-check: 2 trials × 2 min = 4 min.
- Results tally + judge turn: 20 min.
- **Total budget: 2.5 hours.** Hard stop at 3 hours.

### What to do if pass

Both models pass: promote restricted toolset to a candidate production config. Run E2 (ε-T3 surgical offender removal) on the full 10-task suite to find the minimum-impact production config. Do NOT ship T1 directly — its breadth restriction breaks browser/web tasks that one-shot Tasks might need. T3 is the production-ready version.

Dense passes, MoE fails (or vice versa): the failure modes are confirmed distinct per β. Ship T1 for dense as Gemma-dense profile; escalate to β-fuse or γ runtime-hide for MoE.

### What to do if fail

Both models fail (< threshold): run E3 (ε-T2 dispatch-only) as disposition sanity check. If T2 also fails, disposition dominates and β-fuse becomes the next-step mandatory intervention. If T2 passes, T1's `read_file`/`search_files` surface specifically was the attractor — combine T1 + ζ-R1 for E4.

Dense fails but tool-not-found > 3/15: tool-restriction lever is working mechanically (model is trying to reach forbidden tools) but disposition runs deeper. Escalate to γ-runtime-hide (dynamic gating with clear error messages) or β-fuse.

---

## 10. Longer-term roadmap

### If E1 (ε-T1) succeeds

1. **E2 (ε-T3 surgical).** ~75 min. Validates a production-ready config with broader surface.
2. **E7 (δ-reorder).** ~80 min. Bakes in 1-line insurance change; co-shipped with T3.
3. **E5 (η-C2 + ζ-R2).** ~75 min. Closes escape clauses for residual lift on final-dispatch and to prevent HERMES.md / correction drift.
4. **E8 (α-E1).** ~70 min. Recency-zone dispatch reminder; cosmetic but free.
5. **Ship as r7.3 config:** T3 toolset + δ-reorder + η-C2 + ζ-R2 + α-E1. Full probe sweep. If dense first-attempt ≥ 4/5 and MoE first-attempt ≥ 3/5, declare r7.3 shippable.

### If E1 fails

1. **E3 (ε-T2 dispatch-only).** ~60 min. Disposition confirmation.
2. **E6 (β-fuse).** ~5 hrs. Structural endgame. This is where the project goes if cheap fixes plateau.
3. Before β-fuse: **β §6.2 item 1 — add "do not end the turn after TASK CLASS marker" rule to HERMES.md** and test on MoE specifically. ~30 min trial cost; may rescue MoE chatbot-mode without requiring full β-fuse.

### If E6 (β-fuse) succeeds

β-fuse becomes the shipped architecture for r8. r8 deprecates the free-floating text marker contract for structured/LH. HERMES.md classification section rewritten. check.py dual-path gate. The whole harness is more robust because the contract is now schema-enforced rather than text-format-enforced.

### Durable project-level action (regardless of E1 outcome)

- **Write β-fuse's implementation spec now**, while the worker context is fresh and the schema design is clean in β's artifact. Do NOT implement it yet. This is risk insurance against losing the design if E1 succeeds and the project deprioritizes β-fuse — when β-fuse becomes needed for the next round of lift (e.g., r7.4 when the ceiling is hit), the spec is ready.
- **Fix the probe wrapper fallback-recovery bug** (r7.2 dense v2 §10.3: when the primary `session_id:` regex misses AND a child dispatch happened, the wrapper picks the child as the parent). This is orthogonal to all remediation but would have prevented the Trial 5 ambiguity and should be fixed before the next probe run.
- **Document the two failure modes** (dense role-collapse-via-orientation; MoE chatbot-mode) as first-class behavioral profiles in the variant DESIGN.md. Future variant tuning should target both explicitly.

---

## 11. Scope-check verdict

Every fix proposed above touches only:

- `variants/hermes/HERMES-variantD.md` (ζ-R2, ζ-R3, ζ-R4)
- `variants/hermes/delegate_worker.py` (ζ-R1, β-fuse schema)
- `probe-variantE-wrapper.sh` (η-C2, η-C3, ε-T1/T2/T3 flag plumbing)
- `probe-variantE-check.py` (β-fuse gate logic only; no other experiment touches it)
- `toolsets.py` on ubuntu-vm (`file_readonly` entry for ε-T1; `hermes-cli-no-offenders` for ε-T3)
- `run_agent.py` on ubuntu-vm (α-E1 platform hint swap; α-E2/E3 prompt reorder)
- Tool-binding code on ubuntu-vm (δ-reorder, δ-remove delegate_task)

No recommendation touches:
- `core/` or `core/harness-core.md` or `core/permissions.md`
- `references/` or any reference document
- `playbooks/` or any scenario playbook
- `templates/` or any harness template
- `evaluation/` or golden tasks
- `MEMORY.md` or user-profile files
- Any non-Hermes variant (none exist in the repo but flagging for completeness)

Cross-model integrity: every experiment on the ladder runs on both dense and MoE OR explicitly justifies a single-model run. No fix optimizes for one model at the cost of regressing the other. The differentiated-targeting analysis (§8) enforces this at the design stage, not at deployment.

**Scope-check: PASS.**

---

## Appendix — Key source file paths

- Live HERMES variant D: `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantD.md` (md5 `4477b8ee1d87c3a3afa9e8646168841f` — staged on ubuntu-vm)
- delegate_worker schema: `/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker.py` (lines 20–50 description block)
- Wrapper: `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh` (md5 `9fd987c5e18e6aa70a05426c473fc0a3`; correction text lines 80–116)
- Toolsets (remote only): `/home/parallels/.hermes/hermes-agent/toolsets.py`
- Prompt builder (remote only): `/home/parallels/.hermes/hermes-agent/run_agent.py` lines 2582–2745
- Baseline artifacts:
  - `/Users/briantaylor/Projects/AgentFW/ARTIFACT-drift-step-a-retally.md`
  - `/Users/briantaylor/Projects/AgentFW/ARTIFACT-probe-r7.2-dense-v2.md`
  - `/Users/briantaylor/Projects/AgentFW/ARTIFACT-probe-r7.2-moe.md`
- Worker artifacts:
  - α: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-remediation-worker-alpha-prompt-anatomy.md`
  - β: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-remediation-worker-beta-first-turn.md`
  - γ: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-remediation-worker-gamma-retry-divergence.md`
  - δ: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-remediation-worker-delta-tool-surface.md`
  - ε: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-remediation-worker-epsilon-toolset-restriction.md`
  - ζ: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-remediation-worker-zeta-prompt-rewrites.md`
  - η: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-remediation-worker-eta-correction-rewrites.md`

End of artifact.
