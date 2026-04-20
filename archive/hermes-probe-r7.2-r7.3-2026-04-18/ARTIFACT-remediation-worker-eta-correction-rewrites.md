# Worker η — Correction-Message Rewrites for Dense Retry-Success Lift

**Scope:** Design-only. Propose rewrites to `correction_for()` in `probe-variantE-wrapper.sh` that plausibly move dense 2/5 → 5/5 without regressing MoE 5/5.

**Source read:** `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh` lines 80-116.

---

## 1. Current correction text audit

### `VIOLATION:NO_DISPATCH:structured|long-horizon`
Current text (paraphrased): ~90 words, 4 sentences, 2 paragraphs, with a 3-line tool-call template, plus a negative-list clause ("Do not call patch, write_file, terminal, execute_code, or skill_manage..."), plus an escape-hatch clause ("If you truly believe dispatch isn't warranted, re-classify to `one-shot`...").

**Weak spots for dense:**
- **Buried imperative.** The actual action ("Output the tool call now") is in the middle, sandwiched between policy justification ("HERMES.md requires...") and constraints ("Do not call patch..."). Dense models appear to attention-collapse on the first clause and miss the action.
- **Escape hatch is prominent.** The re-classify-to-one-shot option is the last sentence — recency-weighted. A dense model under pressure is likely to take the exit rather than complete the harder action. This is probably *the* lift lever.
- **Tool-call template is schematic, not scaffolded.** The `"goal": "your complete self-contained task description including..."` is a description-of-what-to-fill-in, not a fill-in-the-blank with a clear slot token. Dense may treat it as prose and not copy the JSON envelope.
- **No acknowledgment of what the model just did.** The correction is generic to the class; it doesn't quote back the model's own (wrong) first action. That costs engagement.

### `VIOLATION:ROLE_COLLAPSE:structured|long-horizon`
Current text: similar shape, ~75 words. Leads with the diagnosis ("That's role collapse. HERMES.md forbids..."), then the imperative, then the template.

**Weak spots:**
- Same buried-imperative and unscaffolded-template issues as NO_DISPATCH.
- Phrase "Stop the main-session work" is ambiguous — does the model interpret this as "stop producing output" (it does, sometimes) vs "stop using main-session tools for this task"?
- No escape hatch here (good), but also no acknowledgment of what learnings to pass forward into the goal.

### `VIOLATION:NO_MARKER`
One sentence, clear imperative. Probably already adequate — dense failures on this are likely rarer.

### `VIOLATION:FABRICATION`
Offers a two-branch choice ("either retry, or state explicitly not complete"). For a dense model this is probably fine; for our retry-exhaustion pattern this isn't the primary failure mode.

### `VIOLATION:NO_ASSISTANT_RESPONSE` and default
Short. Adequate.

**Focus of rewrites:** NO_DISPATCH and ROLE_COLLAPSE. These are the dense killers.

---

## 2. Variant C1–C4 — exact rewrite text

### Variant C1 — Shorter + imperative (lead with action, cut justification)

**NO_DISPATCH:**
```
DISPATCH NOW. Your next response must contain exactly this tool call with the goal string filled in to describe your task:

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "<your task, self-contained: what to do, which files, what done looks like>"}}
</tool_call>

Emit no other tool. No prose before the tool call.
```

**ROLE_COLLAPSE:**
```
DISPATCH NOW. You already ran main-session mutation tools — stop and hand the rest to a worker. Your next response must contain exactly this tool call with the goal string filled in, including everything you have learned so far:

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "<task + findings so far + next steps>"}}
</tool_call>

Emit no other tool. No prose before the tool call.
```

### Variant C2 — Remove escape hatch (force dispatch-or-error)

**NO_DISPATCH:**
```
You classified this task as structured or long-horizon and did not dispatch. That is a protocol violation. The only valid next response is a delegate_worker tool call in this exact format:

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "<your self-contained task description>"}}
</tool_call>

Do not re-classify. Do not explain. Do not call any other tool. Emit the tool call now.
```

**ROLE_COLLAPSE:** same as above, preceded by one sentence: `You already used main-session mutation tools. Stop. Dispatch now.`

### Variant C3 — "Complete this output for me" (pre-built skeleton)

**NO_DISPATCH:**
```
Your next response MUST begin with exactly the following lines, replacing ONLY the string YOUR_GOAL_HERE with a 2-3 sentence description of the task. Every other character is fixed.

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "YOUR_GOAL_HERE"}}
</tool_call>

Do not add any text before the <tool_call> line. Do not add any text after the </tool_call> line. Do not change the JSON keys or structure. Replace YOUR_GOAL_HERE only.
```

**ROLE_COLLAPSE:**
```
Your next response MUST begin with exactly the following lines, replacing ONLY the string YOUR_GOAL_HERE with a 2-3 sentence description of the task AND any findings from your partial work so far. Every other character is fixed.

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "YOUR_GOAL_HERE"}}
</tool_call>

Do not add any text before or after the tool call. Replace YOUR_GOAL_HERE only.
```

### Variant C4 — Cite-evidence-then-dispatch (force contract engagement)

**NO_DISPATCH:**
```
You violated HERMES.md role-separation. Do exactly two things, in order, in your next response:

1. Quote the exact line from HERMES.md that says structured/long-horizon tasks must dispatch a worker.
2. Immediately after the quote, emit this tool call with goal filled in:

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "<your self-contained task>"}}
</tool_call>

Nothing else. No classification marker, no explanation, no other tools.
```

**ROLE_COLLAPSE:** same structure with "Quote the HERMES.md line that forbids main-session mutation before dispatch" as step 1.

---

## 3. Effectiveness scoring matrix

Rough priors; dense = gemma-4-31b-it-4bit, MoE = gemma-4-26B-A4B-it-MLX-8bit.

| Variant | Expected dense lift (from 2/5) | Expected MoE maintain (from 5/5) | New failure-mode risk |
|---|---|---|---|
| **C1 — shorter + imperative** | +1 to +2 (→ 3/5–4/5). Helps because the imperative is front-loaded. Keeps escape hatch absent, reduces token count. | High — MoE already complies; shorter text doesn't hurt it. | Low. Worst case: model emits tool-call without surrounding prose, which is what we want. |
| **C2 — remove escape hatch** | +2 to +3 (→ 4/5–5/5). The escape hatch is the most likely culprit; removing it forces the correct action. | High. | Medium. A dense model that *couldn't* dispatch (e.g., truly mis-classified) now has no way out and may emit malformed JSON or stall. But stall is already the failure mode we're fighting, so this doesn't regress. |
| **C3 — pre-built skeleton** | +2 to +3 (→ 4/5–5/5). Reduces the cognitive load to "fill one slot." Very dense-friendly. | High. | Medium-high. Risk that the model *strips the scaffolding* and emits bare JSON without `<tool_call>...</tool_call>` tags, or that it pastes "YOUR_GOAL_HERE" literally. Needs parser tolerance check or an explicit "do not output the literal string YOUR_GOAL_HERE" line. |
| **C4 — cite-evidence-then-dispatch** | +0 to +1 (→ 2/5–3/5). Adds work before the imperative — the opposite of C1. Dense may get stuck on the quote step and never reach dispatch. | Medium-high. MoE can handle the extra step, but it's wasted tokens. | High. The quote step is a distractor; dense may hallucinate the quote or loop. Not recommended as first try. |

---

## 4. First-test recommendation

**Primary: Variant C2** (remove escape hatch). Highest expected lift, smallest change surface. If Worker γ's root-cause diagnosis points at "model takes the exit," C2 is dispositive.

**Secondary / parallel A/B: Variant C3** (pre-built skeleton). Addresses a different failure mode (tool-call envelope malformation) and is orthogonal to C2. Good second arm.

**Skip C1 and C4 for now.** C1 is a watered-down C2; C4 is likely regressive for dense.

Suggested first run: 5 trials dense + 5 trials MoE on C2; if dense hits ≥4/5 without MoE regression, ship C2. If dense is still ≤3/5, run C3 next. If both fail, stack C2+C3 (remove escape hatch AND pre-built skeleton).

---

## 5. Implementation plan — parameterize the wrapper to A/B variants

Goal: swap correction text without editing the main script body for each trial. Two options, preferring option A.

### Option A (recommended): env-var-selected variant, inline case

Add a `CORRECTION_VARIANT` env var read at the top of the script:

```bash
CORRECTION_VARIANT="${CORRECTION_VARIANT:-baseline}"
```

Replace the two heavy cases in `correction_for()` with a nested dispatch:

```bash
"VIOLATION:NO_DISPATCH:structured"|"VIOLATION:NO_DISPATCH:long-horizon")
  case "$CORRECTION_VARIANT" in
    baseline) cat <<'MSGEOF'
<current text>
MSGEOF
      ;;
    C1) cat <<'MSGEOF'
DISPATCH NOW. Your next response must contain exactly this tool call...
MSGEOF
      ;;
    C2) cat <<'MSGEOF'
You classified this task as structured or long-horizon and did not dispatch...
MSGEOF
      ;;
    C3) cat <<'MSGEOF'
Your next response MUST begin with exactly the following lines...
MSGEOF
      ;;
    C4) cat <<'MSGEOF'
You violated HERMES.md role-separation. Do exactly two things...
MSGEOF
      ;;
  esac
  ;;
```

Same pattern for ROLE_COLLAPSE. NO_MARKER / FABRICATION / NO_ASSISTANT_RESPONSE stay unchanged (no variant needed).

**Also stamp the variant into the outcome line** for post-hoc analysis. In the OUTCOME echoes, add `variant=$CORRECTION_VARIANT`:

```bash
echo "OUTCOME run=$RUN_NUM MODEL=$MODEL ... variant=$CORRECTION_VARIANT chain=\"$CHAIN\""
```

Invocation:
```bash
CORRECTION_VARIANT=C2 MODEL=gemma-4-31b-it-4bit ./probe-variantE-wrapper.sh 1 "<task>"
```

Default stays `baseline` so existing scripts don't change behavior.

### Option B: separate wrapper files

Copy `probe-variantE-wrapper.sh` to `probe-variantE-wrapper-C2.sh` etc. Reject: duplicates the harness logic, drift risk, analysis harder.

### Option C: external correction-text file

Put correction templates in `corrections-<variant>.sh` that gets sourced. Cleaner long-term if we expect >4 variants, but overkill for a 2-arm A/B.

**Decision:** go with **Option A**. Minimal diff, one file, variant stamped in outcomes.

### Test-plan notes for the judge / evaluator

1. Run baseline (existing corrections) 5x dense + 5x MoE first to confirm the 2/5 vs 5/5 gap replicates under the current revision.
2. Run C2 5x dense + 5x MoE. Compare retry-success rate and mean-attempts-to-compliance.
3. Verify MoE doesn't regress (5/5 still).
4. If C2 wins, ship it as the new baseline and retire the escape-hatch phrasing from HERMES.md also (optional follow-up — consistency between doc and correction).
5. If C2 doesn't move dense, escalate to C3 (or C2+C3 stacked).
6. Keep the `chain=` trace in OUTCOME so we can see whether the failure mode shifts (e.g., from "no tool call" to "malformed tool call") under each variant — that's informative even when the final rate doesn't change.

### Non-goals / out of scope here

- Changing HERMES.md itself (coordinate with Worker γ's findings first).
- Adding new violation types.
- Changing retry count (`MAX_RETRIES=3`) — variant effectiveness should be measurable within the existing budget.
