---
type: A1 implementation (S3)
date: 2026-04-20
campaign: r7.7 Path A
worker: S3
---
# A1 implementation

S3 implemented A1 (child toolset restriction) per the S1 diag at
`ARTIFACT-r7.7-A1-diag.md`. Three files modified / created on the Mac side:
the β-fuse handler module, a new stage script, and a standalone unit test.
Nothing was pushed, committed, or staged to the VM — that is S7's job.

## Files modified

| File | Status | md5 before | md5 after |
|------|--------|-----------:|----------:|
| `variants/hermes/delegate_worker_v2.py` | edited (added `import os`, two helpers, env-gated invocation) | `d31876fe987331a26c8640202334fd46` | `cadb49504950dc40459f95f33b38dc9f` |
| `probe-variantJ-A1-stage.sh` | created, chmod +x | — | `64a0c7285a820065a5ec66d53d86a9bd` |
| `variants/hermes/test_delegate_worker_v2_a1.py` | created | — | `d4acfcf0090bb2dc84ff8336111c198e` |

No other files touched.

## Helper code (final)

Inserted between the imports and `DELEGATE_WORKER_V2_SCHEMA`. Uses the
diag's reverse-map pattern (`model_tools.get_toolset_for_tool`) verbatim —
NOT the buggy plan §6.4 sketch that returned raw tool names.

```python
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

    Grandchild note: MAX_DEPTH=2 and `delegation` being blocked for children
    together guarantee no grandchildren exist, so this helper's effect does
    not need to propagate beyond depth 1.
    """
    resolved = _resolve_parent_toolsets(parent_agent)
    return [t for t in resolved if t not in _A1_FABRICATION_SUBSTRATE]
```

Minor additions vs. the diag sketch: a grandchild-note paragraph in
`_derive_restricted_child_toolset`'s docstring to capture the "why this
doesn't need to propagate" reasoning from the diag's Edge Cases section. No
behavioral change.

## Invocation edit (before / after)

### Before (lines ~137-148 of pre-patch file)

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

### After

```python
    # Spawn child via delegate_task internals (same path as legacy
    # delegate_worker). A1 (r7.7): if HERMES_CHILD_TOOLSET_RESTRICT=1, strip
    # fabrication-substrate toolsets (todo) from the child's surface before
    # inheritance. Default off preserves r7.5 behavior for A/B probes.
    # Env var is read per-call (not cached) so a probe harness can toggle
    # between runs without restarting Hermes.
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

Backward compat: when `HERMES_CHILD_TOOLSET_RESTRICT` is unset / any value
other than `"1"`, `restricted = None` and `delegate_task(toolsets=None, ...)`
matches r7.5 behavior exactly.

## Stage script header

```
#!/usr/bin/env bash
# probe-variantJ-A1-stage.sh — Stage/unstage the A1 (child toolset restriction)
# patch to delegate_worker_v2.py on ubuntu-vm.
#
# USAGE:
#   ./probe-variantJ-A1-stage.sh stage      # backup existing delegate_worker_v2.py to .probe-r7.7-orig, scp local copy
#   ./probe-variantJ-A1-stage.sh unstage    # restore .probe-r7.7-orig backup
#   ./probe-variantJ-A1-stage.sh status     # show md5 state and overall STAGED / UNSTAGED / PARTIAL
#
# DEPENDENCY CHAIN (variantJ-A1 stacks on top):
#   * variantD:   stages delegate_worker v1               (backup: .probe-d-orig)
#   * variantF:   stages delegate_worker_v2 (β-fuse)       (backup: .probe-r7.4-orig)
#   * variantG/H/I: later β-fuse refinements
#   * variantJ-A1 (THIS SCRIPT): overlays A1 child toolset restriction on top
#                                 of the variantF-staged delegate_worker_v2.py
#                                 (backup: .probe-r7.7-orig)
#
# PRECONDITION:
#   variantF MUST be staged first. This script verifies the VM has a
#   delegate_worker_v2.py at ~/.hermes/hermes-agent/tools/ before touching
#   it; if missing, aborts with a clear error pointing at probe-variantF-stage.sh.
#
# SAFETY:
#   * Idempotent: re-running `stage` when local md5 matches remote is a no-op.
#   * Backup uses `.probe-r7.7-orig` suffix (distinct from variantF's
#     `.probe-r7.4-orig` so the two chains coexist cleanly).
#   * Backup is created ONLY if it does not already exist — preserves the
#     pre-A1 state across repeated stage/unstage cycles.
#   * set -euo pipefail: aborts on mid-stage failure.
#   * Runtime behavior is env-gated by HERMES_CHILD_TOOLSET_RESTRICT=1; staging
#     this file without setting the env var is a pure no-op for running
#     agents. A/B probes toggle the env, not the staged file.
```

Key design points:

- **Precondition check.** `cmd_stage` aborts if the VM has no
  `~/.hermes/hermes-agent/tools/delegate_worker_v2.py` with a clear error
  pointing at `probe-variantF-stage.sh`.
- **Idempotent stage.** If local and remote md5s already match, skip the
  scp (but still ensure the `.probe-r7.7-orig` backup exists defensively).
- **Idempotent backup.** Backup is created only if absent — preserves the
  earliest pre-A1 state across repeated stage/unstage cycles even if the
  remote was modified out of band between cycles.
- **Distinct backup suffix.** `.probe-r7.7-orig` does not collide with
  variantF's `.probe-r7.4-orig` chain; both coexist.
- **Status command.** Prints local md5, remote md5, backup presence +
  backup md5, then classifies overall state as STAGED / UNSTAGED /
  PARTIAL with actionable guidance.

## Unit test results

Ran locally on Mac (Python 3, stubs for `tools.delegate_tool` and
`tools.registry` since the real modules aren't importable outside the
Hermes runtime):

```
$ python3 variants/hermes/test_delegate_worker_v2_a1.py
PASS  test_none_none_returns_default_minus_todo
PASS  test_idempotent_when_parent_already_excludes_todo
PASS  test_strips_todo_from_enabled_list
PASS  test_preserves_multiple_exclusions_and_removes_todo
PASS  test_none_parent_returns_default_minus_todo

OK (5 tests passed)
```

Test coverage maps to the three required assertions from the task spec
plus two defensive cases:

1. `test_none_none_returns_default_minus_todo` — parent with
   `enabled_toolsets=None` and no `valid_tool_names`: helper returns
   `_DEFAULT_TOOLSETS_FALLBACK` minus todo, NOT an empty list. (Required.)
2. `test_idempotent_when_parent_already_excludes_todo` — parent whose
   `enabled_toolsets` already lacks todo: helper returns the same list
   verbatim. (Required.)
3. `test_strips_todo_from_enabled_list` — parent has todo mid-list:
   helper strips exactly todo, preserves order.
4. `test_preserves_multiple_exclusions_and_removes_todo` — parent
   already lacks delegation/clarify/memory and has todo: helper strips
   todo, leaves the other implicit exclusions alone. (Required — the
   "multiple exclusions" case.)
5. `test_none_parent_returns_default_minus_todo` — defensive: helper
   tolerates `parent_agent=None` (API misuse path).

## Verification

- `python -c "import ast; ast.parse(open('variants/hermes/delegate_worker_v2.py').read())"` → PASS
- `bash -n probe-variantJ-A1-stage.sh` → PASS
- `python3 variants/hermes/test_delegate_worker_v2_a1.py` → 5/5 PASS

md5 summary:

```
cadb49504950dc40459f95f33b38dc9f  variants/hermes/delegate_worker_v2.py
64a0c7285a820065a5ec66d53d86a9bd  probe-variantJ-A1-stage.sh
d4acfcf0090bb2dc84ff8336111c198e  variants/hermes/test_delegate_worker_v2_a1.py
```

No VM-side actions taken. No other files modified.

## Judgment notes (diag deviations)

None material. The implementation follows the diag's code verbatim, with
two non-behavioral additions:

1. A grandchild-note sentence appended to
   `_derive_restricted_child_toolset`'s docstring, citing MAX_DEPTH=2 +
   delegation being blocked for children. Sourced from the diag's Edge
   Cases section.
2. The unit test file needed shim modules for `tools.delegate_tool` and
   `tools.registry` because `delegate_worker_v2.py` imports them at the
   module top. The diag's test sketch assumed the helper was importable
   without the wrapper imports; in practice the module-level
   `from tools.delegate_tool import delegate_task` fires on import. The
   shim is minimal (two stub `types.ModuleType` objects) and does not
   change what the test exercises — it just lets the import complete so
   the helper can be called.

## Ready for S5 judge?

**YES.** All three deliverables produced and locally verified; no
blockers; no VM mutations pending S7. S5 has a clean diff and a working
test to evaluate.
