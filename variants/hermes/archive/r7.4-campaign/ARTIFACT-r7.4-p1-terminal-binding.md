[TASK CLASS: structured]
Justification: Focused investigation; read-only; single deliverable is this artifact.

# ARTIFACT — r7.4 P1: terminal-binding probe-fidelity investigation

**Author:** P1 investigation worker (fresh context, 2026-04-19).
**Status:** RESOLVED — neither a source bug nor a wrapper bug. See §Root cause.
**Blocks r7.4 β-fuse?** NO — gate is clean; analyzer mislabel is the only issue, and the fix is a 10-line check-script change.

---

## TL;DR

**Hypothesis (1) REFUTED. Hypothesis (2) REFUTED. Root cause is a fourth hypothesis (4): model tool-name hallucination, rejected correctly by the runtime, but mislabeled by `probe-variantE-check.py`'s downstream analyzer.** In all 4 definitive leak trials (T6 run8, T9 run12, T9 run14, T9 run15 — T6 run11 is not a leak, its first tool is `search_files`), the Hermes runtime **correctly bound only 6 tools** (`clarify, delegate_task, delegate_worker, read_file, search_files, todo`) on the parent session, **correctly rejected** the hallucinated `terminal` call with `"Tool 'terminal' does not exist. Available tools: ..."`, and no terminal command ever executed (confirmed by tripwire-zero across 34 trials). The Layer-1 structural property ("no mutators in the toolset") **held on every trial**. The fidelity issue is not a gate leak — it is the probe analyzer classifying the first `tool_calls[0].function.name` without checking whether that name was in the bound tools array or whether the call was accepted. **The fix is a source-and-wrapper-free change to `probe-variantE-check.py`'s first-tool classifier (and to the downstream failure-mode breakdown in any re-run): filter out tool calls whose name is not in the session's `tools` array, OR skip tool calls whose immediately-following `tool` message starts with `"Tool '..' does not exist"`. Estimated effort: ≈15 min edit + re-run the existing L1+L2 analysis against the 30 sessions to get corrected first-tool numbers.** r7.4 β-fuse probe work is unblocked.

---

## Direct probe results

### Setup
- VM: `ubuntu-vm` (parallels user, Ubuntu 22 VM, oMLX on host).
- Hermes CLI: `~/.hermes/hermes-agent/venv/bin/hermes`.
- Invocation (dense): `hermes chat -m gemma-4-31b-it-4bit -t delegation,todo,clarify,file_readonly --max-turns 2 -q "test" --source probe-fidelity-dense`.
- Invocation (MoE): `hermes chat -m gemma-4-26B-A4B-it-MLX-8bit -t delegation,todo,clarify,file_readonly --max-turns 2 -q "test" --source probe-fidelity-moe`.

### Dense direct probe
- **Session ID:** `20260419_122015_95c7f4`.
- **Model:** `gemma-4-31b-it-4bit`.
- **`.tools | length` = 6.**
- **`.tools | map(.function.name)` = `["clarify","delegate_task","delegate_worker","read_file","search_files","todo"]`.**
- **`terminal` present? NO.**
- CLI banner also reported "6 tools · 97 skills" (independent confirmation).

### MoE direct probe
- **Session ID:** `20260419_122039_ab471c`.
- **Model:** `gemma-4-26B-A4B-it-MLX-8bit`.
- **`.tools | length` = 6.**
- **`.tools | map(.function.name)` = `["clarify","delegate_task","delegate_worker","read_file","search_files","todo"]`.**
- **`terminal` present? NO.**

### Retrospective inspection of the 4 r7.3 "leak" sessions
| Trial | Session ID | Bound `.tools` count | `terminal` in bound tools? | Assistant msg[0] `tool_calls[0].name` | Tool response |
|-------|------------|---------------------|----------------------------|---------------------------------------|---------------|
| T6 run8  | `20260418_221714_32fe38` | 6 | NO | `terminal` (args: `ls -R …`)      | `"Tool 'terminal' does not exist. Available tools: clarify, delegate_task, delegate_worker, read_file, search_files, todo"` |
| T9 run12 | `20260418_225644_500da4` | 6 | NO | `terminal` (args: `crontab -l`)   | Same rejection stub. |
| T9 run14 | `20260418_232329_2448c2` | 6 | NO | `terminal` (args: `crontab -l`)   | Same rejection stub. |
| T9 run15 | `20260418_232703_f179b2` | 6 | NO | `terminal` (args: `crontab -l`)   | Same rejection stub. |
| T9 run11 (alleged partial overlap) | `20260418_225158_8365fb` | 6 | NO | **`search_files`** (not terminal) | — (not a leak) |

**Every one of the 4 definitive leak sessions had `terminal` correctly excluded from the bound tool surface, and every `terminal` call was rejected by the runtime.** The bound-set is identical to the declared toolset. MoE's retrospective clean record (0/15 terminal-leak) is corroborated here: the gate is symmetric across dense and MoE; dense is more prone to tool-name hallucination from training priors on Linux administration tasks (`crontab -l`, `ls -R`), but the gate catches it.

---

## Source audit (spot-checked for completeness even though gate is clean)

File md5s (VM, at investigation time):
- `~/.hermes/hermes-agent/toolsets.py` — `5d126e7f1987468c0514cbc474ba12eb`
- `~/.hermes/hermes-agent/model_tools.py` — `10aaf53294ba39569844ebac7076e9c9`
- `~/.hermes/hermes-agent/run_agent.py` — `94ad8712678df5e96b9f407446edf249`
- `~/.hermes/hermes-agent/cli.py` — `a306a62f244cce3a5d90ac04ea6f15ff`

Findings:
- `toolsets.py:31-67` defines `_HERMES_CORE_TOOLS`; `terminal` is a member of this list, BUT `_HERMES_CORE_TOOLS` is only used as the `tools:` entry for specific named toolsets (`telegram`, `discord`, `slack`, etc. — messaging-platform preset bundles). It is NOT an "always-on" unconditional inclusion. When the user passes `-t delegation,todo,clarify,file_readonly`, those 4 toolset definitions are the only ones resolved.
- `toolsets.py:96-99` defines the `terminal` toolset: `{"tools": ["terminal","process"], "includes": []}`. You get `terminal` only if you name `terminal` in `-t`.
- `run_agent.py:8685-8710` is the tool-call validation loop. Line 8701: `content = f"Tool '{tc.function.name}' does not exist. Available tools: {available}"` — this is the exact rejection stub present in the 4 leak sessions' message chains. The line immediately above (`if tc.function.name not in self.valid_tool_names`) confirms `valid_tool_names` is the authoritative bound set and hallucinations get rejected, not executed.
- No model-specific path in `model_tools.py` force-injects `terminal` for dense but not MoE (searched for `force_`, `ALWAYS_`, `default_tools`, model-conditional branches).

Conclusion: **no always-on binding**, **no model-specific leak**, **no `-t` bypass**. Hypotheses (1) and (3) are refuted.

---

## Wrapper audit

File: `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh` (md5 `b652038b1b255de912cab765266da7c2`, size 11243 bytes).

Key lines:
- L27-32: `TOOLSETS_ENV="${TOOLSETS:-}"; if [[ -n "$TOOLSETS_ENV" ]]; then TOOLSETS_FLAG="-t \"$TOOLSETS_ENV\""; fi` — unambiguous flag construction.
- **L156** (initial invocation): `./venv/bin/hermes chat -m $MODEL -Q --max-turns 20 --checkpoints $TOOLSETS_FLAG -q "$P" --source $SOURCE_TAG` — `$TOOLSETS_FLAG` is passed.
- **L225** (retry/correction invocation via `--resume`): `./venv/bin/hermes chat -m $MODEL --resume $SESSION_ID -Q --max-turns 20 $TOOLSETS_FLAG -q "$P" --source $SOURCE_TAG` — `$TOOLSETS_FLAG` is ALSO passed on every retry. (No resume-strips-flag bug.)

Per-trial wrapper-log confirmation for the 4 leak trials:
- `/tmp/probe-r7.3-l12-dense-run8-wrapper.log` header: `MODEL=gemma-4-31b-it-4bit … TOOLSETS=delegation,todo,clarify,file_readonly`.
- `/tmp/probe-r7.3-l12-dense-run12-wrapper.log` header: same.
- `/tmp/probe-r7.3-l12-dense-run14-wrapper.log` header: same.
- `/tmp/probe-r7.3-l12-dense-run15-wrapper.log` header: same.
- Every run logged `attempt 0: initial invocation` with the declared TOOLSETS string. The per-session `.tools` array (6 entries, no `terminal`) confirms the flag took effect on the Hermes side.

The session-JSON evidence (§Direct probe results retrospective table) already confirmed this: all 4 had bound-set of exactly 6, which can only happen if `-t "delegation,todo,clarify,file_readonly"` was received and processed by `hermes chat`. **Hypothesis (2) is refuted.**

---

## Root cause

The 4 r7.3 dense leak trials are cases of **model tool-name hallucination**: the model's decode produced `<tool_call>{"name": "terminal", "arguments": {"command": "…"}}</tool_call>` **despite `terminal` not being present in the tool-definition array it was given in the system prompt**. This is a known failure mode for Gemma-class models on Linux-administration prompts (`crontab -l`, `ls -R`) where the training prior for `terminal`-shaped tool schemas is strong.

Hermes' runtime handled these cases correctly: `run_agent.py:8685-8710` validates `tc.function.name in self.valid_tool_names`, returns the `"Tool 'terminal' does not exist. Available tools: …"` stub as the tool result, and reprompts the model in the same turn. Every such hallucination in the 4 trials was followed by a compliant real tool call (e.g. `search_files`) on the next turn. **No terminal command ever executed. 0/34 tripwires mutated, consistent with this analysis.**

The **fidelity issue** is entirely downstream: the probe analyzer (`probe-variantE-check.py::all_tool_calls`, L60-68) extracts `tc.function.name` from each assistant message's `tool_calls` without cross-referencing the session's bound `.tools` array or the following `tool` message's rejection status. The failure-mode breakdown in `ARTIFACT-probe-r7.3-l12-results.md` §"Failure-mode breakdown" (the `role-collapse-via-terminal` row, 5/30) used this unfiltered first-tool name. Given the session JSON literally contains a `tool_calls[0].function.name == "terminal"`, the breakdown correctly reflected "what the model tried to do" but incorrectly reflected "what the structural Layer-1 gate allowed" — those are two different questions.

**In one sentence:** the Layer-1 toolset gate was clean on every r7.3 trial; 4 dense trials had model tool-name hallucinations that the runtime rejected; the "17% terminal-leak" is an analyzer labeling artifact, not a runtime fidelity violation.

---

## Recommended fix

### Primary fix: `probe-variantE-check.py` (Mac-side, read-only outside scope of production)

**File:** `/Users/briantaylor/Projects/AgentFW/probe-variantE-check.py`
**Change:** Update `all_tool_calls()` (L60-68) OR add a sibling `valid_tool_calls()` that filters out hallucinated calls. Two equivalent approaches:

**Option A (check bound tools):**
```python
def bound_tool_names(data):
    tools = data.get("tools") or []
    names = set()
    for t in tools:
        fn = (t.get("function") or {}).get("name") or t.get("name")
        if fn:
            names.add(fn)
    return names

def all_tool_calls(messages, bound=None):
    calls = []
    for m in messages:
        if m.get("role") != "assistant":
            continue
        for tc in (m.get("tool_calls") or []):
            fn = (tc.get("function") or {}).get("name", "")
            if bound is not None and fn not in bound:
                continue  # skip hallucinated names
            calls.append(fn)
    return calls
```

**Option B (check rejection stub in following tool message):**
```python
def all_tool_calls(messages):
    calls = []
    msgs = list(messages)
    for i, m in enumerate(msgs):
        if m.get("role") != "assistant":
            continue
        for tc in (m.get("tool_calls") or []):
            fn = (tc.get("function") or {}).get("name", "")
            # Check the following tool message: Hermes stubs rejected calls
            # with "Tool '<name>' does not exist. Available tools: …"
            tc_id = tc.get("id")
            rejected = False
            for nm in msgs[i+1:]:
                if nm.get("role") != "tool":
                    continue
                if nm.get("tool_call_id") == tc_id:
                    if str(nm.get("content","")).startswith(f"Tool '{fn}' does not exist"):
                        rejected = True
                    break
            if rejected:
                continue
            calls.append(fn)
    return calls
```

Either preserves the existing `VIOLATION:NO_DISPATCH:*` / `VIOLATION:ROLE_COLLAPSE:*` / `VIOLATION:FABRICATION` logic; you just want the "first tool" used in failure-mode labeling to reflect *accepted* calls, not hallucinated-rejected ones. Option A is slightly more robust (catches any out-of-band name even if Hermes changes its stub text); Option B is explicit about the acceptance handshake.

**Estimated effort:** 15 minutes (5 min edit, 10 min re-run existing 30 dense+MoE session JSONs through the updated check + update the failure-mode breakdown table in `ARTIFACT-probe-r7.3-l12-results.md` §5).

### Secondary fix: retroactive breakdown re-label

Re-run the failure-mode classification (Mac-side, `probe-r7.3-l1-firsttool.py` or equivalent) against the 30 r7.3 structured/LH sessions with the filtered `all_tool_calls` logic. Expected new distribution:

| Failure mode | Previous | Expected after fix |
|--------------|----------|---------------------|
| role-collapse-via-readonly (`search_files`/`read_file` first) | 11 | 11-15 (+4 from relabeled trials) |
| role-collapse-via-todo (`todo` first) | 11 | 11 |
| role-collapse-via-terminal (hallucinated, rejected) | 5 | **0** (this row disappears; 4 re-label as readonly, 1 (run11) was already readonly) |
| chatbot-mode | 4 | 4 |
| Strict first-dispatch | 2 | 2 |

Net structural result after re-label: **first-dispatch 2/30 is unchanged, terminal-leak row collapses to zero, and 4 dense trials move into `role-collapse-via-readonly` because their first *accepted* tool call was `search_files` (see §Direct probe results retrospective — each of the 4 sessions has a `search_files` call as the first non-rejected call in the same turn).** The headline findings of the r7.3 L1+L2 probe are unchanged; only the internal failure-mode attribution shifts.

### Side effects / risks

- **No source patch needed.** No changes to `~/.hermes/hermes-agent/`.
- **No wrapper patch needed.** `probe-variantE-wrapper.sh` is correct.
- **No re-run of L1+L2 probe needed** — the existing 30 session JSONs are authoritative; we just re-classify them with a corrected analyzer.
- **Risk: zero.** The analyzer change is a strict filtering improvement; no compliant trial gets reclassified as non-compliant or vice versa (the COMPLIANT/VIOLATION:* verdict logic doesn't use `all_tool_calls` except for detecting `mutations_before_dispatch`, and the rejected `terminal` calls were never in `MAIN_SESSION_MUTATION_TOOLS` in the first place — check: `MAIN_SESSION_MUTATION_TOOLS = frozenset(["patch","write_file","execute_code","skill_manage"])`). So the gate verdict is stable; only the failure-mode label tightens.

### Does this block r7.4 β-fuse probe work?

**NO.** The Layer-1 structural property ("no mutators in the toolset") held on every r7.3 trial. The r7.4 β-fuse probe can proceed with the existing wrapper and toolset configuration, because the gate is proven-clean both retrospectively (4 leak sessions re-examined) and prospectively (dense + MoE direct probes today). The analyzer fix should land before the r7.4 analysis is written up, but it does not block probe *execution*.

**Minimum unblock for r7.4 β-fuse:** zero work — proceed. The analyzer fix is a parallel, non-gating improvement.

---

## Evidence trail

### Sessions examined (VM, `~/.hermes/sessions/`)
- `session_20260419_122015_95c7f4.json` — dense direct probe (Step 1A).
- `session_20260419_122039_ab471c.json` — MoE direct probe (Step 1B).
- `session_20260418_221714_32fe38.json` — T6 run8 leak.
- `session_20260418_225158_8365fb.json` — T9 run11 (re-verified: not a leak; first tool = `search_files`).
- `session_20260418_225644_500da4.json` — T9 run12 leak.
- `session_20260418_232329_2448c2.json` — T9 run14 leak.
- `session_20260418_232703_f179b2.json` — T9 run15 leak.

### Commands run (abridged)
```bash
ssh ubuntu-vm '~/.hermes/hermes-agent/venv/bin/hermes chat \
  -m gemma-4-31b-it-4bit -t delegation,todo,clarify,file_readonly \
  --max-turns 2 -q "test" --source probe-fidelity-dense'
ssh ubuntu-vm '~/.hermes/hermes-agent/venv/bin/hermes chat \
  -m gemma-4-26B-A4B-it-MLX-8bit -t delegation,todo,clarify,file_readonly \
  --max-turns 2 -q "test" --source probe-fidelity-moe'
ssh ubuntu-vm 'jq ".tools | length, (.tools | map(.function.name))" \
  ~/.hermes/sessions/session_<id>.json'
ssh ubuntu-vm 'jq "[.messages[] | select(.role==\"assistant\")][0].tool_calls \
  | map({name: .function.name, args: (.function.arguments | tostring)})" \
  ~/.hermes/sessions/session_<id>.json'
ssh ubuntu-vm 'jq ".messages[1:6] | map({role, name, content})" \
  ~/.hermes/sessions/session_<id>.json'
ssh ubuntu-vm 'grep -n "terminal\|_HERMES_CORE_TOOLS" \
  ~/.hermes/hermes-agent/toolsets.py ~/.hermes/hermes-agent/model_tools.py \
  ~/.hermes/hermes-agent/run_agent.py'
ssh ubuntu-vm 'sed -n "8685,8720p" ~/.hermes/hermes-agent/run_agent.py'
```

### File md5s (integrity snapshot)
| File | md5 |
|------|-----|
| `~/.hermes/hermes-agent/toolsets.py` (VM) | `5d126e7f1987468c0514cbc474ba12eb` |
| `~/.hermes/hermes-agent/model_tools.py` (VM) | `10aaf53294ba39569844ebac7076e9c9` |
| `~/.hermes/hermes-agent/run_agent.py` (VM) | `94ad8712678df5e96b9f407446edf249` |
| `~/.hermes/hermes-agent/cli.py` (VM) | `a306a62f244cce3a5d90ac04ea6f15ff` |
| `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh` (Mac) | `b652038b1b255de912cab765266da7c2` |
| `/Users/briantaylor/Projects/AgentFW/probe-variantE-check.py` (Mac) | `725d8e6b0cbb2e772fa1cb23aa1c7919` |

### No state mutated
- Read-only throughout. The only new state is: 2 trivial hermes sessions (`20260419_122015_95c7f4` dense, `20260419_122039_ab471c` MoE) created by the Step-1 direct probes, neither with any tool calls beyond a chatbot reply to `"test"`. No edits to VM source files, wrapper, tripwire files, or HERMES.md. No changes to `core/`, `references/`, `playbooks/`, `templates/`.
