"""A1 unit tests for delegate_worker_v2._derive_restricted_child_toolset.

Goal: exercise the helper in isolation without requiring the Hermes runtime.
The module under test imports `from tools.delegate_tool import delegate_task`
and `from tools.registry import registry` at top level — those imports will
fail in a plain-Python test environment. We shim them out with stub modules
before importing the helper. Since the helper itself only touches
`os.environ` (in the caller) and a local `import model_tools` (lazy,
wrapped in try/except), the shim is sufficient.

Run locally:  python3 variants/hermes/test_delegate_worker_v2_a1.py
Expected:     all asserts pass, final "OK" line printed.
"""

import os
import sys
import types


def _install_hermes_stubs():
    """Insert minimal stubs for tools.delegate_tool and tools.registry so the
    delegate_worker_v2 module can be imported outside the Hermes runtime."""
    tools_mod = types.ModuleType("tools")
    tools_mod.__path__ = []  # mark as package

    dt_mod = types.ModuleType("tools.delegate_tool")
    def _delegate_task_stub(*args, **kwargs):
        raise RuntimeError("stub: delegate_task should not be called in unit test")
    dt_mod.delegate_task = _delegate_task_stub

    reg_mod = types.ModuleType("tools.registry")
    class _RegistryStub:
        def register(self, *args, **kwargs):
            pass  # no-op
    reg_mod.registry = _RegistryStub()

    sys.modules.setdefault("tools", tools_mod)
    sys.modules["tools.delegate_tool"] = dt_mod
    sys.modules["tools.registry"] = reg_mod


_install_hermes_stubs()

# Now import the module under test.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import delegate_worker_v2  # noqa: E402
from delegate_worker_v2 import (  # noqa: E402
    _DEFAULT_TOOLSETS_FALLBACK,
    _derive_restricted_child_toolset,
)


# --- Mocks -----------------------------------------------------------------

class _FakeParentBothNone:
    """Parent with no explicit toolsets and no valid_tool_names.

    Triggers the last-resort fallback branch in _resolve_parent_toolsets.
    """
    enabled_toolsets = None
    valid_tool_names = None


class _FakeParentExcludesTodo:
    """Parent whose enabled_toolsets already excludes todo."""
    enabled_toolsets = ["file", "web", "terminal"]
    valid_tool_names = None


class _FakeParentIncludesTodo:
    """Parent whose enabled_toolsets includes todo in the middle of a list."""
    enabled_toolsets = ["file", "todo", "web"]
    valid_tool_names = None


class _FakeParentMultiExclusions:
    """Parent whose enabled_toolsets already excludes multiple tools (no
    delegation, no clarify) AND includes todo. Helper must strip todo and
    leave the other exclusions intact.
    """
    # Note: the "already excluded" concept is modelled by simply NOT listing
    # delegation/clarify in enabled_toolsets. The helper should return a
    # list that likewise does not contain them (it just passes parent_enabled
    # through minus todo).
    enabled_toolsets = ["file", "web", "terminal", "todo", "search"]
    valid_tool_names = None


# --- Tests -----------------------------------------------------------------

def test_none_none_returns_default_minus_todo():
    """Parent with enabled_toolsets=None and no valid_tool_names falls back
    to DEFAULT_TOOLSETS_FALLBACK. Helper must strip todo (if present in the
    fallback — it isn't by default, so the result == fallback) and must NOT
    return an empty list (which would silently disable all child tools)."""
    result = _derive_restricted_child_toolset(_FakeParentBothNone())
    assert "todo" not in result, f"todo must be stripped; got {result!r}"
    assert result, f"helper must not return empty list on None/None parent; got {result!r}"
    expected = [t for t in _DEFAULT_TOOLSETS_FALLBACK if t != "todo"]
    assert set(result) == set(expected), (
        f"expected {expected!r}, got {result!r}"
    )


def test_idempotent_when_parent_already_excludes_todo():
    """Parent's enabled_toolsets already lacks todo → helper returns the
    same list (order-preserving for the enabled_toolsets path)."""
    result = _derive_restricted_child_toolset(_FakeParentExcludesTodo())
    assert result == ["file", "web", "terminal"], (
        f"idempotent path should preserve list verbatim; got {result!r}"
    )


def test_strips_todo_from_enabled_list():
    """Parent's enabled_toolsets contains todo in the middle — helper removes
    just todo, preserving order and all other entries."""
    result = _derive_restricted_child_toolset(_FakeParentIncludesTodo())
    assert "todo" not in result, f"todo must be stripped; got {result!r}"
    assert result == ["file", "web"], (
        f"expected ['file', 'web'] (order preserved, todo removed); got {result!r}"
    )


def test_preserves_multiple_exclusions_and_removes_todo():
    """Parent that already excludes delegation/clarify/memory (they simply
    aren't in enabled_toolsets) AND includes todo — helper strips todo and
    leaves the other implicit exclusions intact (i.e., they stay out)."""
    result = _derive_restricted_child_toolset(_FakeParentMultiExclusions())
    assert "todo" not in result, f"todo must be stripped; got {result!r}"
    assert "delegation" not in result, "delegation must remain excluded"
    assert "clarify" not in result, "clarify must remain excluded"
    assert "memory" not in result, "memory must remain excluded"
    assert set(result) == {"file", "web", "terminal", "search"}, (
        f"unexpected residual: {result!r}"
    )


def test_none_parent_returns_default_minus_todo():
    """Defensive: parent_agent is None (API misuse). Helper returns the
    fallback minus todo rather than crashing."""
    result = _derive_restricted_child_toolset(None)
    assert result, "must not return empty list for None parent"
    assert "todo" not in result


if __name__ == "__main__":
    tests = [
        test_none_none_returns_default_minus_todo,
        test_idempotent_when_parent_already_excludes_todo,
        test_strips_todo_from_enabled_list,
        test_preserves_multiple_exclusions_and_removes_todo,
        test_none_parent_returns_default_minus_todo,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    if failed:
        print(f"\n{failed} failure(s)")
        sys.exit(1)
    print(f"\nOK ({len(tests)} tests passed)")
