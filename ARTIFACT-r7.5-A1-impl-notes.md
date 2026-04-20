# ARTIFACT-r7.5-A1-impl-notes.md

**Worker:** r7.5 Workstream A.1 — Hermes-side conditional toolset binding
**Status:** DONE
**Return date:** 2026-04-19
**VM state at return:** CANONICAL (all probe patches unstaged, tripwires intact)

---

## Summary

Installed an r7.5-A1 **turn-0 toolset restriction hook** in `~/.hermes/hermes-agent/run_agent.py` on ubuntu-vm. When a session is running with the EXACT β-fuse probe toolset (`delegation,todo,clarify,file_readonly`) AND no assistant message in the in-progress `api_messages` has called `delegate_worker_v2`, the Hermes agent filters `self.tools` down to `{delegate_worker_v2, clarify}` BEFORE sending the tool schema to the LLM. Once any prior assistant turn has emitted a `delegate_worker_v2` tool_call (successful OR errored), the full declared toolset is bound for subsequent turns.

The restriction is **narrowly scoped to the β-fuse toolset composition** — any other `enabled_toolsets` (e.g. canonical `hermes-cli` used by cron / hermes-telegram / interactive CLI) bypasses the hook entirely and receives the unchanged `self.tools` list. The comparison is order-insensitive (frozenset equality against `{"delegation", "todo", "clarify", "file_readonly"}`).

Closes the dense `todo`/`search_files` escape route observed in r7.4 Phase D.

---

## Mac artifacts (created)

| File | md5 | Notes |
|------|-----|-------|
| `/Users/briantaylor/Projects/AgentFW/probe-variantG-stage.sh` | `913330e89b8f01c78cc975cf34154cf8` | Stage/unstage/status. `.probe-r7.5-orig` backup suffix. Idempotent. Layers ON TOP of variantF — see coordination below. |
| `/Users/briantaylor/Projects/AgentFW/probe-variantG-check.py` | `e1edfd538bd4a384595ef9c8da2dcff1` | Header-only diff vs variantF; gate logic IDENTICAL (intentional — B2 will add WRONG_SESSION verdict later). Note: this file was externally edited post-creation to extend the header with B2's planned WRONG_SESSION verdict documentation; the extra documentation does not change gate behavior. md5 at worker-return reflects the post-edit state. |
| `/Users/briantaylor/Projects/AgentFW/probe-variantG-wrapper.sh` | `42b51b4c1dbd7f87aa53b4e9e49a5982` | Wrapper parallels variantF's; `SOURCE_PREFIX=probe-r7.5-varG`, points at variantG check + `/tmp/probe-variantG-check.py` remote. Was externally edited post-creation to make `TIMEOUT_PER_TURN` env-overridable (for B1 compatibility); the functional turn-0/retry loop is unchanged. |

All three are `chmod +x`.

---

## VM patches

**File:** `~/.hermes/hermes-agent/run_agent.py`
**Backup:** `run_agent.py.probe-r7.5-orig` (created on first stage; coexists with `.probe-r7.4-orig` and `.probe-d-orig`)
**Idempotency marker:** the string `_resolve_tools_for_turn_r75a` appears exactly 3 times when staged (method definition + 2 call sites), 0 times when unstaged.

### Patch 1 — new method (inserted directly before `def _build_api_kwargs`)

```python
_BETA_FUSE_TOOLSET_SET = frozenset({"delegation", "todo", "clarify", "file_readonly"})
_BETA_FUSE_TURN0_ALLOWED = frozenset({"delegate_worker_v2", "clarify"})

def _resolve_tools_for_turn_r75a(self, api_messages):
    """Return possibly-restricted tool list for the current turn.

    If self.enabled_toolsets is exactly the β-fuse probe set and no
    assistant message in api_messages has yet called delegate_worker_v2,
    restrict to {delegate_worker_v2, clarify}. Otherwise return self.tools.
    Defensive: if the filtered result is empty (e.g. v2 not in tools
    because variantF was not staged), falls back to self.tools rather
    than starving the model of tools.
    """
    tools = self.tools
    if not tools:
        return tools
    enabled = getattr(self, "enabled_toolsets", None)
    if not enabled:
        return tools
    if frozenset(enabled) != self._BETA_FUSE_TOOLSET_SET:
        return tools
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
    if v2_called:
        return tools
    restricted = [
        t for t in tools
        if isinstance(t, dict)
        and (t.get("function") or {}).get("name") in self._BETA_FUSE_TURN0_ALLOWED
    ]
    return restricted if restricted else tools
```

### Patch 2 — anthropic-branch call site (inside `_build_api_kwargs`)

```diff
- tools=self.tools,
+ tools=self._resolve_tools_for_turn_r75a(api_messages),
```

### Patch 3 — OpenAI-branch call site (inside `_build_api_kwargs`)

```diff
- if self.tools:
-     api_kwargs["tools"] = self.tools
+ _resolved_tools_r75a = self._resolve_tools_for_turn_r75a(api_messages)
+ if _resolved_tools_r75a:
+     api_kwargs["tools"] = _resolved_tools_r75a
```

**Why `_build_api_kwargs`:** it is the single per-turn function that builds the LLM API request, has access to both `self.tools` AND the live `api_messages`, is invoked once per assistant turn, and covers both active API modes (anthropic_messages and OpenAI-compatible). All 4 other `_build_api_kwargs` call sites in run_agent.py automatically inherit the hook (memory-tool path, codex path, retry path).

**Why class constants as attributes:** declaring `_BETA_FUSE_TOOLSET_SET` / `_BETA_FUSE_TURN0_ALLOWED` as class-level attributes (not module globals) ensures they're scoped to the AIAgent class, avoids polluting run_agent module namespace, and makes them trivially accessible to the instance method.

**Why `frozenset(enabled) != _SET` (not list comparison):** `enabled_toolsets` is parsed via `[t.strip() for t in toolsets.split(",")]`, which preserves order. Using frozenset equality makes the check order-insensitive, so operators invoking `-t "clarify,file_readonly,delegation,todo"` (same set, different order) still trigger the hook.

---

## Stage/unstage procedure

### Stage (order matters — variantF FIRST)

```bash
./probe-variantF-stage.sh stage   # adds delegate_worker_v2 tool + registrations
./probe-variantG-stage.sh stage   # adds turn-0 restriction hook on top
```

### Unstage (reverse order)

```bash
./probe-variantG-stage.sh unstage   # restores run_agent.py.probe-r7.5-orig
./probe-variantF-stage.sh unstage   # restores *.probe-r7.4-orig backups
```

### Status

```bash
./probe-variantG-stage.sh status   # also reports whether variantF appears staged
./probe-variantF-stage.sh status
```

Both stage scripts are idempotent. Re-running `stage` when already staged is a no-op (checked via unique marker grep).

---

## Verification

All verification performed with VM in `variantF+variantG STAGED` state.

### Unit tests (hook logic in isolation)

Extracted the method + class vars via AST and ran 7 isolated test cases:

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
| 1 | β-fuse set, no v2 called | restrict to `{clarify, delegate_worker_v2}` | PASS |
| 2 | β-fuse set, v2 already called | full 7 tools | PASS |
| 3 | `["hermes-cli"]` toolset | full 7 tools (hook skipped) | PASS |
| 4 | β-fuse set reordered (`file_readonly,clarify,todo,delegation`) | restrict (order-insensitive) | PASS |
| 5 | empty `self.tools` | `[]` | PASS |
| 6 | β-fuse + tools list missing v2 but has clarify | `[clarify]` (non-empty so returned) | PASS |
| 7 | β-fuse + tools list missing BOTH v2 and clarify | fallback to full self.tools (defensive) | PASS |

### Live Hermes invocation

Direct `hermes chat` invocations with tracing instrumentation temporarily added:

**Turn-0 trace (single-turn greeting):**
- Command: `hermes chat -m gemma-4-31b-it-4bit -t delegation,todo,clarify,file_readonly --max-turns 1 -Q -q "hello" --source r7.5-A1-trace`
- Session ID: `20260419_172341_a7fc03`
- Stderr trace: `[R75A_TRACE] enabled=['delegation', 'todo', 'clarify', 'file_readonly'] v2_called=False bound_names=['clarify', 'delegate_worker_v2']`
- **Verdict: hook fires, turn 0 bound to exactly 2 tools.**

**Multi-turn trace (task requiring tool use):**
- Command: `hermes chat ... --max-turns 5 -q "Please classify this task then proceed: read the first line of /etc/hostname..."`
- Session ID: `20260419_172523_ea97c8`
- Method was invoked 5 times (one per API turn). First call printed the restricted path trace; remaining 4 calls short-circuited (v2_called=True after turn 0). Assistant emitted `delegate_worker_v2` first (as required); downstream turns used `read_file` (which requires the full toolset — confirming the expansion worked).

**Final clean-state verify (no instrumentation):**
- Command: `hermes chat ... --max-turns 1 -Q -q "hello" --source r7.5-A1-verify-clean`
- Session ID: `20260419_172709_d99e17`
- Session JSON's top-level `tools` field: 7 tools declared (persisted as the AGENT-level tool set, not the per-turn filtered set). This is a Hermes design limitation — see Gotchas below.

### Tool-array persistence limitation

**Key finding for downstream workers:** Hermes persists the full AGENT-level `self.tools` array at session creation in the session JSON's top-level `tools` field. The per-turn filtered tool list (what we actually send to the LLM) is NOT recorded in the session JSON. There is no per-turn `tools` snapshot.

Implication for verification: you cannot inspect the session JSON to prove the hook fired on turn N. The evidence lives only in:
1. What the LLM *chose* to call on each turn (assistant message `tool_calls` list) — indirect but useful signal.
2. The effective tool-call signature per the Hermes log (also indirect).
3. Instrumentation (add a stderr print in the method; see this artifact's verification section for the procedure).

For r7.5-A3 judge / future analyses: the primary evidence for turn-0 restriction working is the absence of non-`{delegate_worker_v2, clarify}` tool_calls in the FIRST assistant message across a probe run. If the model emits `todo` / `search_files` / `read_file` as its first tool_call under variantG, the hook failed.

### Canonical tripwires at return

All three tripwires verified at canonical md5 at return time:

```
0780c232a6cb52e13e432261f0d68ad9  HERMES.md
fb1a5a5208a6cf2fcb8252aac10397eb  SKILL.md
a1dce6e989527686124d0860830627c9  jira-briefing.sh
```

---

## Gotchas for downstream workers

### For B1 (wrapper SIGTERM mitigations)

- `probe-variantG-wrapper.sh` was externally edited after my initial write to make `TIMEOUT_PER_TURN` env-overridable via `: "${TIMEOUT_PER_TURN:=900}"`. Build your SIGTERM work on top of that.
- Source prefix is `probe-r7.5-varG`; artifact log files land at `/tmp/probe-r7.5-varG-run${N}-{wrapper.log,stdout.txt}`.
- The wrapper's session-id fallback recovery (primary regex miss → source-tag scan → most-recent) is unchanged from variantF. SIGTERM scenarios that need to reliably attach to the PARENT session should consider adding a `--session-id-hint` flag plumbed to check.py (B2's WRONG_SESSION verdict is the backstop).
- Check script is uploaded idempotently to `/tmp/probe-variantG-check.py` (via md5 compare) at trial start.

### For B2 (WRONG_SESSION verdict in check.py)

- `probe-variantG-check.py` already has the WRONG_SESSION verdict in its header documentation (added via external edit post-creation). Gate logic is identical to variantF. You still need to IMPLEMENT the `--expected-prompt-prefix` CLI arg parsing and the `ERROR:WRONG_SESSION` verdict emission — those aren't in the code yet, only documented.
- The existing argparse structure uses `if len(sys.argv) != 2: print("ERROR:USAGE"); return 1`. You'll need to convert that to real argparse with a positional `session_path` and optional `--expected-prompt-prefix`.
- When adding the WRONG_SESSION check, the parent-session heuristic is: the session's `messages[0]` (role=user) `content` field must start with the expected trial prompt prefix. If it starts with something else (e.g. a dispatched goal string), emit `ERROR:WRONG_SESSION` and let the wrapper handle it.

### For Phase 3+ smoke-test worker

- Stage order is critical: **variantF FIRST, variantG SECOND.** Unstage in reverse.
- The variantG stage script's `status` subcommand reports whether variantF appears staged — if the state is "VARIANT-G STAGED BUT VARIANT-F NOT STAGED", the probe will fail immediately because `delegate_worker_v2` won't be registered as a tool (so the restricted turn-0 binding will be `[clarify]` only, and the model will have no dispatch path).
- `timeout` on the ssh-wrapped hermes invocation sometimes kills the session before the session_id marker flushes to stdout — the wrapper's source-tag fallback scan handles this (unchanged from variantF).
- The `unhashable type: 'slice'` error observed in my verification runs is a PRE-EXISTING variantF issue (reproduces identically with variantG unstaged), NOT caused by this worker's patch. It appears to occur in the `delegate_worker_v2` tool handler itself during certain MLX / OpenAI-compatible API responses. Operator should file this separately — out of scope for r7.5-A1.

### For operators running canonical workloads concurrently

- The hook is guarded on `enabled_toolsets == {"delegation","todo","clarify","file_readonly"}` (exact set equality, order-insensitive). Canonical `hermes-cli` / cron / hermes-telegram toolsets do NOT match this, so the hook is a no-op for them.
- However, if you happen to invoke `hermes chat -t delegation,todo,clarify,file_readonly` for non-probe purposes while variantG is staged, you WILL get the turn-0 restriction. Keep this in mind — stage only during probe windows.

---

## Design deviations from the brief

1. **Hook location:** The brief suggested `toolsets.py`. I placed the hook in `run_agent.py`'s `_build_api_kwargs` instead, because that's the unique per-turn site where both `self.tools` and `api_messages` are simultaneously in scope. `toolsets.py` resolves tool definitions at AGENT INIT time (via `get_tool_definitions`), before any conversation exists, so the in-session inspection required by the brief ("check whether v2 has been called") is simply unavailable there. The brief explicitly allowed this fallback decision ("if plumbing the conversation state is invasive, fall back...") — here it's the natural, non-invasive choice.
2. **No env-var / filesystem marker fallback used.** The brief offered a filesystem-marker fallback "if plumbing the conversation state is invasive." Plumbing turned out to be trivial (it was already plumbed), so I did the proper in-session inspection.
3. **No modifications to `toolsets.py` or `model_tools.py`.** The hook is entirely localized to `run_agent.py`. Stage script therefore patches only one file, keeping the footprint minimal and the r7.5-A1 change easily auditable.

---

## File pointers

- Stage: `/Users/briantaylor/Projects/AgentFW/probe-variantG-stage.sh`
- Check: `/Users/briantaylor/Projects/AgentFW/probe-variantG-check.py`
- Wrapper: `/Users/briantaylor/Projects/AgentFW/probe-variantG-wrapper.sh`
- This file: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.5-A1-impl-notes.md`
- Related (frozen): `/Users/briantaylor/Projects/AgentFW/probe-variantF-*.sh`, `probe-variantF-check.py`, `variants/hermes/delegate_worker_v2.py`, `variants/hermes/HERMES-variantF.md`
