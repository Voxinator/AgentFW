[TASK CLASS: structured]
Justification: Fresh-context judge verification of r7.5 Workstream A turn-0 toolset restriction — multi-step verification with side effects (stage/unstage) and a final written verdict artifact.

# ARTIFACT — r7.5 A.2 judge verdict

## Verdict

**ACCEPT.** The hook is present at the claimed location with the claimed semantics, 7/7 AST test cases reproduce the worker's expected outputs against the live class method, and the live probe invocation produced `first_tool == delegate_worker_v2` on turn 0 under the exact β-fuse toolset — confirming the restriction fires end-to-end. VM returned CANONICAL.

---

## Task 1 — Patch target

**VERIFIED.** Before judge work, the VM reported `VARIANT-G UNSTAGED` with `run_agent.py` md5 `94ad8712678df5e96b9f407446edf249`. After staging variantF then variantG, `grep -n "_resolve_tools_for_turn_r75a\|_BETA_FUSE_"` on `~/.hermes/hermes-agent/run_agent.py` returned:

```
5237:    _BETA_FUSE_TOOLSET_SET = frozenset({"delegation", "todo", "clarify", "file_readonly"})
5238:    _BETA_FUSE_TURN0_ALLOWED = frozenset({"delegate_worker_v2", "clarify"})
5240:    def _resolve_tools_for_turn_r75a(self, api_messages):
5257:        if frozenset(enabled) != self._BETA_FUSE_TOOLSET_SET:
5277:            and (t.get("function") or {}).get("name") in self._BETA_FUSE_TURN0_ALLOWED
5293:                tools=self._resolve_tools_for_turn_r75a(api_messages),
5424:        _resolved_tools_r75a = self._resolve_tools_for_turn_r75a(api_messages)
```

Exactly 3 occurrences of `_resolve_tools_for_turn_r75a` (1 definition + 2 call sites). Method lives on class `AIAgent` (declared at line 416). Both class constants present. Stage script status-marker (3 hits) confirmed.

---

## Task 2 — Hook content

Inspected lines 5229–5283 and both call sites. Every claimed behavior verified:

**(a) Guard is frozenset equality against the exact 4-element set (line 5249 and 5257):**
```python
_BETA_FUSE_TOOLSET_SET = frozenset({"delegation", "todo", "clarify", "file_readonly"})
...
if frozenset(enabled) != self._BETA_FUSE_TOOLSET_SET:
    return tools
```
Order-insensitive as claimed (frozenset equality). Other toolsets (e.g. `hermes-cli`) bypass the hook entirely.

**(b) Iterates assistant messages for a v2 tool_call (lines 5261–5272):**
```python
v2_called = False
for m in (api_messages or []):
    if not isinstance(m, dict) or m.get("role") != "assistant":
        continue
    for tc in (m.get("tool_calls") or []):
        fn = (tc.get("function") or {}) if isinstance(tc, dict) else {}
        if fn.get("name") == "delegate_worker_v2":
            v2_called = True
            break
    if v2_called:
        break
```

**(c) Narrows tools when no v2 yet (lines 5274–5278):**
```python
restricted = [
    t for t in tools
    if isinstance(t, dict)
    and (t.get("function") or {}).get("name") in self._BETA_FUSE_TURN0_ALLOWED
]
```

**(d) Defensive fallback when empty (line 5279):**
```python
return restricted if restricted else tools
```
Matches claim. Also the early `if v2_called: return tools` (line 5273) and early `if not tools: return tools` (5245) short-circuit paths are present.

**(e) Called from BOTH branches of `_build_api_kwargs` (class method starting at 5281):**

Anthropic branch (line 5293):
```python
tools=self._resolve_tools_for_turn_r75a(api_messages),
```

OpenAI-compatible branch (lines 5424–5426):
```python
_resolved_tools_r75a = self._resolve_tools_for_turn_r75a(api_messages)
if _resolved_tools_r75a:
    api_kwargs["tools"] = _resolved_tools_r75a
```

All five claimed behaviors verified at source.

---

## Task 3 — Live invocation

**Command:**
```
hermes chat -m gemma-4-26b-a4b-it-mlx-8bit \
  -t delegation,todo,clarify,file_readonly \
  --max-turns 2 -q "what is 2+2?" --source r7.5-A2-judge-verify
```

**HERMES.md pre-swap md5:** `01c0e77bb2a6e753a8ea9063784a25e0` (matches expected variantF hash).

**Session:** `20260419_173212_bc1e3a`
**`first_tool`:** `delegate_worker_v2` ✓
**`classification`:** `one-shot`
**`model`:** `gemma-4-26b-a4b-it-mlx-8bit`
**Declared-tools count in session JSON:** 7 (as expected per known limitation — session persists agent-level list, not per-turn filtered list)

The `delegate_worker_v2` handler itself errored with the known pre-existing `unhashable type: 'slice'` issue (documented as out-of-scope for r7.5-A1 in worker's impl notes). That is irrelevant to the A1 claim — the point of A1 is whether the model's FIRST tool call is v2, which it is. The restriction worked: the model, faced with `{v2, clarify}`, chose v2 (rather than the dense `todo`/`search_files` escape route that motivated r7.5).

---

## Task 4 — Worker's cited sessions

| Session ID | first_tool | classification | model | msgs | Status |
|---|---|---|---|---|---|
| `20260419_172341_a7fc03` | (no tool_calls) | n/a | gemma-4-31b-it-4bit | 2 | Plain-text greeting response to `hello`; no tool call needed. Consistent with worker's description of turn-0 trace with instrumentation. |
| `20260419_172523_ea97c8` | `delegate_worker_v2` | `one-shot` | gemma-4-31b-it-4bit | 6 | Multi-turn task; confirms v2 first, then expansion. Matches worker's claim. |
| `20260419_172709_d99e17` | (no tool_calls) | n/a | gemma-4-31b-it-4bit | 2 | Plain-text greeting. Matches worker's "final clean-state verify (-Q -q hello)". |

All three sessions exist and are consistent with the worker's narrative. The two greeting sessions simply had the model answer without any tool — they don't falsify the restriction (the model was free to call `clarify` but chose plain text). The multi-turn session (`172523_ea97c8`) is the definitive behavioral evidence: first tool call is v2, as required.

---

## Task 5 — AST-style test

Invoked `AIAgent._resolve_tools_for_turn_r75a` directly against the live class method on VM via `venv/bin/python3`, using a duck-typed mock with `_BETA_FUSE_*` constants pulled from `AIAgent`.

**Constants (confirmed):**
- `_BETA_FUSE_TOOLSET_SET`: `{'clarify','delegation','file_readonly','todo'}`
- `_BETA_FUSE_TURN0_ALLOWED`: `{'clarify','delegate_worker_v2'}`

| # | Input | Expected | Observed | Result |
|---|---|---|---|---|
| 1 | β-fuse enabled_toolsets, no v2 in msgs | `[v2, clarify]` | `['delegate_worker_v2','clarify']` | PASS |
| 2 | β-fuse + prior assistant v2 tool_call | full 7 tools | all 7 returned | PASS |
| 3 | `['hermes-cli']` toolset | full 7 tools (hook bypasses) | all 7 returned | PASS |
| 4 | β-fuse reordered `[file_readonly,clarify,todo,delegation]` | `[v2, clarify]` (order-insensitive) | `['delegate_worker_v2','clarify']` | PASS |
| 5 | empty `self.tools` | `[]` | `[]` | PASS |
| 6 | β-fuse; tools list has clarify but no v2 | `[clarify]` (non-empty → returned) | `['clarify']` | PASS |
| 7 | β-fuse; tools missing BOTH v2 and clarify | fallback to full self.tools | `['todo','read_file','search_files']` | PASS |

**7/7 match the worker's claim.** The method behaves exactly as specified, including order-insensitive match and the defensive empty-fallback.

---

## VM state at end

Post-unstage md5s on tripwires:

| Path | Expected | Observed | Match |
|---|---|---|---|
| `~/.hermes/hermes-agent/HERMES.md` | `0780c232a6cb52e13e432261f0d68ad9` | `0780c232a6cb52e13e432261f0d68ad9` | ✓ |
| `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md` | `fb1a5a5208a6cf2fcb8252aac10397eb` | `fb1a5a5208a6cf2fcb8252aac10397eb` | ✓ |
| `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh` | `a1dce6e989527686124d0860830627c9` | `a1dce6e989527686124d0860830627c9` | ✓ |

Additionally, `run_agent.py` md5 restored to pre-judge `94ad8712678df5e96b9f407446edf249`, and `probe-variantG-stage.sh status` reports `VARIANT-G UNSTAGED` with 0 marker hits.

**VM is CANONICAL.** ✓

---

## Issues discovered

1. **[Low / pre-existing, out-of-scope]** The live invocation hit the documented `unhashable type: 'slice'` error in the v2 handler. The worker flagged this as a pre-existing variantF-level bug unrelated to A1 — the error occurs *after* the model has already chosen `delegate_worker_v2` as first tool, so it does NOT impact the A1 restriction verdict. Should be filed separately against variantF.
2. **[Informational]** Session JSON persists only the 7-tool agent-level declared list, not the per-turn filtered schema actually sent to the LLM. The worker correctly flagged this as a known limitation and provided indirect behavioral evidence (which tools the LLM actually chose) as the accepted proxy. Downstream phases should rely on "first tool_call name" as the verification signal.
3. **[None load-bearing]** Two of the three worker-cited sessions (`_a7fc03`, `_d99e17`) were `-q "hello"` greetings where the model returned plain text without any tool_call. This is consistent with the worker's narrative; not evidence of restriction failure (the model was free to call `clarify`, just didn't need to).

No high-severity issues.

---

## Recommendation

**Proceed to Phase 3 integration smoke test.** Workstream A is correctly implemented. The patch is localized, idempotent, stage/unstage-reversible, order-insensitive, and narrowly scoped to the β-fuse toolset (so canonical hermes-cli / cron / telegram workloads are untouched). The 7/7 AST test pass plus the live probe (`first_tool=delegate_worker_v2` on a non-trivial prompt `"what is 2+2?"` under `gemma-4-26b-a4b-it-mlx-8bit`) confirm the restriction fires in both the unit-test and end-to-end paths.

Recommended next steps:
- Proceed to Phase 3 smoke test under variantF+variantG.
- File the pre-existing `unhashable type: 'slice'` bug in the variantF v2 handler as a separate workstream.
- Keep the A1 hook behavior documented as-is; Workstream B (WRONG_SESSION, wrapper SIGTERM) can layer on without modification.
