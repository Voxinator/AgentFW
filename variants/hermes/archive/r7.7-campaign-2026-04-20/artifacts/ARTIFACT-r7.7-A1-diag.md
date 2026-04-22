---
type: A1 diagnostic (S1)
date: 2026-04-20
campaign: r7.7 Path A
worker: S1
---
# A1 diag — child toolset restriction

## Hypothesis verdict

**H-A1c: CONFIRMED.**

`delegate_task(toolsets=None, ...)` inherits the child's toolset from the parent's resolved toolsets, not from a fresh named default. When the parent's session has `enabled_toolsets=None` (the "all tools enabled" convention), the three-way fallback in `_build_child_agent` derives the child's set from `parent_agent.valid_tool_names` via `model_tools.get_toolset_for_tool`, then strips blocked toolsets (`delegation`, `clarify`, `memory`, `code_execution`). The `todo` toolset is **not** in the blocked list, so a parent whose loaded tools include `todo` propagates `todo` to every child.

H-A1a (fresh-resolved from a named default) is **rejected** — no named child-default toolset is consulted by `delegate_task`; `DEFAULT_TOOLSETS = ["terminal", "file", "web"]` is only a last-resort fallback when the parent exposes neither `enabled_toolsets` nor `valid_tool_names`, which is effectively never for a running AIAgent. H-A1b is **rejected** — `_build_child_system_prompt` deals only with prose, not toolset selection.

Therefore A1 must ship as a wrapper-side patch in `variants/hermes/delegate_worker_v2.py` that computes a restricted set and passes it explicitly as `toolsets=`. Editing `toolsets.py` named sets or `DEFAULT_TOOLSETS` would not affect the inheritance path at all.

## Code trace (file:line-cited)

### Q1 — Does `delegate_task` accept `toolsets=None`? What does the None path do?

`~/.hermes/hermes-agent/tools/delegate_tool.py:510-519`:

```python
def delegate_task(
    goal: Optional[str] = None,
    context: Optional[str] = None,
    toolsets: Optional[List[str]] = None,
    tasks: Optional[List[Dict[str, Any]]] = None,
    ...
) -> str:
```

When single-task mode runs, `delegate_tool.py:561` packs it as `task_list = [{"goal": goal, "context": context, "toolsets": toolsets}]`. In the build loop `delegate_tool.py:594` passes `toolsets=t.get("toolsets") or toolsets` into `_build_child_agent`. So a `None` propagates into `_build_child_agent` unchanged.

Inside `_build_child_agent` (`delegate_tool.py:196-249`), the `None` path is NOT a "resolve from named default" — it's an inheritance path (H-A1c). See Q2.

### Q2 — Three-way fallback: `enabled_toolsets → valid_tool_names → DEFAULT_TOOLSETS`

`delegate_tool.py:223-249` is the canonical resolution. It actually has two nested three-way structures — first deriving `parent_toolsets`, then picking `child_toolsets`:

```python
# delegate_tool.py:228-239 — derive parent_toolsets
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

# delegate_tool.py:241-249 — pick child_toolsets
if toolsets:
    child_toolsets = _strip_blocked_tools([t for t in toolsets if t in parent_toolsets])
elif parent_agent and parent_enabled is not None:
    child_toolsets = _strip_blocked_tools(parent_enabled)
elif parent_toolsets:
    child_toolsets = _strip_blocked_tools(sorted(parent_toolsets))
else:
    child_toolsets = _strip_blocked_tools(DEFAULT_TOOLSETS)
```

Branch trigger conditions:

1. `toolsets` is truthy → child gets intersection with parent (caller-supplied path). This is the path A1 will use.
2. `toolsets` is None AND `parent_enabled is not None` → child inherits parent's explicit list verbatim, blocked-stripped.
3. `toolsets` is None AND `parent_enabled is None` AND parent has `valid_tool_names` → child gets all toolsets derivable from parent's loaded tool names (reverse-mapped via `model_tools.get_toolset_for_tool`, `~/.hermes/hermes-agent/model_tools.py:562-564`).
4. Everything falls through → `DEFAULT_TOOLSETS = ["terminal", "file", "web"]` (`delegate_tool.py:40`), blocked-stripped.

`_strip_blocked_tools` (`delegate_tool.py:108-113`) removes exactly four toolsets: `{"delegation", "clarify", "memory", "code_execution"}`. `todo` is NOT stripped — this is the hole.

### Q3 — End-to-end toolset resolution when `delegate_worker_v2` calls `delegate_task(toolsets=None, ...)`

`variants/hermes/delegate_worker_v2.py:139-148` (repo, staged onto VM):

```python
return delegate_task(
    goal=goal,
    context=None,
    toolsets=None,          # ← None propagates
    tasks=None,
    max_iterations=None,
    acp_command=None,
    acp_args=None,
    parent_agent=parent_agent,
)
```

Trace with a typical probe-variantF parent (`hermes-cli` toolset, interactive CLI):

1. `delegate_task` at `delegate_tool.py:510` receives `toolsets=None`.
2. At `delegate_tool.py:594` it forwards `toolsets=None` into `_build_child_agent`.
3. In `_build_child_agent`, `parent_enabled = parent.enabled_toolsets`. For a CLI session launched with `--toolset hermes-cli`, this is the resolved list of enabled toolsets for the `hermes-cli` named alias, which includes `todo` (via `_HERMES_CORE_TOOLS` referenced by `"hermes-cli"` at `~/.hermes/hermes-agent/toolsets.py:294-297`).
4. `toolsets` is falsy AND `parent_enabled is not None` → branch 2 fires: `child_toolsets = _strip_blocked_tools(parent_enabled)`.
5. `todo` survives the strip. Child receives `todo`.

For a parent where `enabled_toolsets is None` (all-tools default), branch 3 fires; `valid_tool_names` for a default-registered CLI agent includes `todo`, which reverse-maps via `get_toolset_for_tool` to the `"todo"` toolset (`~/.hermes/hermes-agent/toolsets.py:167-170`). Same outcome: `todo` reaches the child.

### Q4 — Is `todo` in the default toolset? Minimum viable residual?

`todo` is its own named toolset (`~/.hermes/hermes-agent/toolsets.py:167-170`) with a single tool, `todo`. It is included explicitly in `_HERMES_CORE_TOOLS` (`toolsets.py:50`), `hermes-acp` (`:252`), and `hermes-api-server` (`:278`). So the common parent toolsets all carry it.

After removing `"todo"` from the child-passed list, the residual for a typical `hermes-cli` parent still includes:

- `web`, `search`, `terminal`, `file`, `skills`, `browser`, `session_search`, `vision`, `image_gen`, `tts`, `cronjob` — all propagate verbatim.
- `delegation` → stripped by `_strip_blocked_tools` (prevents grandchild spawn). So `delegate_task` / `delegate_worker` / `delegate_worker_v2` are NOT in the child set. This matches `MAX_DEPTH = 2` at `delegate_tool.py:35`.
- `clarify`, `memory`, `code_execution` → also stripped.

**Correction to the brief's Q4 framing:** the brief asks whether the child will still have `delegate_task` / `delegate_worker` / `clarify`. It will NOT — those toolsets are blocked for children by design (grandchild prevention, no cross-session UI). The minimum viable residual is `read_file`, `search_files`, `write_file`, `patch`, `terminal`, `process`, `web_search`, `web_extract`, and `session_search`. That is sufficient for a structured worker; removing `todo` specifically removes only the fabrication-substrate surface.

## Patch sketch

### Helper

```python
# variants/hermes/delegate_worker_v2.py (new, near top after imports)

import os

# Mirror delegate_tool.py's last-resort default. Must stay in sync with
# ~/.hermes/hermes-agent/tools/delegate_tool.py:40.
_DEFAULT_TOOLSETS_FALLBACK = ["terminal", "file", "web"]

# Toolsets to strip from child when A1 restriction is active.
_A1_FABRICATION_SUBSTRATE = frozenset({"todo"})


def _resolve_parent_toolsets(parent_agent):
    """Mirror the three-way fallback in delegate_tool.py:228-239.

    Returns a list of toolset names representing the parent's effective
    toolset surface, in the same semantics delegate_task would derive if
    given toolsets=None.
    """
    if parent_agent is None:
        return list(_DEFAULT_TOOLSETS_FALLBACK)
    parent_enabled = getattr(parent_agent, "enabled_toolsets", None)
    if parent_enabled is not None:
        return list(parent_enabled)
    valid = getattr(parent_agent, "valid_tool_names", None)
    if valid:
        try:
            import model_tools
            derived = {
                ts for name in valid
                if (ts := model_tools.get_toolset_for_tool(name)) is not None
            }
            if derived:
                return sorted(derived)
        except Exception:
            pass
    return list(_DEFAULT_TOOLSETS_FALLBACK)


def _derive_restricted_child_toolset(parent_agent):
    """A1: parent's resolved toolsets minus fabrication substrate (todo).

    Idempotent: if the parent's set already excludes todo, the result is
    identical (sans any reordering from _resolve_parent_toolsets).
    Non-expansive: the intersection logic in delegate_tool.py:242-243 will
    still clip anything we return to the parent's surface, so a stale/larger
    return value cannot accidentally grant the child extra tools.
    """
    resolved = _resolve_parent_toolsets(parent_agent)
    return [t for t in resolved if t not in _A1_FABRICATION_SUBSTRATE]
```

### Updated invocation in `delegate_worker_v2.py`

Lines 136-148, before:

```python
    # Spawn child via delegate_task internals (same path as legacy
    # delegate_worker).
    return delegate_task(
        goal=goal,
        context=None,
        toolsets=None,
        tasks=None,
        max_iterations=None,
        acp_command=None,
        acp_args=None,
        parent_agent=parent_agent,
    )
```

After:

```python
    # Spawn child via delegate_task internals (same path as legacy
    # delegate_worker). A1 (r7.7): if HERMES_CHILD_TOOLSET_RESTRICT=1, strip
    # fabrication-substrate toolsets (todo) from the child's surface before
    # inheritance. Default off preserves r7.5 behavior for A/B probes.
    if os.environ.get("HERMES_CHILD_TOOLSET_RESTRICT") == "1":
        restricted = _derive_restricted_child_toolset(parent_agent)
    else:
        restricted = None
    return delegate_task(
        goal=goal,
        context=None,
        toolsets=restricted,
        tasks=None,
        max_iterations=None,
        acp_command=None,
        acp_args=None,
        parent_agent=parent_agent,
    )
```

Note: `os` import must be added to the module's import block (currently only imports `delegate_task` and `registry`).

### Env-var gate

`HERMES_CHILD_TOOLSET_RESTRICT=1` activates the restriction; any other value (including unset) is a no-op that passes `toolsets=None` and preserves r7.5 behavior verbatim. This makes A/B probes clean: same staged binary, flip env, no conditional logic drift. The env var is read per-call (not cached) so a probe harness can toggle between runs without restarting Hermes.

A grandchild (depth-2 spawn) cannot occur — `delegation` is blocked-stripped from the child (`delegate_tool.py:110-113`) AND `MAX_DEPTH = 2` enforces it (`delegate_tool.py:36`, `:535-541`). So the env-gate's propagation to grandchildren is moot: there are no grandchildren.

### Unit test

```python
class _FakeParent:
    enabled_toolsets = None
    valid_tool_names = None

def test_derive_restricted_child_toolset_none_none_returns_default_minus_todo():
    # Parent with no explicit toolsets and no valid_tool_names must fall back
    # to DEFAULT_TOOLSETS, not return [] (which would silently disable all
    # child tools and cause dispatch failure).
    result = _derive_restricted_child_toolset(_FakeParent())
    assert "todo" not in result
    assert result, "helper must not return empty list on None/None parent"
    assert set(result) == set(_DEFAULT_TOOLSETS_FALLBACK) - {"todo"}
```

Two additional assertions worth including in the S3 implementation test file:

```python
def test_idempotent_when_parent_already_excludes_todo():
    class P: enabled_toolsets = ["file", "web", "terminal"]
    assert _derive_restricted_child_toolset(P()) == ["file", "web", "terminal"]

def test_strips_todo_from_enabled_list():
    class P: enabled_toolsets = ["file", "todo", "web"]
    out = _derive_restricted_child_toolset(P())
    assert "todo" not in out
    assert set(out) == {"file", "web"}
```

## Edge cases

- **Parent already excludes `todo`.** Helper is idempotent — list comprehension over a set that does not contain `todo` returns the same list (modulo ordering, which `_build_child_agent` doesn't depend on). Covered by `test_idempotent_when_parent_already_excludes_todo`.
- **Parent has a restricted subset (e.g., `file_readonly` only).** Helper returns that subset (minus `todo` if present, minus nothing if not). The intersection logic at `delegate_tool.py:242-243` (`[t for t in toolsets if t in parent_toolsets]`) further clips to the parent's surface, so even if our helper returned something extra, the child could not gain tools the parent lacks. Non-expansive by construction.
- **Parent has `enabled_toolsets=[]` (explicit empty list, distinct from None).** `_resolve_parent_toolsets` returns `[]` because the first branch hits (`parent_enabled is not None` is true for `[]`). Helper then returns `[]`. `delegate_task` receives `toolsets=[]`. In `_build_child_agent` at `delegate_tool.py:241`, `if toolsets:` is **false** for an empty list — so branch 1 is skipped. Then `elif parent_enabled is not None` (still true for `[]`) fires → `child_toolsets = _strip_blocked_tools([])` → `[]`. This is the same behavior as the unpatched code for a parent with empty explicit toolsets, i.e., a child with no tools. Not a regression, but worth flagging: if a probe configures a parent with `enabled_toolsets=[]`, both the A1-on and A1-off paths yield an empty child. Document, don't mitigate.
- **Grandchild propagation.** `MAX_DEPTH = 2` and `delegation` being blocked for children together guarantee no grandchildren exist, so the question of "does the restriction propagate to grandchildren?" is vacuous. Document this in a code comment for future readers.
- **`model_tools` import fails (e.g., during unit test without Hermes runtime).** Helper catches the exception and falls back to `_DEFAULT_TOOLSETS_FALLBACK` minus `todo`. This keeps the helper unit-testable in a lightweight harness.
- **Parent is `None` (API misuse).** `_resolve_parent_toolsets(None)` returns `_DEFAULT_TOOLSETS_FALLBACK` unchanged; helper then strips `todo`. The enclosing `delegate_task` will itself reject `parent_agent is None` at `delegate_tool.py:529-530`, so this path is defensive only.

## Surprises vs I2 report

One material reconciliation needed, otherwise I2 is confirmed.

1. **I2's three-way fallback formulation was slightly off.** The plan text at §6.4 (likely paraphrasing I2) wrote `parent.enabled_toolsets → parent.valid_tool_names → DEFAULT_TOOLSETS`, implying `valid_tool_names` is used directly as a toolset list. It is not. `valid_tool_names` is a list of **tool names**, which must be reverse-mapped to **toolset names** via `model_tools.get_toolset_for_tool` (`model_tools.py:562-564`). My helper does this mapping; a naive `list(parent.valid_tool_names)` would return raw tool names that `delegate_task` would then fail to match against registered toolsets. Worth flagging to S3 implementer — the sketch in the plan (`return list(parent_agent.valid_tool_names)`) is incorrect as written.

2. **`delegate_worker_v2.py` is present only as a .pyc on the VM** (`~/.hermes/hermes-agent/tools/__pycache__/delegate_worker_v2.cpython-311.pyc`, no corresponding `.py` in `tools/`). The canonical source is `variants/hermes/delegate_worker_v2.py` on the Mac side, staged via `probe-variantF-stage.sh` (per plan §6.5 which will become `probe-variantJ-stage.sh`). This matches the variant-overlay staging pattern and is not a concern — just noting that post-patch verification must re-stage before inspecting child session tool arrays.

3. **`delegate_worker_v2` registers itself with `toolset="delegation"`** (`variants/hermes/delegate_worker_v2.py:154`). Since `delegation` is blocked for children, `delegate_worker_v2` is correctly absent from the child's tool surface in either A1-on or A1-off mode. No concern.

Nothing changed on the VM between I2's 2026-04-20 morning read and mine. File mtimes on `delegate_tool.py` are stable.

## Ready for S3 impl?

**YES.**

S3 has: exact lines to modify (`variants/hermes/delegate_worker_v2.py` lines 136-148 plus a new helper block and an `import os` addition), full helper code, full invocation diff, env-var gating spec, three unit test assertions (one required, two recommended), and edge-case documentation. The plan's proposed helper at §6.4 needs one correction (reverse-map `valid_tool_names` through `model_tools.get_toolset_for_tool`); otherwise it is implementable as written.

No blockers.
