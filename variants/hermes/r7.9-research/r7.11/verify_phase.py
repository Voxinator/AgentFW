"""verify_phase — r7.11 verifier, tiers 1, 2, and 3.

Items 2 and 3 of the r7.11 implementation order. Standalone; no
Hermes integration. Per DESIGN-r7.11-architecture.md §3, this module
produces a structured `VerifyResult` whose shape will be persisted to
verified-state.json by a thin Hermes tool wrapper (item 5). This
module does not write any file; the wrapper sets `persisted_to`.

Tiers implemented here:
  - Tier 1 (PRESENCE): each declared path exists; body is non-trivial
    (>= presence_min_bytes, >= presence_min_nonblank_lines, and for
    Python files, AST is more than a single module-level docstring
    Expr/Constant).
  - Tier 2 (SYNTAX + IMPORTS): for each Python file: ast.parse
    succeeds; no `raise NotImplementedError` in non-test code; imports
    resolve project-relative or via importlib.util.find_spec, with
    PHASE-AWARENESS for cross-phase declared paths.
  - Tier 3 (WIRING): structured AST analysis of cross-file references
    in four explicit categories:
      [CAT1:defined-unused]            top-level definition is never
                                        referenced from any phase-N file
                                        or from any tolerated-phase file
                                        (that exists on disk); subject
                                        to a small public-API allow-list
                                        and `__all__` exemption.
      [CAT2:imported-unused]           an `import` introduces a name
                                        that is never used in the same
                                        file (subject to TYPE_CHECKING
                                        and `__all__` exemptions).
      [CAT3:test-references-nonexistent]
                                        a test file does
                                        `from <impl_module> import X`
                                        where the resolved impl file
                                        does not define X.
      [CAT4:duplicate-definition]      the same top-level symbol name
                                        is defined in two-or-more files
                                        across phase-N + tolerated
                                        phase-M files-on-disk + ORPHAN
                                        baseline files (any .py under
                                        scaffold_root/src or /tests not
                                        declared in any PLAN.md phase).
                                        Orphan participants are flagged
                                        with the substring "orphan
                                        baseline stub" in the finding
                                        body so the parent's remediation
                                        path is unambiguous (delete or
                                        empty the orphan, or rewrite the
                                        phase to declare and modify the
                                        orphan in-place). See r7.11 F-9
                                        for motivating trial.
    Tier 3 also scans phase-N files for dynamic-dispatch markers
    (importlib.import_module, __import__, getattr/setattr on a known-
    imported module, exec/eval, globals()/locals() mutation). When any
    such marker is present, the result's `tier_3_hint` field is set to
    a string suggesting the caller invoke tier 3.5 (item 4) for full
    coverage.

The eventual default tier in production (per design §3) is 3; in this
module the default remains 2 to preserve backward compatibility with
existing callers / tests until item 5 (the Hermes tool wrapper) is
written and explicitly passes tier=3.

Tier 4 is NOT implemented in this build (deferred to r7.12); calling
with tier=4 raises NotImplementedError.

Tier 3.5 (RUNTIME SMOKE TEST) — opt-in:
  Activated via `with_runtime_smoke_test=True`. Spawns a subprocess
  with a constrained environment that imports the phase's PLAN.md
  modules in declared order, scans for registry-shaped objects, and
  reports any registered (key, value) pair whose `value.__module__`
  resolves to an unexpected file (the n=10 r4 importlib-shadowing
  archetype). Findings populate `runtime_smoke_findings`; only
  `[SHADOWING:...]` entries set `passed=False`. `[INCONCLUSIVE:...]`
  entries (subprocess crashed/timed out/malformed output) do NOT
  affect `passed` — tiers 1-3 alone determine pass/fail in that case.
  `[CHECKED:...]` entries are informational. Tier 3.5 runs ONLY when
  tiers 1 and 2 passed; otherwise it emits `[SKIPPED]` and continues.
  See TIER35-NOTES.md for sandbox guarantees and detection limits.

  The Hermes tool wrapper (item 5) determines when to invoke tier 3.5;
  this module just executes when asked. The wrapper SHOULD escalate
  to tier 3.5 when tier 3 returns a `tier_3_hint` (dynamic imports
  detected). Default (`with_runtime_smoke_test=False`) keeps the fast
  path identical to pre-tier-3.5 behavior.

Phase-awareness rule (LOAD-BEARING — see PHASE-AWARENESS-NOTE.md):
  When verifying phase N, the caller may pass `project_phases` (the
  full list of phases from PLAN.md). The verifier computes a "tolerated
  unresolved" set as the union of `paths` declared by all OTHER phases.
  An unresolved import whose target maps to a path in that set is
  treated as `deferred (declared in another phase)` and does NOT cause
  passed=False. With project_phases=None, only the phase being verified
  is known, so cross-phase imports cannot be deferred.

Resolution algorithm for imports (deterministic; documented in source):
  For an absolute import `from a.b.c import name` in file F:
    1. Project-relative search at scaffold_root: try
       a/b/c.py, then a/b/c/__init__.py, then a/b.py, then a/b/__init__.py,
       then a.py, then a/__init__.py. The FIRST hit wins (most-specific
       module first). If any of these is in the tolerated-deferred set,
       record as deferred and continue.
    2. If not project-relative, try `importlib.util.find_spec("a.b.c")`
       and walk up to "a.b" and "a" if needed. A find_spec hit is
       treated as resolved (third-party / stdlib / venv).
    3. Otherwise: integrity issue (unresolvable import).

  For a relative import `from .x import y` in file F at depth N:
    1. Compute the package directory: walk N levels up from F.
    2. Look for x.py / x/__init__.py under that directory.
    3. Apply the tolerated-deferred check.
    4. Otherwise: integrity issue.

  Re-export pattern: if `from .x import y`, the verifier only checks
  that `.x` resolves to a file or package. Whether `y` actually exists
  inside `.x` is tier-3's job (wiring).

Test/non-test classification:
  A file is "test code" if any of:
    - path component "tests" anywhere in its relative path
    - filename starts with "test_"
    - filename ends with "_test.py"
  All other Python files are non-test. `raise NotImplementedError`
  in non-test code is an integrity issue; in test code it is exempt
  (test stubs are common).

Stdlib only.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple, Union

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class Tier(Enum):
    """Tiers implemented in this build.

    Tier 3.5 (RUNTIME_SMOKE) is item 4; tier 4 (SEMANTIC) is r7.12.
    They are not listed here on purpose — those workers add them.
    """

    PRESENCE = 1
    SYNTAX = 2
    WIRING = 3


@dataclass
class PhaseInput:
    """What the caller passes for a single phase.

    `paths` are RELATIVE to scaffold_root, exactly as PLAN.md declares
    them.
    """

    id: int
    paths: List[str]


@dataclass
class VerifyResult:
    """Matches the §3 schema. `persisted_to` is set by the Hermes tool
    wrapper (item 5) when it writes the result into verified-state.json
    via `verified_state.record_verdict` + `save`. This module does NOT
    set it; it stays None on direct calls.

    `tier_3_hint` is a tier-3 advisory: None when tier 3 didn't run OR
    ran without finding any dynamic-dispatch markers; a non-empty
    string when phase-N files contain `importlib.import_module(...)`,
    `__import__(...)`, `getattr` on an imported module, `exec`/`eval`,
    or `globals()`/`locals()` mutation. The hint is informational and
    independent of `passed` — a phase can pass tier 3 wiring AND have
    a hint that suggests escalating to tier 3.5 runtime smoke (item 4)
    for runtime-shadowing patterns AST cannot resolve.

    `runtime_smoke_findings` (tier 3.5) prefix taxonomy:
      [SHADOWING:...]    Registry entry's __module__ is a file NOT
                         declared by any phase OR is declared by a
                         phase but the registered value resolves to
                         an unexpected source. Sets passed=False and
                         contributes to corrective_dispatch.
      [CHECKED:...]      A registry entry whose source resolves to a
                         phase-declared file or to stdlib/third-party.
                         Informational; audit trail of what was scanned.
                         Does NOT affect passed.
      [INCONCLUSIVE:...] Tier 3.5 could not conclude (subprocess crashed,
                         timed out, malformed output, sandbox setup
                         failure, or per-module import error). Does NOT
                         affect passed; tier-1-3 verdict stands.
      [SKIPPED]          Tier 3.5 was requested but tier 1 or tier 2
                         failed first; runtime smoke not attempted.

    `acceptance_runner_findings` (tier 3.7) prefix taxonomy:
      [ACCEPTANCE_PASSED]       Acceptance command exited 0. Informational;
                                does NOT affect passed (tier 3.7 is a
                                gate, not a guarantee — tiers 1..3 still
                                determine the integrity verdict).
      [ACCEPTANCE_FAILED:N]     Acceptance command exited with a code that
                                indicates a real failure of the criterion
                                as written (e.g., pytest exit 1). Sets
                                passed=False and contributes captured
                                stdout/stderr to corrective_dispatch.
      [ENVIRONMENT:<reason>]    Acceptance command could not complete due
                                to an environment-side issue (timeout,
                                command-not-found, no-tests-collected).
                                Sets passed=False; corrective_dispatch
                                points the parent at env diagnosis,
                                NOT at code revision.
      [INCONCLUSIVE:<reason>]   Tier 3.7 could not determine an acceptance
                                verdict (subprocess crashed, pytest
                                internal error, unknown exit code).
                                Does NOT affect passed; tier-1-3 verdict
                                stands.
      [SKIPPED]                 Tier 3.7 did not run — either no
                                acceptance_command was declared in PLAN.md
                                for this phase, or tier 1 / tier 2 failed
                                first (no point running an acceptance
                                command on broken syntax).
    """

    passed: bool
    tier_run: int
    missing_paths: List[str] = field(default_factory=list)
    integrity_issues: List[str] = field(default_factory=list)
    runtime_smoke_findings: List[str] = field(default_factory=list)
    acceptance_runner_findings: List[str] = field(default_factory=list)
    semantic_concerns: List[str] = field(default_factory=list)
    corrective_dispatch: str = ""
    persisted_to: Optional[str] = None
    tier_3_hint: Optional[str] = None


# ---------------------------------------------------------------------------
# Tier-1 helpers
# ---------------------------------------------------------------------------


def _is_pure_docstring_stub(src: str) -> bool:
    """True iff the module's AST is exactly one Expr whose value is a
    string Constant (or empty body). A docstring + any other top-level
    node returns False."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        # Syntactically invalid files are not "stubs" for tier-1
        # purposes — tier 2 will flag the SyntaxError. Don't double-count.
        return False
    body = tree.body
    if not body:
        return True
    if len(body) != 1:
        return False
    node = body[0]
    if not isinstance(node, ast.Expr):
        return False
    val = node.value
    if isinstance(val, ast.Constant) and isinstance(val.value, str):
        return True
    return False


def _check_presence_one(
    path_rel: str,
    scaffold_root: Path,
    min_bytes: int,
    min_nonblank_lines: int,
) -> Optional[str]:
    """Return None if the path passes tier 1; else a string note for
    `missing_paths` describing why it failed."""
    abs_path = scaffold_root / path_rel
    if not abs_path.exists():
        return path_rel
    if not abs_path.is_file():
        return f"{path_rel} (present but not a regular file)"
    try:
        data = abs_path.read_bytes()
    except OSError as exc:
        return f"{path_rel} (unreadable: {exc})"
    if len(data) < min_bytes:
        return (
            f"{path_rel} (present but too small: {len(data)} bytes < "
            f"{min_bytes})"
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        # Binary-ish file. Accept presence based on byte count alone for
        # non-text files; line count is meaningless. But if the path
        # ends in .py, this is suspicious — flag it.
        if path_rel.endswith(".py"):
            return f"{path_rel} (present but not valid UTF-8)"
        return None

    nonblank = sum(1 for line in text.splitlines() if line.strip())
    if nonblank < min_nonblank_lines:
        return (
            f"{path_rel} (present but only {nonblank} non-blank lines < "
            f"{min_nonblank_lines})"
        )

    if path_rel.endswith(".py"):
        if _is_pure_docstring_stub(text):
            return f"{path_rel} (present but pure-docstring stub)"

    return None


# ---------------------------------------------------------------------------
# Tier-2 helpers — test/non-test classification
# ---------------------------------------------------------------------------


def _is_test_path(path_rel: str) -> bool:
    """A path is test code if any path-component is 'tests' OR the
    filename starts with 'test_' OR ends with '_test.py'."""
    parts = Path(path_rel).parts
    if "tests" in parts:
        return True
    name = Path(path_rel).name
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    return False


def _find_notimplementederror_raises(tree: ast.AST) -> List[int]:
    """Return line numbers of `raise NotImplementedError(...)` /
    `raise NotImplementedError` nodes."""
    found: List[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise):
            continue
        exc = node.exc
        if exc is None:
            continue
        # raise NotImplementedError
        if isinstance(exc, ast.Name) and exc.id == "NotImplementedError":
            found.append(node.lineno)
            continue
        # raise NotImplementedError(...)
        if isinstance(exc, ast.Call):
            func = exc.func
            if isinstance(func, ast.Name) and func.id == "NotImplementedError":
                found.append(node.lineno)
                continue
    return found


# ---------------------------------------------------------------------------
# Tier-2 helpers — import collection
# ---------------------------------------------------------------------------


@dataclass
class _ImportRef:
    """One import statement to resolve."""

    # For `import a.b.c` and `from a.b import c`:
    # absolute=True, level=0, module="a.b" or "a.b.c"
    # For `from .x import y` inside a package at level=1:
    # absolute=False, level=1, module="x" (or "" for `from . import y`)
    absolute: bool
    level: int
    module: str  # may be "" for `from . import x`
    # For `from M import X` we need X for fallback resolution: if M is a
    # package with submodule X, we may need to try M.X as a module path.
    # For `from M import X`, we ONLY check M resolves; X-existence is
    # tier-3's wiring concern. So `name` is informational.
    name: Optional[str]
    lineno: int


def _collect_imports(tree: ast.AST) -> List[_ImportRef]:
    refs: List[_ImportRef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # `import a.b.c` — module = "a.b.c", absolute, level=0.
            for alias in node.names:
                refs.append(
                    _ImportRef(
                        absolute=True,
                        level=0,
                        module=alias.name,
                        name=None,
                        lineno=node.lineno,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level or 0
            absolute = level == 0
            # Even though `from a.b import c` only needs `a.b` resolved,
            # we record the names in case we want a richer report.
            if node.names:
                for alias in node.names:
                    refs.append(
                        _ImportRef(
                            absolute=absolute,
                            level=level,
                            module=module,
                            name=alias.name,
                            lineno=node.lineno,
                        )
                    )
            else:
                refs.append(
                    _ImportRef(
                        absolute=absolute,
                        level=level,
                        module=module,
                        name=None,
                        lineno=node.lineno,
                    )
                )
    return refs


# ---------------------------------------------------------------------------
# Tier-2 helpers — import resolution
# ---------------------------------------------------------------------------


def _module_to_candidate_paths(module: str) -> List[str]:
    """Given a dotted module path 'a.b.c', return the relative POSIX
    paths to try, in priority order: most-specific module/package first.

    For 'a.b.c':
      a/b/c.py
      a/b/c/__init__.py
      a/b.py
      a/b/__init__.py
      a.py
      a/__init__.py
    """
    parts = module.split(".") if module else []
    candidates: List[str] = []
    while parts:
        base = "/".join(parts)
        candidates.append(base + ".py")
        candidates.append(base + "/__init__.py")
        parts = parts[:-1]
    return candidates


def _resolve_absolute_project(
    module: str,
    scaffold_root: Path,
) -> Optional[Path]:
    """Try to resolve `module` against scaffold_root. Returns the
    project-relative absolute path on hit; None on miss.

    The first candidate (most-specific module/package) wins, so
    'a.b' shadows 'a' when both exist. This matches Python's actual
    import-resolution preference for the deepest match given the
    declared dotted path.
    """
    for cand in _module_to_candidate_paths(module):
        p = scaffold_root / cand
        if p.is_file():
            return p
    return None


def _resolve_absolute_venv(module: str) -> bool:
    """Try `importlib.util.find_spec(module)` walking up to its parents.
    Returns True if any parent prefix resolves via the active venv /
    stdlib / site-packages. Doesn't import the module — find_spec is
    metadata-only.
    """
    if not module:
        return False
    parts = module.split(".")
    while parts:
        candidate = ".".join(parts)
        try:
            spec = importlib.util.find_spec(candidate)
        except (ImportError, ValueError, ModuleNotFoundError):
            spec = None
        except Exception:  # noqa: BLE001
            # find_spec can raise various things if a parent's __init__
            # has side effects. Treat as miss; we don't want to execute.
            spec = None
        if spec is not None:
            return True
        parts = parts[:-1]
    return False


def _resolve_relative(
    file_path: Path,
    scaffold_root: Path,
    level: int,
    module: str,
) -> Optional[Path]:
    """Resolve `from .module import x` / `from ..module import x`.

    The package directory is computed by walking `level` directories
    up from the file's parent. (level=1 means the file's own directory;
    level=2 means one above; matching Python's spec.) Returns the
    project-relative absolute path or None.

    If `module` is empty (e.g., `from . import x`), the package
    directory itself is the resolution target — we check that the
    package is a real directory, treating it as resolved.
    """
    rel_to_scaffold = file_path.relative_to(scaffold_root)
    parts = list(rel_to_scaffold.parts)
    # Drop the file name.
    parts = parts[:-1]
    # Walk up (level-1) directories. level=1 -> same dir; level=2 -> one up.
    up = level - 1
    if up > len(parts):
        return None
    package_parts = parts[: len(parts) - up] if up else parts

    if module:
        sub_parts = module.split(".")
        full = package_parts + sub_parts
        base = "/".join(full) if full else ""
        candidates = []
        if base:
            candidates.append(base + ".py")
            candidates.append(base + "/__init__.py")
        for cand in candidates:
            p = scaffold_root / cand
            if p.is_file():
                return p
        return None
    else:
        # `from . import x` — only checking the package itself exists.
        if not package_parts:
            # `from . import x` at top-level project — package is
            # scaffold_root. Treat as resolved.
            return scaffold_root
        pkg_dir = scaffold_root / "/".join(package_parts)
        init_file = pkg_dir / "__init__.py"
        if init_file.is_file():
            return init_file
        if pkg_dir.is_dir():
            # Implicit namespace package — accept.
            return pkg_dir
        return None


def _path_in_tolerated(
    target: Path,
    tolerated_paths: Set[str],
    scaffold_root: Path,
) -> bool:
    """target may be a file or directory under scaffold_root. Compare
    its scaffold-root-relative POSIX path against tolerated_paths."""
    try:
        rel = target.relative_to(scaffold_root).as_posix()
    except ValueError:
        return False
    return rel in tolerated_paths


def _is_tolerated_module_unresolved(
    module: str,
    scaffold_root: Path,
    tolerated_paths: Set[str],
) -> Optional[str]:
    """For a module that didn't resolve project-relative or via venv,
    check if any candidate path matches tolerated_paths. Returns the
    matched relative path on hit; None on miss."""
    for cand in _module_to_candidate_paths(module):
        if cand in tolerated_paths:
            return cand
    return None


def _is_tolerated_relative_unresolved(
    file_path: Path,
    scaffold_root: Path,
    level: int,
    module: str,
    tolerated_paths: Set[str],
) -> Optional[str]:
    rel_to_scaffold = file_path.relative_to(scaffold_root)
    parts = list(rel_to_scaffold.parts)[:-1]
    up = level - 1
    if up > len(parts):
        return None
    package_parts = parts[: len(parts) - up] if up else parts
    sub_parts = module.split(".") if module else []
    full = package_parts + sub_parts
    if not full:
        return None
    base = "/".join(full)
    for cand in (base + ".py", base + "/__init__.py"):
        if cand in tolerated_paths:
            return cand
    return None


# ---------------------------------------------------------------------------
# corrective_dispatch
# ---------------------------------------------------------------------------


def _build_corrective_dispatch(
    phase: PhaseInput,
    missing_paths: List[str],
    integrity_issues: List[str],
    runtime_smoke_findings: Optional[List[str]] = None,
    acceptance_runner_findings: Optional[List[str]] = None,
    acceptance_command: Optional[str] = None,
) -> str:
    """Build a paste-ready re-dispatch goal text per §3 worked examples.

    Format:
      "Re-dispatch with explicit focus on: <paths>. <reason summary>.
       <prescription>."

    Distinguishes tier-1 (missing paths), tier-2 (syntax/imports),
    tier-3 (CAT1..CAT4 wiring categories), tier-3.5 (SHADOWING), and
    tier-3.7 (ACCEPTANCE_FAILED / ENVIRONMENT) failures. When mixed,
    each section is named explicitly and prescriptions are merged.
    INCONCLUSIVE / CHECKED / ACCEPTANCE_PASSED / SKIPPED entries are
    NOT included here — they don't drive a re-dispatch.
    """
    runtime_smoke_findings = runtime_smoke_findings or []
    acceptance_runner_findings = acceptance_runner_findings or []
    shadowing_entries = [
        f for f in runtime_smoke_findings if f.startswith("[SHADOWING:")
    ]
    acceptance_failure_entries = [
        f for f in acceptance_runner_findings
        if f.startswith("[ACCEPTANCE_FAILED:")
        or f.startswith("[ENVIRONMENT:")
    ]
    if (
        not missing_paths
        and not integrity_issues
        and not shadowing_entries
        and not acceptance_failure_entries
    ):
        return ""

    parts: List[str] = []

    if missing_paths:
        focus_paths = [m.split(" ")[0] for m in missing_paths]
        focus_str = ", ".join(focus_paths)
        parts.append(
            f"Re-dispatch with explicit focus on: {focus_str}. "
            f"Phase {phase.id} declared these paths in PLAN.md but tier 1 "
            f"(presence) found them missing or stub-shaped: "
            f"{'; '.join(missing_paths)}. "
            "Write each missing file with a non-trivial body (real "
            "implementation, not a docstring stub or NotImplementedError "
            "placeholder)."
        )
        # If we have BOTH missing_paths and integrity_issues we still
        # ran tier 1 only (the implementation short-circuits before
        # tier 2/3 when missing_paths is non-empty). So no tier-2/3
        # branch follows. Tier 3.5 cannot run when tier 1 fails (it
        # emits [SKIPPED]) so no shadowing branch either.
        return " ".join(parts)

    # Case: ONLY tier-3.5 SHADOWING entries (no tier-2/3 issues). Build a
    # focused re-dispatch citing just the shadowing.
    if shadowing_entries and not integrity_issues:
        parts.append(_format_shadowing_prescription(phase, shadowing_entries))
        if acceptance_failure_entries:
            parts.append(_format_acceptance_prescription(
                phase, acceptance_failure_entries, acceptance_command
            ))
        return " ".join(parts)

    # Case: ONLY tier-3.7 acceptance failures (no tier-2/3 wiring issues
    # AND no tier-3.5 shadowing). Tiers 1-3 cleared; the acceptance command
    # itself is the discriminator.
    if (
        acceptance_failure_entries
        and not integrity_issues
        and not shadowing_entries
    ):
        parts.append(_format_acceptance_prescription(
            phase, acceptance_failure_entries, acceptance_command
        ))
        return " ".join(parts)

    # No missing paths — issues come from tier 2 OR tier 3 OR both.
    # Split by the "[CATn:...]" prefix used by tier 3.
    tier3_issues = [i for i in integrity_issues if i.startswith("[CAT")]
    tier2_issues = [i for i in integrity_issues if not i.startswith("[CAT")]

    # Build focus list from path tokens in all issues.
    focus_paths: List[str] = []
    for issue in integrity_issues:
        # Tier-2 issues are "<path>:<lineno>: ..."
        # Tier-3 issues are "[CATn:tag] <path>:<lineno?> — ..."
        body = issue
        if body.startswith("[CAT"):
            close = body.find("]")
            if close != -1:
                body = body[close + 1 :].strip()
        head = body.split(":", 1)[0].strip()
        # Strip a leading "src/foo.py" — head may also be a bare path.
        # Collapse whitespace and discard empty tails.
        if head and head not in focus_paths:
            focus_paths.append(head)
    focus_str = ", ".join(focus_paths) if focus_paths else "the affected files"

    # ---- tier-2 prescriptions ----
    if tier2_issues and not tier3_issues:
        prescriptions: List[str] = []
        if any("SyntaxError" in i for i in tier2_issues):
            prescriptions.append(
                "Fix the syntax errors so the files parse cleanly."
            )
        if any("NotImplementedError" in i for i in tier2_issues):
            prescriptions.append(
                "Replace `raise NotImplementedError` in non-test code with "
                "a real implementation that satisfies the acceptance criteria."
            )
        if any("unresolvable import" in i for i in tier2_issues):
            prescriptions.append(
                "Either fix the import target (correct module path or write "
                "the missing module) or, if the import is a third-party "
                "dependency, add it to the project's declared dependencies."
            )
        if not prescriptions:
            prescriptions.append(
                "Address each integrity issue listed above."
            )
        parts.append(
            f"Re-dispatch with explicit focus on: {focus_str}. "
            f"Phase {phase.id} cleared tier 1 (presence) but failed tier 2 "
            f"(syntax + imports) with: {'; '.join(tier2_issues)}. "
            + " ".join(prescriptions)
        )
        if shadowing_entries:
            parts.append(_format_shadowing_prescription(phase, shadowing_entries))
        if acceptance_failure_entries:
            parts.append(_format_acceptance_prescription(
                phase, acceptance_failure_entries, acceptance_command
            ))
        return " ".join(parts)

    # ---- tier-3 (and possibly mixed) prescriptions ----
    # Group tier-3 by category.
    cat_buckets: dict = {"CAT1": [], "CAT2": [], "CAT3": [], "CAT4": []}
    for issue in tier3_issues:
        for cat in cat_buckets:
            if issue.startswith(f"[{cat}:"):
                cat_buckets[cat].append(issue)
                break

    cat_prescriptions: List[Tuple[str, str]] = []
    if cat_buckets["CAT1"]:
        cat_prescriptions.append((
            "CAT1:defined-unused",
            "Remove unused definitions OR ensure they're invoked from a "
            "runtime call site.",
        ))
    if cat_buckets["CAT2"]:
        cat_prescriptions.append((
            "CAT2:imported-unused",
            "Remove unused imports OR use them where intended.",
        ))
    if cat_buckets["CAT3"]:
        cat_prescriptions.append((
            "CAT3:test-references-nonexistent",
            "The test references symbols not present in the impl file. "
            "Either define the missing symbols in the impl, or update the "
            "test to reference real symbols.",
        ))
    if cat_buckets["CAT4"]:
        cat_prescriptions.append((
            "CAT4:duplicate-definition",
            "The same symbol is defined in multiple files. Choose ONE "
            "canonical definition; remove or rename the others to avoid "
            "runtime-shadowing.",
        ))

    summary_lines: List[str] = []
    if tier2_issues:
        summary_lines.append(
            f"tier-2 (syntax+imports): {'; '.join(tier2_issues)}"
        )
    for cat in ("CAT1", "CAT2", "CAT3", "CAT4"):
        if cat_buckets[cat]:
            summary_lines.append(
                f"{cat}: {'; '.join(cat_buckets[cat])}"
            )

    prescription_text = " ".join(
        f"[{tag}] {text}" for tag, text in cat_prescriptions
    )
    if tier2_issues:
        prescription_text = (
            "Address the syntax/import issues, then "
            + prescription_text
        )

    parts.append(
        f"Re-dispatch with explicit focus on: {focus_str}. "
        f"Phase {phase.id} cleared tier 1 (presence) but failed tier 3 "
        f"(wiring) with: {' | '.join(summary_lines)}. "
        + prescription_text
    )

    if shadowing_entries:
        parts.append(_format_shadowing_prescription(phase, shadowing_entries))

    if acceptance_failure_entries:
        parts.append(_format_acceptance_prescription(
            phase, acceptance_failure_entries, acceptance_command
        ))

    return " ".join(parts)


def _format_shadowing_prescription(
    phase: PhaseInput, shadowing_entries: List[str]
) -> str:
    """Build the per-§3-worked-example shadowing prescription text. Each
    `[SHADOWING:...]` finding carries pipe-delimited fields embedded in
    its body — see `_run_tier35` for the format.
    """
    lines: List[str] = []
    for entry in shadowing_entries:
        # Strip the prefix, keep the structured detail.
        body = entry
        if body.startswith("[SHADOWING:"):
            close = body.find("]")
            if close != -1:
                body = body[close + 1 :].strip()
        lines.append(body)
    detail_block = " | ".join(lines)
    return (
        f"Re-dispatch with explicit focus on registry resolution: phase "
        f"{phase.id}'s runtime smoke test (tier 3.5) found one or more "
        f"registered symbols whose runtime source does NOT match the "
        f"PLAN.md-declared file. Details: {detail_block}. Either remove "
        f"the shadowing definition in the actual module, or update "
        f"PLAN.md to declare the actual source file. The intended "
        f"implementation must win at runtime — verify by re-running tier "
        f"3.5 after the fix."
    )


def _format_acceptance_prescription(
    phase: PhaseInput,
    acceptance_failure_entries: List[str],
    acceptance_command: Optional[str],
) -> str:
    """Build the per-§3 acceptance-failure prescription text. Each
    `[ACCEPTANCE_FAILED:N]` / `[ENVIRONMENT:..]` finding carries its
    structured detail in the body — see `_run_tier37` for the format.

    The body of an `[ACCEPTANCE_FAILED:N]` entry includes the captured
    stdout/stderr (already truncated by `_run_tier37`) so the parent can
    see the actual failure output, not just the exit code.
    """
    cmd_repr = (
        f"`{acceptance_command}`"
        if acceptance_command
        else "(unknown)"
    )
    failed = [
        e for e in acceptance_failure_entries
        if e.startswith("[ACCEPTANCE_FAILED:")
    ]
    env = [
        e for e in acceptance_failure_entries
        if e.startswith("[ENVIRONMENT:")
    ]
    out: List[str] = []
    if failed:
        detail_block = "\n\n".join(failed)
        out.append(
            f"Phase {phase.id} cleared tier 1 (presence) and tier 3 "
            f"(wiring) but failed tier 3.7 (acceptance command). "
            f"Command: {cmd_repr}. {detail_block} "
            "Re-dispatch with focus on making the acceptance command "
            "pass."
        )
    if env:
        detail_block = " | ".join(env)
        out.append(
            f"Phase {phase.id} acceptance command did not run cleanly. "
            f"Command: {cmd_repr}. {detail_block} This is an "
            "environment-side issue, not a code defect. Either fix the "
            "environment (install missing deps, adjust scaffold venv, "
            "ensure tests exist) or revise PLAN.md's acceptance_command "
            "to be runnable."
        )
    return " ".join(out)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def verify_phase(
    phase: PhaseInput,
    scaffold_root: Union[str, Path],
    *,
    tier: int = 2,
    presence_min_bytes: int = 50,
    presence_min_nonblank_lines: int = 3,
    project_phases: Optional[List[PhaseInput]] = None,
    with_runtime_smoke_test: bool = False,
    runtime_smoke_test_timeout: int = 10,
    cat1_extra_allow_list: Optional[List[str]] = None,
    acceptance_command: Optional[str] = None,
    acceptance_timeout_seconds: int = 120,
) -> VerifyResult:
    """Verify `phase`'s declared paths under `scaffold_root` at the
    requested tier.

    See module docstring for the resolution algorithm and phase-awareness
    semantics. Tier 1 always runs; tier 2 runs if tier >= 2 AND tier 1
    passed. Tier 4 raises NotImplementedError.

    Tier 3.5 (runtime smoke test) is opt-in via `with_runtime_smoke_test`.
    The Hermes tool wrapper (item 5) determines when to invoke it; this
    module just executes when asked. When True, tier 3.5 runs after the
    requested integer tier, but only if tiers 1 AND 2 passed (no point
    running runtime smoke if the code can't even parse). Tier 3.5 runs
    alongside tier 3 if `tier=3` is also requested — they're complementary.
    A `[SHADOWING]` finding sets `passed=False` and contributes to
    `corrective_dispatch`. `[INCONCLUSIVE]` findings do NOT affect
    `passed`. `[CHECKED]` findings are informational. See VerifyResult
    docstring for the full prefix taxonomy.

    `cat1_extra_allow_list` (added for item 5 / Hermes tool wrapper):
    optional list of additional top-level symbol names to exempt from
    the tier-3 CAT1 ``[CAT1:defined-unused]`` check, on top of the
    built-in `_PUBLIC_API_ALLOW_LIST` ({router, app, application, api}).
    Use cases: a project's web framework picks up `ws_app`, `lambda_handler`,
    or other public-API names by string-name lookup, which AST analysis
    cannot detect as a reference. Default `None` is identical to the
    pre-r7.11-item-5 behavior — only the built-in allow-list applies.
    Items 1-4's contracts are unchanged; this is a strictly additive
    seam for the Hermes tool wrapper to thread operator config through.

    Tier 3.7 (acceptance-runner) — implicit, gated on declaration:
      `acceptance_command` (added for r7.11 F-7 fix): an optional shell
      command parsed by `shlex.split` and run as a subprocess in
      `scaffold_root`, with the scaffold's `.venv/lib/.../site-packages`
      injected onto PYTHONPATH (B1 pattern from hermes_multi.py:498-508).
      Tier 3.7 runs ONLY when `acceptance_command` is non-None / non-empty
      AND tier 1 + tier 2 passed (mirrors the tier 3.5 gate). Unlike tier
      3.5, there is no opt-in flag — the field's presence IS the opt-in.
      `acceptance_timeout_seconds` (default 120) bounds the subprocess.
      Findings populate `acceptance_runner_findings` with the prefix
      taxonomy documented on `VerifyResult`. `[ACCEPTANCE_FAILED:N]` and
      `[ENVIRONMENT:..]` set passed=False; `[INCONCLUSIVE:..]`,
      `[ACCEPTANCE_PASSED]`, and `[SKIPPED]` do not.
    """
    if tier not in (1, 2, 3, 4):
        raise ValueError(
            f"unknown tier {tier!r}; expected one of 1, 2, 3, 4"
        )
    if tier == 4:
        raise NotImplementedError(
            "tier 4 not yet implemented in this build (item r7.12)"
        )

    scaffold_root = Path(scaffold_root)

    # ---- Tier 1: presence ----
    missing_paths: List[str] = []
    for rel in phase.paths:
        note = _check_presence_one(
            rel,
            scaffold_root,
            presence_min_bytes,
            presence_min_nonblank_lines,
        )
        if note is not None:
            missing_paths.append(note)

    if missing_paths:
        runtime_smoke_findings: List[str] = []
        if with_runtime_smoke_test:
            runtime_smoke_findings = [
                "[SKIPPED] tier 1 or 2 failed; runtime smoke test not "
                "attempted"
            ]
        acceptance_runner_findings: List[str] = []
        if acceptance_command:
            acceptance_runner_findings = [
                "[SKIPPED] tier 1 or 2 failed; acceptance command not "
                "attempted"
            ]
        result = VerifyResult(
            passed=False,
            tier_run=1,
            missing_paths=missing_paths,
            integrity_issues=[],
            runtime_smoke_findings=runtime_smoke_findings,
            acceptance_runner_findings=acceptance_runner_findings,
            semantic_concerns=[],
            corrective_dispatch="",
            persisted_to=None,
        )
        result.corrective_dispatch = _build_corrective_dispatch(
            phase, missing_paths, []
        )
        return result

    if tier == 1:
        runtime_smoke_findings = []
        if with_runtime_smoke_test:
            # Tier 1 only — tier 2 didn't run, but tier 1 passed. The
            # contract is "runs only if tiers 1 AND 2 passed". Tier 2
            # was not requested, so we still run tier 3.5 because tier
            # 1 passed and there's no tier-2 verdict to gate on. To stay
            # conservative AND to satisfy the gate, run an inline tier 2
            # check just for the smoke-test prerequisite. If it fails,
            # emit [SKIPPED]. This keeps tier_run=1 so we don't surprise
            # callers who asked for tier 1.
            tier2_issues = _compute_tier2_issues(
                phase, scaffold_root, project_phases
            )
            if tier2_issues:
                runtime_smoke_findings = [
                    "[SKIPPED] tier 1 or 2 failed; runtime smoke test "
                    "not attempted"
                ]
            else:
                runtime_smoke_findings = _run_tier35(
                    phase=phase,
                    scaffold_root=scaffold_root,
                    project_phases=project_phases,
                    timeout=runtime_smoke_test_timeout,
                )
        # Tier 3.7 mirrors the tier 3.5 gate: requires tier 1 AND tier 2.
        # When the caller asked only for tier 1, run an inline tier-2
        # check (same shape as the smoke gate above) so we don't run an
        # acceptance command on broken syntax.
        acceptance_runner_findings = []
        if acceptance_command:
            tier2_issues_for_accept = _compute_tier2_issues(
                phase, scaffold_root, project_phases
            )
            if tier2_issues_for_accept:
                acceptance_runner_findings = [
                    "[SKIPPED] tier 1 or 2 failed; acceptance command "
                    "not attempted"
                ]
            else:
                acceptance_runner_findings = _run_tier37(
                    phase=phase,
                    scaffold_root=scaffold_root,
                    acceptance_command=acceptance_command,
                    timeout_seconds=acceptance_timeout_seconds,
                )
        result = VerifyResult(
            passed=True,
            tier_run=1,
            missing_paths=[],
            integrity_issues=[],
            runtime_smoke_findings=runtime_smoke_findings,
            acceptance_runner_findings=acceptance_runner_findings,
            semantic_concerns=[],
            corrective_dispatch="",
            persisted_to=None,
        )
        # Tier 3.5 may invalidate passed even at tier_run=1.
        smoke_shadowing = any(
            f.startswith("[SHADOWING:") for f in runtime_smoke_findings
        )
        accept_failed = any(
            f.startswith("[ACCEPTANCE_FAILED:")
            or f.startswith("[ENVIRONMENT:")
            for f in acceptance_runner_findings
        )
        if smoke_shadowing or accept_failed:
            result.passed = False
            result.corrective_dispatch = _build_corrective_dispatch(
                phase, [], [],
                runtime_smoke_findings=runtime_smoke_findings,
                acceptance_runner_findings=acceptance_runner_findings,
                acceptance_command=acceptance_command,
            )
        return result

    # ---- Tier 2: syntax + imports ----
    integrity_issues: List[str] = []

    # Tolerated set: union of paths from OTHER phases (phase-awareness).
    tolerated_paths: Set[str] = set()
    if project_phases is not None:
        for other in project_phases:
            if other.id == phase.id:
                continue
            for p in other.paths:
                tolerated_paths.add(p)

    # The phase's own declared paths are also "known to exist now"; we
    # add them too so a same-phase relative import resolves without
    # disk-walking the whole scaffold.
    own_paths: Set[str] = set(phase.paths)

    for rel in phase.paths:
        if not rel.endswith(".py"):
            continue
        abs_path = scaffold_root / rel
        try:
            src = abs_path.read_text(encoding="utf-8")
        except OSError as exc:
            integrity_issues.append(f"{rel}: unreadable ({exc})")
            continue
        except UnicodeDecodeError:
            integrity_issues.append(f"{rel}: not valid UTF-8")
            continue

        try:
            tree = ast.parse(src, filename=rel)
        except SyntaxError as exc:
            integrity_issues.append(
                f"{rel}: SyntaxError on line {exc.lineno}: {exc.msg}"
            )
            continue

        # NotImplementedError check — non-test code only.
        is_test = _is_test_path(rel)
        if not is_test:
            for lineno in _find_notimplementederror_raises(tree):
                integrity_issues.append(
                    f"{rel}:{lineno}: raise NotImplementedError in non-test "
                    "code (use a real implementation)"
                )

        # Imports.
        for ref in _collect_imports(tree):
            issue = _check_import(
                ref=ref,
                file_rel=rel,
                file_abs=abs_path,
                scaffold_root=scaffold_root,
                tolerated_paths=tolerated_paths,
                own_paths=own_paths,
            )
            if issue is not None:
                integrity_issues.append(issue)

    # tier-2 verdict snapshot, used by tier 3.5 gate
    tier2_passed_for_smoke = not integrity_issues

    if tier == 2:
        passed = not integrity_issues
        runtime_smoke_findings = []
        if with_runtime_smoke_test:
            if not tier2_passed_for_smoke:
                runtime_smoke_findings = [
                    "[SKIPPED] tier 1 or 2 failed; runtime smoke test "
                    "not attempted"
                ]
            else:
                runtime_smoke_findings = _run_tier35(
                    phase=phase,
                    scaffold_root=scaffold_root,
                    project_phases=project_phases,
                    timeout=runtime_smoke_test_timeout,
                )
                if any(
                    f.startswith("[SHADOWING:")
                    for f in runtime_smoke_findings
                ):
                    passed = False
        # Tier 3.7 — same gate as tier 3.5.
        acceptance_runner_findings = []
        if acceptance_command:
            if not tier2_passed_for_smoke:
                acceptance_runner_findings = [
                    "[SKIPPED] tier 1 or 2 failed; acceptance command "
                    "not attempted"
                ]
            else:
                acceptance_runner_findings = _run_tier37(
                    phase=phase,
                    scaffold_root=scaffold_root,
                    acceptance_command=acceptance_command,
                    timeout_seconds=acceptance_timeout_seconds,
                )
                if any(
                    f.startswith("[ACCEPTANCE_FAILED:")
                    or f.startswith("[ENVIRONMENT:")
                    for f in acceptance_runner_findings
                ):
                    passed = False
        result = VerifyResult(
            passed=passed,
            tier_run=2,
            missing_paths=[],
            integrity_issues=integrity_issues,
            runtime_smoke_findings=runtime_smoke_findings,
            acceptance_runner_findings=acceptance_runner_findings,
            semantic_concerns=[],
            corrective_dispatch="",
            persisted_to=None,
        )
        if not passed:
            result.corrective_dispatch = _build_corrective_dispatch(
                phase,
                [],
                integrity_issues,
                runtime_smoke_findings=runtime_smoke_findings,
                acceptance_runner_findings=acceptance_runner_findings,
                acceptance_command=acceptance_command,
            )
        return result

    # ---- Tier 3: wiring ----
    # Even if tier-2 found integrity issues, tier-3 still runs (the
    # caller asked for tier 3). Tier-3 findings append to integrity_issues
    # with the [CATn:...] prefix, so callers can split by prefix.
    tier3_issues, tier_3_hint = _run_tier3(
        phase=phase,
        scaffold_root=scaffold_root,
        tolerated_paths=tolerated_paths,
        project_phases=project_phases,
        cat1_extra_allow_list=cat1_extra_allow_list,
    )
    integrity_issues.extend(tier3_issues)

    runtime_smoke_findings = []
    if with_runtime_smoke_test:
        if not tier2_passed_for_smoke:
            runtime_smoke_findings = [
                "[SKIPPED] tier 1 or 2 failed; runtime smoke test not "
                "attempted"
            ]
        else:
            runtime_smoke_findings = _run_tier35(
                phase=phase,
                scaffold_root=scaffold_root,
                project_phases=project_phases,
                timeout=runtime_smoke_test_timeout,
            )

    # Tier 3.7 — first execution-based tier. Gated on tier 1 + tier 2.
    # Default-on when acceptance_command is declared (the field's
    # presence IS the opt-in; no separate flag).
    acceptance_runner_findings: List[str] = []
    if acceptance_command:
        if not tier2_passed_for_smoke:
            acceptance_runner_findings = [
                "[SKIPPED] tier 1 or 2 failed; acceptance command not "
                "attempted"
            ]
        else:
            acceptance_runner_findings = _run_tier37(
                phase=phase,
                scaffold_root=scaffold_root,
                acceptance_command=acceptance_command,
                timeout_seconds=acceptance_timeout_seconds,
            )

    smoke_shadowing = any(
        f.startswith("[SHADOWING:") for f in runtime_smoke_findings
    )
    accept_failed = any(
        f.startswith("[ACCEPTANCE_FAILED:")
        or f.startswith("[ENVIRONMENT:")
        for f in acceptance_runner_findings
    )
    passed = (
        (not integrity_issues)
        and (not smoke_shadowing)
        and (not accept_failed)
    )
    result = VerifyResult(
        passed=passed,
        tier_run=3,
        missing_paths=[],
        integrity_issues=integrity_issues,
        runtime_smoke_findings=runtime_smoke_findings,
        acceptance_runner_findings=acceptance_runner_findings,
        semantic_concerns=[],
        corrective_dispatch="",
        persisted_to=None,
        tier_3_hint=tier_3_hint,
    )
    if not passed:
        result.corrective_dispatch = _build_corrective_dispatch(
            phase,
            [],
            integrity_issues,
            runtime_smoke_findings=runtime_smoke_findings,
            acceptance_runner_findings=acceptance_runner_findings,
            acceptance_command=acceptance_command,
        )
    return result


def _check_import(
    ref: _ImportRef,
    file_rel: str,
    file_abs: Path,
    scaffold_root: Path,
    tolerated_paths: Set[str],
    own_paths: Set[str],
) -> Optional[str]:
    """Resolve a single import. Return None on hit (or deferred);
    return an integrity-issue string on miss."""
    if ref.absolute:
        if not ref.module:
            # `import` with empty module shouldn't occur, but be safe.
            return None
        # 1. Project-relative.
        hit = _resolve_absolute_project(ref.module, scaffold_root)
        if hit is not None:
            return None
        # 2. Tolerated (cross-phase declared).
        tolerated_match = _is_tolerated_module_unresolved(
            ref.module, scaffold_root, tolerated_paths
        )
        if tolerated_match is not None:
            # Deferred — informational; not an integrity issue.
            return None
        # Also tolerate same-phase declared paths if they happen to
        # match (e.g., a phase declares two files and one imports the
        # other — but only the importer is on disk by the time we run).
        # In practice tier 1 already verified all own_paths exist, so
        # this branch is unlikely to fire. Defensive.
        own_match = _is_tolerated_module_unresolved(
            ref.module, scaffold_root, own_paths
        )
        if own_match is not None:
            return None
        # 3. Venv / stdlib.
        if _resolve_absolute_venv(ref.module):
            return None
        # 4. Miss.
        return (
            f"{file_rel}:{ref.lineno}: unresolvable import "
            f"`{ref.module}` (not present in scaffold and not found via "
            "importlib.util.find_spec)"
        )
    else:
        # Relative import.
        hit = _resolve_relative(
            file_abs, scaffold_root, ref.level, ref.module
        )
        if hit is not None:
            return None
        # Tolerated cross-phase / own-phase.
        tolerated_match = _is_tolerated_relative_unresolved(
            file_abs, scaffold_root, ref.level, ref.module, tolerated_paths
        )
        if tolerated_match is not None:
            return None
        own_match = _is_tolerated_relative_unresolved(
            file_abs, scaffold_root, ref.level, ref.module, own_paths
        )
        if own_match is not None:
            return None
        rel_repr = "." * ref.level + (ref.module or "")
        return (
            f"{file_rel}:{ref.lineno}: unresolvable relative import "
            f"`{rel_repr}` (not present in scaffold under the file's "
            "package directory)"
        )


# ---------------------------------------------------------------------------
# Tier-3 helpers — wiring analyzer
# ---------------------------------------------------------------------------


# Default allow-list for "public-API" top-level names that are commonly
# defined and consumed by an external runtime (a web framework picks
# them up by name, not by Python-level reference). To extend the
# allow-list, edit this constant or — once item 5 is wired — extend
# from the Hermes tool wrapper before calling. We deliberately keep the
# list small; false negatives (we let a truly-unused symbol slide) are
# preferable to false positives (we flag a working FastAPI router).
_PUBLIC_API_ALLOW_LIST: Set[str] = {
    "router",
    "app",
    "application",
    "api",
}


@dataclass
class _FileAnalysis:
    """Cache of per-file AST-derived facts used across tier-3 categories."""

    path_rel: str
    is_test: bool
    tree: Optional[ast.AST]
    src: str
    # Top-level definitions: function name -> set of dunder/regular flag
    defined_names: Set[str] = field(default_factory=set)
    # Top-level definitions classified
    defined_funcs: Set[str] = field(default_factory=set)
    defined_classes: Set[str] = field(default_factory=set)
    defined_vars: Set[str] = field(default_factory=set)
    # __all__ entries (string literals only)
    all_exports: Set[str] = field(default_factory=set)
    # Imports — bound names introduced into the file's namespace
    # alias_name -> (module_str_used_for_resolution, original_name, lineno)
    imported_aliases: dict = field(default_factory=dict)
    # Names referenced anywhere in the module body (Name, Attribute roots)
    used_names: Set[str] = field(default_factory=set)
    # (module_str, level, [(imported_name, lineno), ...]) tuples for
    # `from M import x, y` so tier-3 CAT3 can walk the tests' imports.
    from_imports: List[Tuple[str, int, List[Tuple[str, int]]]] = field(
        default_factory=list
    )
    # Names used inside `if TYPE_CHECKING:` blocks — these don't count
    # as "used" for runtime-imports BUT do qualify as type-only usage
    # (so we don't flag `from __future__ import annotations` style
    # imports nested in TYPE_CHECKING). See _CAT2.
    typecheck_imported_aliases: Set[str] = field(default_factory=set)


def _read_python_file(
    path_rel: str, scaffold_root: Path
) -> Optional[_FileAnalysis]:
    """Read & parse a Python file. Return None if the file doesn't
    exist on disk OR isn't Python OR fails to parse. Tier-3 silently
    skips bad files; tier 2 already reported them."""
    abs_path = scaffold_root / path_rel
    if not abs_path.is_file():
        return None
    if not path_rel.endswith(".py"):
        return None
    try:
        src = abs_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        tree = ast.parse(src, filename=path_rel)
    except SyntaxError:
        return None
    fa = _FileAnalysis(
        path_rel=path_rel,
        is_test=_is_test_path(path_rel),
        tree=tree,
        src=src,
    )
    _populate_file_analysis(fa)
    return fa


def _populate_file_analysis(fa: _FileAnalysis) -> None:
    tree = fa.tree
    if tree is None:
        return
    # --- top-level definitions ---
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fa.defined_funcs.add(node.name)
            fa.defined_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            fa.defined_classes.add(node.name)
            fa.defined_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    fa.defined_vars.add(t.id)
                    fa.defined_names.add(t.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                fa.defined_vars.add(node.target.id)
                fa.defined_names.add(node.target.id)

    # --- __all__ extraction (string-literal entries only) ---
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(
                                elt.value, str
                            ):
                                fa.all_exports.add(elt.value)

    # --- imports (collect bound names + structure) ---
    # We need to know whether an import is inside `if TYPE_CHECKING:`
    # to apply the CAT2 type-checking exemption. Walk top-level only
    # (TYPE_CHECKING is a top-level conditional in idiomatic code).
    def _is_typecheck_if(node: ast.AST) -> bool:
        if not isinstance(node, ast.If):
            return False
        t = node.test
        if isinstance(t, ast.Name) and t.id == "TYPE_CHECKING":
            return True
        if isinstance(t, ast.Attribute) and t.attr == "TYPE_CHECKING":
            return True
        return False

    def _record_imports(stmt: ast.AST, in_typecheck: bool) -> None:
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                bound = alias.asname or alias.name.split(".")[0]
                if in_typecheck:
                    fa.typecheck_imported_aliases.add(bound)
                else:
                    fa.imported_aliases[bound] = (
                        alias.name,
                        alias.name,
                        stmt.lineno,
                    )
        elif isinstance(stmt, ast.ImportFrom):
            module = stmt.module or ""
            level = stmt.level or 0
            names_pairs: List[Tuple[str, int]] = []
            for alias in stmt.names:
                if alias.name == "*":
                    continue
                bound = alias.asname or alias.name
                if in_typecheck:
                    fa.typecheck_imported_aliases.add(bound)
                else:
                    fa.imported_aliases[bound] = (
                        module,
                        alias.name,
                        stmt.lineno,
                    )
                names_pairs.append((alias.name, stmt.lineno))
            fa.from_imports.append((module, level, names_pairs))

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            _record_imports(node, in_typecheck=False)
        elif _is_typecheck_if(node):
            for sub in node.body:
                if isinstance(sub, (ast.Import, ast.ImportFrom)):
                    _record_imports(sub, in_typecheck=True)

    # --- used names (Name + Attribute root) anywhere in the module ---
    # Skip the actual Import/ImportFrom and the `__all__ = [...]`
    # node, since those introduce the names rather than use them.
    # For Attribute(value=Name(id='X')), we record X as used. For
    # nested attributes Attribute(value=Attribute(...), ...), the
    # ast.walk traversal still hits the leaf Name node.
    skip_nodes: Set[int] = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            skip_nodes.add(id(node))
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__"
            for t in node.targets
        ):
            skip_nodes.add(id(node))

    def _walk_uses(parent: ast.AST) -> None:
        for node in ast.walk(parent):
            if id(node) in skip_nodes:
                continue
            if isinstance(node, ast.Name):
                # `Store` context = definition, not use.
                if not isinstance(node.ctx, ast.Store):
                    fa.used_names.add(node.id)

    for node in tree.body:
        if id(node) in skip_nodes:
            continue
        _walk_uses(node)


# ---------- CAT1: defined-but-never-referenced ----------


def _cat1_defined_unused(
    own: List[_FileAnalysis],
    cross: List[_FileAnalysis],
    allow_list: Set[str],
    tolerated_has_pending: bool,
) -> List[str]:
    """For each top-level definition in phase-N files, flag if no
    reference exists across phase-N + tolerated-phase files (on disk).
    Skips dunders (`__*__` names), allow-listed public names, and
    `__all__` exports.

    Conservative cross-phase rule (`tolerated_has_pending=True`):
    when project_phases declares paths in OTHER phases that are not
    yet on disk, we cannot inspect those files for references. To
    avoid false positives during phased construction, CAT1 is fully
    suppressed in this case. This matches the §3 phase-awareness
    contract: cross-phase symbols are deferred, not flagged.
    """
    issues: List[str] = []
    if tolerated_has_pending:
        return issues

    # Build the union "used_names" set across all visible files
    # (phase-N + tolerated phase-M files that exist on disk).
    used_anywhere: Set[str] = set()
    for fa in own + cross:
        used_anywhere.update(fa.used_names)

    for fa in own:
        # Don't flag inside test files; per spec, test fixtures /
        # locally-defined helpers may be unused-from-elsewhere by
        # design (they're invoked by the test runner / referenced by
        # name within the same file or via fixtures).
        if fa.is_test:
            continue
        for name in sorted(fa.defined_funcs | fa.defined_classes
                           | fa.defined_vars):
            if name.startswith("__") and name.endswith("__"):
                continue
            if name in allow_list:
                continue
            if name in fa.all_exports:
                continue
            # If this file declares __all__, anything NOT in __all__
            # is private and must be referenced internally to be
            # considered used. (Standard Python convention.)
            if name in used_anywhere:
                continue
            kind = (
                "function"
                if name in fa.defined_funcs
                else "class"
                if name in fa.defined_classes
                else "variable"
            )
            issues.append(
                f"[CAT1:defined-unused] {fa.path_rel} — {kind} "
                f"`{name}` defined but never referenced"
            )
    return issues


# ---------- CAT2: imported-but-never-used ----------


def _cat2_imported_unused(own: List[_FileAnalysis]) -> List[str]:
    issues: List[str] = []
    for fa in own:
        for bound, (module, orig, lineno) in fa.imported_aliases.items():
            if bound in fa.all_exports:
                continue
            if bound in fa.used_names:
                continue
            # Conservative side-effect-import skip: if the bound name
            # equals the imported module's first part AND it appears
            # in __init__.py-style top-level (module name == file's
            # parent dir), don't flag. We can't easily tell, so be
            # conservative: skip when the alias matches a "logging"-
            # style stdlib package.
            issues.append(
                f"[CAT2:imported-unused] {fa.path_rel}:{lineno} — "
                f"import `{bound}` (from `{module}`) declared but "
                "never used"
            )
    return issues


# ---------- CAT3: tests reference nonexistent symbols ----------


def _resolve_from_module_to_file(
    fa: _FileAnalysis,
    module: str,
    level: int,
    own: List[_FileAnalysis],
    cross: List[_FileAnalysis],
    scaffold_root: Path,
) -> Optional[_FileAnalysis]:
    """Resolve the impl-file FROM which a test is importing. Returns
    the matching _FileAnalysis if the impl is on-disk and parsed; None
    if the impl resolves to something not analyzed (stdlib / venv /
    cross-phase-not-on-disk).

    We resolve in the same order as tier-2:
      1. Project-relative (own + cross union).
      2. Otherwise: None (the caller treats this as "not analyzed").
    """
    # Build a path -> FileAnalysis map for lookup.
    by_path = {a.path_rel: a for a in own + cross}

    if level > 0:
        # Relative import: walk up `level-1` from the file's package dir.
        rel_parts = list(Path(fa.path_rel).parts)[:-1]
        up = level - 1
        if up > len(rel_parts):
            return None
        package_parts = (
            rel_parts[: len(rel_parts) - up] if up else rel_parts
        )
        sub = module.split(".") if module else []
        full = package_parts + sub
        if not full:
            return None
        base = "/".join(full)
        for cand in (base + ".py", base + "/__init__.py"):
            if cand in by_path:
                return by_path[cand]
        return None

    # Absolute import: try most-specific module/package first.
    for cand in _module_to_candidate_paths(module):
        if cand in by_path:
            return by_path[cand]
    return None


def _cat3_test_references_nonexistent(
    own: List[_FileAnalysis],
    cross: List[_FileAnalysis],
    scaffold_root: Path,
) -> List[str]:
    issues: List[str] = []
    for fa in own:
        if not fa.is_test:
            continue
        for module, level, names_pairs in fa.from_imports:
            if not names_pairs:
                continue
            target = _resolve_from_module_to_file(
                fa, module, level, own, cross, scaffold_root
            )
            if target is None:
                # Not on-disk impl: stdlib, venv, or cross-phase-deferred.
                # Don't flag.
                continue
            for name, lineno in names_pairs:
                if name in target.defined_names:
                    continue
                if name in target.imported_aliases:
                    # Re-export — let it pass.
                    continue
                if name in target.all_exports:
                    continue
                issues.append(
                    f"[CAT3:test-references-nonexistent] {fa.path_rel}:"
                    f"{lineno} — symbol `{name}` not defined in "
                    f"`{target.path_rel}` (test imports from named "
                    "impl file but symbol is missing)"
                )
    return issues


# ---------- CAT4: duplicate top-level definitions ----------


def _cat4_duplicate_definition(
    own: List[_FileAnalysis],
    cross: List[_FileAnalysis],
    orphans: Optional[List[_FileAnalysis]] = None,
) -> List[str]:
    """Flag the same top-level symbol name defined in 2+ files across
    phase-N + tolerated phase-M (on-disk) + ORPHAN baseline files.

    `orphans` is a list of `_FileAnalysis` for .py files discovered
    under `<scaffold_root>/src/` and `<scaffold_root>/tests/` that are
    NOT declared in any PLAN.md phase (see `_discover_orphan_files`).
    These files are invisible to PLAN.md-driven analysis but can carry
    colliding top-level symbols (the r7.11 F-9 trial archetype: a
    baseline stub like `src/api/export.py` ships with active code that
    the parent shadows by creating a parallel file, e.g.
    `src/api/export_routes.py`, instead of editing the stub in place).

    Detection rule: any top-level symbol defined in OWN (phase-N) AND
    also in any other location (cross OR orphan) flags a finding. When
    one or more orphan files participate in the collision, the finding
    text includes the substring "orphan baseline stub" against each
    orphan path so the parent gets a clear remediation hint
    (delete/empty the orphan OR rewrite the phase to declare and modify
    the orphan in-place, instead of creating a parallel file).

    Test-fixture exception: duplicates that live entirely inside test
    files don't flag — this matches the existing CAT4 exception and
    extends it to orphan test files (e.g. an orphan
    `tests/test_helpers.py` defining `make_record` alongside an own
    `tests/test_x.py` defining the same fixture).
    """
    orphans = orphans or []
    issues: List[str] = []
    # name -> [(path_rel, is_test, is_orphan), ...]
    name_to_files: dict = {}
    own_paths = {fa.path_rel for fa in own}
    orphan_paths = {fa.path_rel for fa in orphans}
    for fa in own + cross + orphans:
        is_orphan = fa.path_rel in orphan_paths
        for name in fa.defined_funcs | fa.defined_classes | fa.defined_vars:
            # Dunders are per-class on classes; here we're iterating
            # top-level definitions. A top-level dunder like
            # `__version__` could legitimately appear in two packages —
            # but more often it's a sign of duplication. We exempt
            # `__all__`, `__version__`, and `__author__` as common
            # multi-module top-level declarations.
            if name in {"__all__", "__version__", "__author__"}:
                continue
            name_to_files.setdefault(name, []).append(
                (fa.path_rel, fa.is_test, is_orphan)
            )

    for name, locations in sorted(name_to_files.items()):
        if len(locations) < 2:
            continue
        # Only flag if at least one location is in OWN (phase-N). The
        # orphan-vs-orphan or orphan-vs-cross-only case is not phase-N's
        # responsibility to remediate; phase-N didn't introduce it.
        own_locs = [loc for loc in locations if loc[0] in own_paths]
        if not own_locs:
            continue
        # Test-fixture exception: every location is a test file
        # (covers orphan test fixtures too, mirroring CAT4 spirit).
        if all(is_test for (_, is_test, _) in locations):
            continue
        # Render the file list. Annotate orphan participants explicitly
        # so the parent's remediation path is unambiguous. The substring
        # "orphan baseline stub" is load-bearing — F-9 mitigation hooks
        # downstream tooling (and humans grepping logs) on it.
        rendered: List[str] = []
        for (p, _is_test, is_orph) in locations:
            if is_orph:
                rendered.append(f"`{p}` — orphan baseline stub")
            else:
                rendered.append(f"`{p}`")
        files_list = ", ".join(rendered)
        any_orphan = any(is_orph for (_, _, is_orph) in locations)
        if any_orphan:
            # Tailored remediation hint for the orphan-collision shape.
            issues.append(
                f"[CAT4:duplicate-definition] symbol `{name}` defined in "
                f"multiple files: {files_list} — the orphan is not "
                "declared in any PLAN.md phase; either delete or empty "
                "the orphan, OR rewrite the phase to declare and modify "
                "the orphan in-place instead of creating a parallel file"
            )
        else:
            issues.append(
                f"[CAT4:duplicate-definition] symbol `{name}` defined in "
                f"multiple files: {files_list} (choose one canonical "
                "definition; runtime-shadowing risk)"
            )
    return issues


# ---------- orphan discovery (feeds CAT4 orphan-collision detection) ----------


def _discover_orphan_files(
    scaffold_root: Path,
    declared_paths: Set[str],
) -> List[_FileAnalysis]:
    """Walk `<scaffold_root>/src/` and `<scaffold_root>/tests/` for
    .py files NOT in `declared_paths` (the union of every phase's
    `paths`). Return parsed `_FileAnalysis` entries; silently skip
    unreadable / unparseable files (tier 2 already reports those for
    declared paths; orphans are by definition outside that contract).

    Walk scope is restricted to `src/` and `tests/` to avoid pulling in
    repo-level scaffolding (top-level scripts, docs, conftest stubs in
    the root, etc.). A scaffold with a non-conventional layout — e.g.
    code under `lib/` or `app/` — is out of scope; the convention
    documented in `scaffold-baseline/CONVENTION.md` explicitly assumes
    `src/` + `tests/`. The tradeoff: a few false negatives (collisions
    in non-conventional layouts) vs a hard cap on scan cost and false
    positives from unrelated repo files.

    Excluded subtrees: `.venv/`, `__pycache__/`, `.pytest_cache/`,
    `.git/`, and any directory whose name starts with `.` (hidden).

    Normalization (added 2026-04-29 after r7.11 trial-4 escalation):
    `declared_paths` is a `Set[str]` whose entries may be absolute or
    relative depending on what PLAN.md authors wrote — real PLAN.md
    files commonly use absolute paths matching the scaffold_root prefix
    (e.g. `/tmp/scaffold/src/foo.py`), while the rglob walker yields
    relative path strings (`src/foo.py`). Naive string comparison
    therefore misclassifies legitimately-declared files as orphans,
    producing spurious CAT4 self-collisions. Fix: normalize BOTH sides
    via `Path.resolve()` (canonicalizes absolute-ness, `..` segments,
    and symlinks) and compare resolved `Path` objects, not strings.
    Relative declared paths are first joined to `scaffold_root` so
    they resolve under the scaffold; absolute paths resolve as-is.
    The `rel` argument passed to `_read_python_file` remains the
    walker-relative string so finding-text shape is preserved.
    """
    # Normalize declared paths once: absolute paths resolve as-is;
    # relative paths are joined to `scaffold_root` first. Pathologically
    # broken paths (symlink loops, OS errors) are skipped — the
    # comparison then treats them as not-in-set, which is the
    # conservative-but-acceptable failure mode for input that shouldn't
    # appear in well-formed PLAN.md files anyway.
    declared_resolved: Set[Path] = set()
    for p in declared_paths:
        candidate = Path(p)
        if not candidate.is_absolute():
            candidate = scaffold_root / candidate
        try:
            declared_resolved.add(candidate.resolve())
        except (OSError, RuntimeError):
            continue

    orphans: List[_FileAnalysis] = []
    excluded_dirs = {".venv", "__pycache__", ".pytest_cache", ".git"}
    for top in ("src", "tests"):
        root_dir = scaffold_root / top
        if not root_dir.is_dir():
            continue
        for path in root_dir.rglob("*.py"):
            # Skip excluded subtrees and hidden directories.
            rel_parts = path.relative_to(scaffold_root).parts
            if any(
                part in excluded_dirs or part.startswith(".")
                for part in rel_parts
            ):
                continue
            try:
                walker_resolved = path.resolve()
            except (OSError, RuntimeError):
                continue
            if walker_resolved in declared_resolved:
                continue
            rel = "/".join(rel_parts)
            fa = _read_python_file(rel, scaffold_root)
            if fa is not None:
                orphans.append(fa)
    return orphans


# ---------- dynamic-dispatch detection (sets tier_3_hint) ----------


_DYNAMIC_DISPATCH_HINT = (
    "this phase contains dynamic imports; consider invoking tier 3.5 "
    "runtime smoke test for full coverage"
)


def _scan_dynamic_dispatch(own: List[_FileAnalysis]) -> bool:
    """Return True if ANY phase-N file contains a dynamic-dispatch
    marker.

    Patterns checked (AST-level only; obfuscated cases are out of
    scope and intentionally left for tier 3.5):

      - importlib.import_module(...)            -> Call(Attribute)
      - importlib.util.find_spec(...).loader.exec_module(...)
                                                -> Attribute chain
      - __import__(...)                         -> Call(Name="__import__")
      - pkgutil.import_module(...) (rare)       -> Attribute
      - getattr(M, ...) where M is in imported_aliases
                                                -> Call(Name="getattr")
      - setattr(M, ...) where M is in imported_aliases
                                                -> Call(Name="setattr")
      - exec(...), eval(...)                    -> Call(Name)
      - globals()[...] = / locals()[...] =      -> Subscript on Call
    """
    for fa in own:
        if fa.tree is None:
            continue
        module_aliases = set(fa.imported_aliases.keys())
        for node in ast.walk(fa.tree):
            if isinstance(node, ast.Call):
                func = node.func
                # __import__ / exec / eval (bare-name calls)
                if isinstance(func, ast.Name) and func.id in {
                    "__import__",
                    "exec",
                    "eval",
                }:
                    return True
                # getattr/setattr where first arg is an imported module
                if isinstance(func, ast.Name) and func.id in {
                    "getattr",
                    "setattr",
                }:
                    if node.args and isinstance(node.args[0], ast.Name):
                        if node.args[0].id in module_aliases:
                            return True
                # importlib.import_module / pkgutil.import_module /
                # importlib.util.find_spec
                if isinstance(func, ast.Attribute):
                    if func.attr in {
                        "import_module",
                        "find_spec",
                        "exec_module",
                        "load_module",
                    }:
                        return True
            # globals()[...] / locals()[...] assignments / mutations
            if isinstance(node, ast.Subscript):
                v = node.value
                if (
                    isinstance(v, ast.Call)
                    and isinstance(v.func, ast.Name)
                    and v.func.id in {"globals", "locals"}
                ):
                    # Only flag when used as an assignment target. Read
                    # access is rarer & less load-bearing.
                    if isinstance(node.ctx, ast.Store):
                        return True
    return False


# ---------- Tier-3 driver ----------


def _run_tier3(
    phase: PhaseInput,
    scaffold_root: Path,
    tolerated_paths: Set[str],
    project_phases: Optional[List[PhaseInput]],
    cat1_extra_allow_list: Optional[List[str]] = None,
) -> Tuple[List[str], Optional[str]]:
    """Run all four wiring categories + dynamic-dispatch scan. Return
    (integrity_issues_with_CAT_prefix, tier_3_hint_or_None).

    `cat1_extra_allow_list` extends the built-in CAT1 public-API
    allow-list. Default None preserves prior behavior.
    """
    own_analyses: List[_FileAnalysis] = []
    cross_analyses: List[_FileAnalysis] = []

    for rel in phase.paths:
        fa = _read_python_file(rel, scaffold_root)
        if fa is not None:
            own_analyses.append(fa)

    # Tolerated phase files that exist on disk count toward "references"
    # and "duplicate-definition" reachability.
    tolerated_has_pending = False
    if project_phases is not None:
        for other in project_phases:
            if other.id == phase.id:
                continue
            for rel in other.paths:
                if not rel.endswith(".py"):
                    # Non-Python tolerated paths can't reference Python
                    # symbols; they don't gate CAT1.
                    continue
                fa = _read_python_file(rel, scaffold_root)
                if fa is None:
                    # File declared by another phase but not yet on disk
                    # (or unreadable / unparseable). Suppress CAT1 to
                    # avoid false positives during phased construction.
                    tolerated_has_pending = True
                else:
                    cross_analyses.append(fa)

    effective_allow_list = _PUBLIC_API_ALLOW_LIST | set(
        cat1_extra_allow_list or []
    )

    # Orphan discovery (r7.11 F-9 mitigation, part B): any .py file
    # under scaffold_root/src/ or /tests/ that's NOT declared in any
    # phase's `paths`. These are invisible to CAT1-CAT3 (which key off
    # PLAN.md declarations) but can carry colliding top-level symbols
    # — the trial-3 archetype where `src/api/export.py` (orphan
    # baseline stub) collides with phase-N's `src/api/export_routes.py`.
    declared_paths: Set[str] = set(phase.paths)
    if project_phases is not None:
        for other in project_phases:
            for rel in other.paths:
                declared_paths.add(rel)
    orphan_analyses = _discover_orphan_files(scaffold_root, declared_paths)

    issues: List[str] = []
    issues.extend(
        _cat1_defined_unused(
            own_analyses,
            cross_analyses,
            effective_allow_list,
            tolerated_has_pending=tolerated_has_pending,
        )
    )
    issues.extend(_cat2_imported_unused(own_analyses))
    issues.extend(
        _cat3_test_references_nonexistent(
            own_analyses, cross_analyses, scaffold_root
        )
    )
    issues.extend(
        _cat4_duplicate_definition(
            own_analyses, cross_analyses, orphan_analyses
        )
    )

    hint: Optional[str] = None
    if _scan_dynamic_dispatch(own_analyses):
        hint = _DYNAMIC_DISPATCH_HINT

    return issues, hint


# ---------------------------------------------------------------------------
# Tier-3.5 — runtime smoke test (subprocess sandbox)
# ---------------------------------------------------------------------------


_TIER35_SENTINEL_START = "===TIER35-FINDINGS-START==="
_TIER35_SENTINEL_END = "===TIER35-FINDINGS-END==="


def _compute_tier2_issues(
    phase: PhaseInput,
    scaffold_root: Path,
    project_phases: Optional[List[PhaseInput]],
) -> List[str]:
    """Recompute tier-2 integrity issues. Used by the tier 3.5 gate when
    `tier=1` was requested but the caller still asked for runtime smoke;
    we need a tier-2 verdict before deciding whether to proceed.

    This is a pure read-only check; no side effects.
    """
    integrity_issues: List[str] = []
    tolerated_paths: Set[str] = set()
    if project_phases is not None:
        for other in project_phases:
            if other.id == phase.id:
                continue
            for p in other.paths:
                tolerated_paths.add(p)
    own_paths: Set[str] = set(phase.paths)

    for rel in phase.paths:
        if not rel.endswith(".py"):
            continue
        abs_path = scaffold_root / rel
        try:
            src = abs_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            integrity_issues.append(f"{rel}: unreadable / not utf-8")
            continue
        try:
            tree = ast.parse(src, filename=rel)
        except SyntaxError as exc:
            integrity_issues.append(
                f"{rel}: SyntaxError on line {exc.lineno}: {exc.msg}"
            )
            continue
        if not _is_test_path(rel):
            for lineno in _find_notimplementederror_raises(tree):
                integrity_issues.append(
                    f"{rel}:{lineno}: raise NotImplementedError in non-test "
                    "code"
                )
        for ref in _collect_imports(tree):
            issue = _check_import(
                ref=ref,
                file_rel=rel,
                file_abs=abs_path,
                scaffold_root=scaffold_root,
                tolerated_paths=tolerated_paths,
                own_paths=own_paths,
            )
            if issue is not None:
                integrity_issues.append(issue)
    return integrity_issues


def _path_to_module_name(path_rel: str) -> Optional[str]:
    """Convert 'src/export/pdf.py' -> 'src.export.pdf'. Returns None for
    non-Python paths or paths with components that aren't valid Python
    identifiers (e.g. 'my-pkg/x.py'). __init__.py becomes the package
    name."""
    if not path_rel.endswith(".py"):
        return None
    parts = list(Path(path_rel).parts)
    if not parts:
        return None
    last = parts[-1]
    if last == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = last[:-3]
    if not parts:
        return None
    for p in parts:
        if not p.isidentifier():
            return None
    return ".".join(parts)


# Top-level package roots considered "in-project". The probe script
# collects modules whose names start with any of these. Computed at
# probe-script generation time from the phase's declared paths.
def _collect_top_level_packages(
    phase: PhaseInput, project_phases: Optional[List[PhaseInput]]
) -> List[str]:
    roots: Set[str] = set()
    all_phases = [phase]
    if project_phases is not None:
        all_phases = list(project_phases)
    for ph in all_phases:
        for p in ph.paths:
            if not p.endswith(".py"):
                continue
            mod = _path_to_module_name(p)
            if mod is None:
                continue
            roots.add(mod.split(".")[0])
    return sorted(roots)


# The probe script — runs in the subprocess. It receives JSON via argv[1]
# describing what to import + which top-level packages to scan. It prints
# a JSON blob between the sentinels documented in TIER35-NOTES.md.
#
# Kept as a string (not a separate file) so verify_phase remains
# single-file. The string is dedented, then dropped into a temp .py.
_TIER35_PROBE_SCRIPT = textwrap.dedent(
    """
    import importlib
    import json
    import os
    import sys
    import traceback

    SENTINEL_START = "===TIER35-FINDINGS-START==="
    SENTINEL_END = "===TIER35-FINDINGS-END==="

    REGISTRY_NAME_PATTERNS = (
        # Exact-match canonical names (case-sensitive).
        "_REGISTRY", "REGISTRY", "_FORMATS", "FORMATS",
        "registry", "_registry", "_handlers", "HANDLERS",
        "_serializers", "SERIALIZERS",
    )
    REGISTRY_SUBSTRING_PATTERNS = ("_registry", "_handlers", "_serializers")


    def _looks_like_registry_name(name):
        if name in REGISTRY_NAME_PATTERNS:
            return True
        lower = name.lower()
        for sub in REGISTRY_SUBSTRING_PATTERNS:
            if sub in lower:
                return True
        return False


    def _has_register_and_get(obj):
        try:
            return callable(getattr(obj, "register", None)) and callable(
                getattr(obj, "get", None)
            )
        except Exception:
            return False


    def _entry_module(value):
        # For class objects, the module that defines them.
        # For instances, the module of the class.
        try:
            if isinstance(value, type):
                return getattr(value, "__module__", "<unknown>")
            cls = type(value)
            return getattr(cls, "__module__", "<unknown>")
        except Exception:
            return "<unknown>"


    def _entry_qualname(value):
        try:
            if isinstance(value, type):
                return getattr(value, "__qualname__", repr(value))
            return type(value).__qualname__
        except Exception:
            return repr(value)


    def _is_dict_like(obj):
        # Consider dict + subclasses + objects with .items() that returns
        # an iterable of (k, v). For safety, only treat actual dicts as
        # registries detected by name (the duck-typed branch is for
        # objects with register/get).
        return isinstance(obj, dict)


    def main():
        spec = json.loads(sys.argv[1])
        scaffold_root = spec["scaffold_root"]
        modules_to_import = spec["modules"]
        top_level_packages = spec["top_level_packages"]

        sys.path.insert(0, scaffold_root)

        import_errors = []
        imported = []

        for mod_name in modules_to_import:
            try:
                importlib.import_module(mod_name)
                imported.append(mod_name)
            except BaseException as exc:
                tb = traceback.format_exception_only(type(exc), exc)
                msg = (tb[-1].strip() if tb else repr(exc))
                import_errors.append({"module": mod_name, "error": msg})

        # Scan sys.modules for in-project modules.
        in_project = []
        for name, mod in list(sys.modules.items()):
            if mod is None:
                continue
            if not any(
                name == pkg or name.startswith(pkg + ".")
                for pkg in top_level_packages
            ):
                continue
            in_project.append((name, mod))

        registries_inspected = 0
        registry_records = []  # list of {registry_module, registry_name, kind, entries}

        seen_registry_ids = set()

        for mod_name, mod in in_project:
            try:
                attrs = list(vars(mod).items())
            except Exception:
                continue
            for attr_name, attr_val in attrs:
                if id(attr_val) in seen_registry_ids:
                    continue
                kind = None
                entries_iter = None

                if _is_dict_like(attr_val) and _looks_like_registry_name(
                    attr_name
                ):
                    kind = "dict"
                    try:
                        entries_iter = list(attr_val.items())
                    except Exception:
                        entries_iter = None

                elif _has_register_and_get(attr_val) and not isinstance(
                    attr_val, type
                ):
                    # Duck-typed registry instance. Try to dump entries
                    # by inspecting its public attributes for dict-shaped
                    # internal state.
                    kind = "duck"
                    candidates = []
                    try:
                        for sub_name, sub_val in vars(attr_val).items():
                            if isinstance(sub_val, dict):
                                candidates.append((sub_name, sub_val))
                    except Exception:
                        pass
                    # Pick the largest dict, if any.
                    if candidates:
                        candidates.sort(
                            key=lambda kv: len(kv[1]), reverse=True
                        )
                        try:
                            entries_iter = list(candidates[0][1].items())
                        except Exception:
                            entries_iter = None

                if kind is None:
                    continue
                if entries_iter is None:
                    continue

                seen_registry_ids.add(id(attr_val))
                registries_inspected += 1
                entries_dump = []
                for k, v in entries_iter:
                    try:
                        k_repr = repr(k)
                    except Exception:
                        k_repr = "<unrepr>"
                    entries_dump.append({
                        "key": k_repr,
                        "value_module": _entry_module(v),
                        "value_qualname": _entry_qualname(v),
                        "value_is_class": isinstance(v, type),
                        "value_repr": repr(v) if not isinstance(v, type) else "",
                    })

                registry_records.append({
                    "registry_module": mod_name,
                    "registry_name": attr_name,
                    "kind": kind,
                    "entries": entries_dump,
                })

        out = {
            "modules_imported": imported,
            "import_errors": import_errors,
            "registries_inspected": registries_inspected,
            "registry_records": registry_records,
        }
        sys.stdout.write(SENTINEL_START + "\\n")
        sys.stdout.write(json.dumps(out))
        sys.stdout.write("\\n" + SENTINEL_END + "\\n")
        sys.stdout.flush()


    if __name__ == "__main__":
        try:
            main()
        except BaseException as exc:
            tb = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
            sys.stderr.write(tb)
            sys.exit(2)
    """
).strip()


# Optional preamble that applies POSIX resource limits before user code
# runs. Prepended to the probe script when applicable. Kept separate so
# the main probe body is portable and the limits live in one place.
_TIER35_RLIMIT_PREAMBLE = textwrap.dedent(
    """
    try:
        import resource
        # CPU: 30s soft / 60s hard. Memory address-space: 1 GB.
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (30, 60))
        except (ValueError, OSError):
            pass
        try:
            resource.setrlimit(
                resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024)
            )
        except (ValueError, OSError):
            pass
    except ImportError:
        # Windows: `resource` not available. Subprocess timeout still
        # applies via subprocess.run(..., timeout=...).
        pass
    """
).strip()


def _run_tier35(
    phase: PhaseInput,
    scaffold_root: Path,
    project_phases: Optional[List[PhaseInput]],
    timeout: int,
) -> List[str]:
    """Spawn a subprocess that imports the phase's PLAN.md modules and
    inspects registry-shaped objects for shadowing. Returns a list of
    `[SHADOWING:...]` / `[CHECKED:...]` / `[INCONCLUSIVE:...]` strings.
    """
    findings: List[str] = []

    # Map declared .py paths to module names. Skip non-Python paths and
    # paths with non-identifier components.
    declared_module_names: List[str] = []
    declared_module_to_path: dict = {}
    for rel in phase.paths:
        mod = _path_to_module_name(rel)
        if mod is None:
            continue
        declared_module_names.append(mod)
        declared_module_to_path[mod] = rel

    if not declared_module_names:
        # Nothing to import — nothing to smoke-test.
        findings.append(
            "[INCONCLUSIVE:no-importable-modules] phase declared no "
            ".py files with valid module names"
        )
        return findings

    # All phases' Python paths -> module-name mapping (for shadowing
    # discrimination).
    all_phase_module_to_path: dict = {}
    if project_phases is not None:
        for ph in project_phases:
            for p in ph.paths:
                m = _path_to_module_name(p)
                if m is not None:
                    all_phase_module_to_path[m] = (ph.id, p)
    else:
        for m, p in declared_module_to_path.items():
            all_phase_module_to_path[m] = (phase.id, p)

    top_level_packages = _collect_top_level_packages(phase, project_phases)

    # Build the probe script file.
    probe_body = _TIER35_RLIMIT_PREAMBLE + "\n\n" + _TIER35_PROBE_SCRIPT
    spec_payload = json.dumps(
        {
            "scaffold_root": str(scaffold_root.resolve()),
            "modules": declared_module_names,
            "top_level_packages": top_level_packages,
        }
    )

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_path = Path(tmpdir) / "tier35_probe.py"
            probe_path.write_text(probe_body, encoding="utf-8")

            # Constrained env: no inherited PYTHONPATH, no API keys.
            sandbox_env = {
                "PYTHONPATH": str(scaffold_root.resolve()),
                "PATH": os.defpath,  # minimal stdlib path
                "HOME": "/tmp",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                # Force unbuffered stdout so sentinels arrive intact even
                # if the probe is killed mid-write.
                "PYTHONUNBUFFERED": "1",
                # Prevent .pyc clutter in scaffold.
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            # Explicitly DROP HTTP_PROXY/HTTPS_PROXY/NO_PROXY/etc — by
            # building env from scratch we ensure they don't leak in.

            try:
                proc = subprocess.run(
                    [sys.executable, str(probe_path), spec_payload],
                    cwd=str(scaffold_root.resolve()),
                    env=sandbox_env,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired as exc:
                findings.append(
                    f"[INCONCLUSIVE:timeout] runtime smoke subprocess did "
                    f"not finish within {timeout}s"
                )
                return findings
            except OSError as exc:
                findings.append(
                    f"[INCONCLUSIVE:sandbox-setup-failed] could not spawn "
                    f"runtime smoke subprocess: {exc}"
                )
                return findings

            stdout = proc.stdout or ""
            stderr = proc.stderr or ""

            # Even on non-zero exit, the probe MAY have printed sentinels
            # before the crash. Try to parse first; fall through to crash
            # report if no sentinel.
            payload = _parse_tier35_output(stdout)

            if payload is None:
                if proc.returncode != 0:
                    err_excerpt = stderr.strip().splitlines()
                    last_err = err_excerpt[-1] if err_excerpt else "(no stderr)"
                    findings.append(
                        f"[INCONCLUSIVE:subprocess-crashed] exit code "
                        f"{proc.returncode}: {last_err}"
                    )
                else:
                    findings.append(
                        "[INCONCLUSIVE:malformed-output] subprocess exited "
                        "0 but produced no parseable findings sentinel"
                    )
                return findings

            # Surface per-module import errors as INCONCLUSIVE entries.
            for ie in payload.get("import_errors", []):
                findings.append(
                    f"[INCONCLUSIVE:import-error] module "
                    f"`{ie['module']}` failed to import: {ie['error']}"
                )

            # Walk registry records, classify each entry.
            for record in payload.get("registry_records", []):
                reg_mod = record["registry_module"]
                reg_name = record["registry_name"]
                kind = record["kind"]
                entries = record.get("entries", [])
                if not entries:
                    findings.append(
                        f"[CHECKED:empty-registry] registry `{reg_name}` "
                        f"in `{reg_mod}` ({kind}) has no entries"
                    )
                    continue
                for entry in entries:
                    classification = _classify_registry_entry(
                        entry,
                        declared_module_to_path,
                        all_phase_module_to_path,
                        phase_id=phase.id,
                    )
                    finding_str = _format_registry_entry_finding(
                        classification,
                        registry_module=reg_mod,
                        registry_name=reg_name,
                        registry_kind=kind,
                        entry=entry,
                        declared_module_to_path=declared_module_to_path,
                    )
                    if finding_str:
                        findings.append(finding_str)

            if not payload.get("registry_records"):
                findings.append(
                    f"[CHECKED:no-registries-detected] inspected "
                    f"{len(payload.get('modules_imported', []))} module(s); "
                    f"no registry-shaped objects matched the heuristic"
                )
    except Exception as exc:  # noqa: BLE001
        # Any unexpected error in the verifier itself is a tool-error.
        findings.append(
            f"[INCONCLUSIVE:sandbox-setup-failed] unexpected verifier "
            f"error: {type(exc).__name__}: {exc}"
        )
        return findings

    return findings


def _parse_tier35_output(stdout: str) -> Optional[dict]:
    """Find the JSON payload between the sentinels. Returns the parsed
    dict on success, None on any failure (missing sentinels, bad JSON)."""
    start = stdout.find(_TIER35_SENTINEL_START)
    if start == -1:
        return None
    end = stdout.find(_TIER35_SENTINEL_END, start)
    if end == -1:
        return None
    body = stdout[start + len(_TIER35_SENTINEL_START) : end].strip()
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def _classify_registry_entry(
    entry: dict,
    declared_module_to_path: dict,
    all_phase_module_to_path: dict,
    phase_id: int,
) -> str:
    """Return one of:
      'shadowing-other-phase'   — value's __module__ resolves to a path
                                  declared by a DIFFERENT phase. Hard
                                  shadowing (different from this phase's
                                  declared paths).
      'shadowing-undeclared'    — value's __module__ resolves to an
                                  in-project file NOT declared by any
                                  phase. Pure shadowing.
      'checked-this-phase'      — value's __module__ matches one of
                                  THIS phase's declared paths.
      'checked-third-party'     — value's __module__ does not match any
                                  in-project module (stdlib/third-party).
                                  Treated as informational.
      'checked-other-phase'     — value's __module__ matches another
                                  phase's declared paths AND THIS phase
                                  declared a module the entry could be
                                  expected to come from. We surface this
                                  as a SHADOWING when this phase declares
                                  a module that is the "natural" source
                                  for a key but the runtime resolution
                                  picked a different (cross-phase)
                                  module instead.

    The conservative rule: an entry is SHADOWING iff value.__module__
    is an in-project module AND that module is not declared by THIS
    phase. The rationale: if THIS phase declared the module, the runtime
    matched expectation; if ANOTHER phase declared it OR no phase did,
    the registration came from somewhere this phase doesn't own — the
    n=10 r4 archetype.
    """
    val_mod = entry.get("value_module", "")
    if not val_mod or val_mod == "<unknown>":
        return "checked-third-party"

    # Match against this phase's declared modules.
    if val_mod in declared_module_to_path:
        return "checked-this-phase"

    # Match against any project module declared by another phase.
    if val_mod in all_phase_module_to_path:
        other_phase_id, _path = all_phase_module_to_path[val_mod]
        if other_phase_id != phase_id:
            return "shadowing-other-phase"
        # Same phase id but different path-mapping fingerprint:
        # treat as this-phase (already covered by declared map).
        return "checked-this-phase"

    # Determine if val_mod looks in-project (top-level package matches a
    # declared phase package). If so, it's an undeclared in-project
    # module — shadowing. Otherwise it's third-party / stdlib.
    top_level = val_mod.split(".")[0]
    declared_top_levels = {
        m.split(".")[0] for m in all_phase_module_to_path.keys()
    }
    if top_level in declared_top_levels:
        return "shadowing-undeclared"
    return "checked-third-party"


def _format_registry_entry_finding(
    classification: str,
    *,
    registry_module: str,
    registry_name: str,
    registry_kind: str,
    entry: dict,
    declared_module_to_path: dict,
) -> Optional[str]:
    """Render a finding string for a single registry entry. SHADOWING
    findings include structured detail used by `_format_shadowing_
    prescription`."""
    key = entry.get("key", "<?>")
    qual = entry.get("value_qualname", "<?>")
    val_mod = entry.get("value_module", "<unknown>")

    if classification == "checked-this-phase":
        path = declared_module_to_path.get(val_mod, "<phase-declared>")
        return (
            f"[CHECKED:entry-matches-declared] registry `{registry_name}` "
            f"in `{registry_module}` ({registry_kind}): key={key} -> "
            f"`{qual}` from `{val_mod}` (declared in PLAN.md as `{path}`)"
        )
    if classification == "checked-third-party":
        return (
            f"[CHECKED:entry-third-party] registry `{registry_name}` in "
            f"`{registry_module}` ({registry_kind}): key={key} -> `{qual}` "
            f"from `{val_mod}` (stdlib/third-party — out of scope for "
            "shadowing detection)"
        )
    if classification in (
        "shadowing-other-phase",
        "shadowing-undeclared",
    ):
        # Try to figure out the EXPECTED path: any declared module in
        # THIS phase whose name matches the registry key (best-effort
        # heuristic). If none, expected_paths reads "any of this phase's
        # declared modules".
        expected_paths_list = list(declared_module_to_path.values())
        expected_paths_str = (
            ", ".join(f"`{p}`" for p in expected_paths_list)
            if expected_paths_list
            else "(no .py modules declared)"
        )
        actual_module = val_mod
        kind_tag = (
            "other-phase"
            if classification == "shadowing-other-phase"
            else "undeclared"
        )
        return (
            f"[SHADOWING:registry-entry-{kind_tag}] registry "
            f"`{registry_name}` in `{registry_module}` ({registry_kind}): "
            f"key={key} -> `{qual}` resolves at runtime to `{actual_module}` "
            f"rather than any of this phase's declared paths "
            f"({expected_paths_str})"
        )
    return None


# ---------------------------------------------------------------------------
# Tier 3.7 — acceptance-runner (first execution-based tier)
# ---------------------------------------------------------------------------
#
# Tier 3.7 is the first verification tier that runs an EXECUTION-time
# command (not just AST or sandboxed-import metadata). It exists because
# tiers 1-3 verify code shape, not behavior; r7.11 item 8 trial 3 (F-7)
# showed that wiring-clean code can still have a failing test suite, and
# the verifier had no tier that ran the suite. The fix is opt-in by
# PLAN.md declaration: when a phase block contains an `Acceptance
# Command:` field, tier 3.7 runs that command in the scaffold root with
# the scaffold's .venv site-packages on PYTHONPATH (the B1 pattern from
# hermes_multi.py:498-508 — copied here verbatim, not imported, to keep
# this module standalone).
#
# The exit-code interpretation distinguishes:
#   - acceptance-failure     (the criterion failed for real)
#   - environment-failure    (the runner could not even reach a verdict
#                             due to env issues — timeout, command not
#                             found, no tests collected)
#   - inconclusive           (subprocess crashed, internal error, unknown
#                             exit code — we don't know whether the
#                             criterion passed or failed)
#
# pytest-specific mapping is keyed off the first token of the command;
# everything else uses the general 0/non-zero mapping.

# Cap on stdout+stderr captured into the corrective_dispatch finding to
# keep the parent's context bounded. Full subprocess output is not
# preserved beyond the truncation boundary.
_TIER37_OUTPUT_CHAR_BUDGET = 1500
# Per-stream tail size when both streams have content.
_TIER37_PER_STREAM_TAIL = 700


def _classify_pytest_exit(exit_code: int) -> Tuple[str, str]:
    """Map a pytest exit code to (category, prefix).

    pytest exit codes (per its CLI documentation, copied here so the
    verifier doesn't need pytest installed):
      0 — all tests passed
      1 — at least one test failed
      2 — interrupted by user (KeyboardInterrupt)
      3 — internal error during execution
      4 — pytest CLI usage error
      5 — no tests were collected

    Categories: acceptance_passed | acceptance_failed | environment |
    inconclusive. Anything we don't recognize is conservatively
    classified as inconclusive — the parent doesn't get a misleading
    pass/fail signal for an unfamiliar exit code.
    """
    if exit_code == 0:
        return "acceptance_passed", "[ACCEPTANCE_PASSED]"
    if exit_code == 1:
        return "acceptance_failed", "[ACCEPTANCE_FAILED:1]"
    if exit_code == 2:
        return "inconclusive", "[INCONCLUSIVE:interrupted]"
    if exit_code in (3, 4):
        return "inconclusive", f"[INCONCLUSIVE:pytest-internal-error:{exit_code}]"
    if exit_code == 5:
        return "environment", "[ENVIRONMENT:no-tests-collected]"
    return "inconclusive", f"[INCONCLUSIVE:unknown-exit:{exit_code}]"


def _classify_general_exit(exit_code: int) -> Tuple[str, str]:
    """Map a non-pytest exit code to (category, prefix).

    Coarser than pytest's mapping: 0 = passed, anything else = failed.
    The exit code is preserved in the prefix so the parent can read it.
    """
    if exit_code == 0:
        return "acceptance_passed", "[ACCEPTANCE_PASSED]"
    return "acceptance_failed", f"[ACCEPTANCE_FAILED:{exit_code}]"


def _looks_like_pytest_command(argv: List[str]) -> bool:
    """Detect whether the first token of an `acceptance_command` is
    pytest. Conservative: false-classifying as pytest is worse than
    false-classifying as general (pytest's exit-5 = no-tests-collected
    becomes ENVIRONMENT, but a bash exit 5 becoming ACCEPTANCE_FAILED:5
    is fine). So we only match on:
      - argv[0] == "pytest" or argv[0].endswith("/pytest")
      - argv[0] in {python, python3, pythonX.Y, /path/to/python} and
        the next two args are "-m" "pytest"
    """
    if not argv:
        return False
    first = argv[0]
    base = os.path.basename(first)
    if base == "pytest" or base.endswith("-pytest"):
        return True
    # python / python3 / python3.11 / py / .venv/bin/python -m pytest
    if (base == "python" or base == "py" or base.startswith("python")) \
            and len(argv) >= 3 and argv[1] == "-m" and argv[2] == "pytest":
        return True
    return False


def _truncate_output_for_finding(stdout: str, stderr: str) -> str:
    """Return a bounded multi-line string fragment combining stdout and
    stderr. Each stream is tail-truncated to `_TIER37_PER_STREAM_TAIL`
    chars; the combined length is capped at `_TIER37_OUTPUT_CHAR_BUDGET`.
    The result is intended to be embedded inside an
    `[ACCEPTANCE_FAILED:N]` finding body, which the parent reads to
    diagnose what failed.
    """
    def _tail(s: str, n: int) -> str:
        if len(s) <= n:
            return s
        return "...(truncated)...\n" + s[-n:]

    out_part = _tail(stdout or "", _TIER37_PER_STREAM_TAIL).rstrip()
    err_part = _tail(stderr or "", _TIER37_PER_STREAM_TAIL).rstrip()
    blocks: List[str] = []
    if out_part:
        blocks.append("stdout (truncated):\n" + out_part)
    if err_part:
        blocks.append("stderr (truncated):\n" + err_part)
    text = "\n\n".join(blocks)
    if len(text) > _TIER37_OUTPUT_CHAR_BUDGET:
        # Hard cap as last-resort guard against pathological combined
        # output. Tail-keep so the trailing context (where pytest prints
        # the failure summary) survives.
        text = "...(truncated to " + str(_TIER37_OUTPUT_CHAR_BUDGET) + \
            " chars)...\n" + text[-_TIER37_OUTPUT_CHAR_BUDGET:]
    return text


def _augment_pythonpath_with_scaffold_venv(
    env: dict, scaffold_root: Path
) -> None:
    """B1 PYTHONPATH-injection — copied from hermes_multi.py:498-508.

    When the scaffold has a `.venv/lib/pythonX.Y/site-packages` directory,
    prepend it to PYTHONPATH so the subprocess sees the scaffold's
    third-party deps without needing to activate the venv. This is the
    same shape used by hermes_multi's LocalProcessTransport — the
    deliberate duplication keeps verify_phase deploy-as-firmware
    standalone (no cross-module import for a 10-line helper).
    """
    scaffold_venv = scaffold_root / ".venv"
    if scaffold_venv.is_dir():
        site_packages = next(
            (scaffold_venv / "lib").glob("python*/site-packages"),
            None,
        )
        if site_packages is not None:
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = (
                f"{site_packages}:{existing}" if existing else str(site_packages)
            )


def _run_acceptance_command(
    *,
    command: str,
    scaffold_root: Path,
    timeout_seconds: int,
) -> Tuple[Optional[int], str, str, str]:
    """Spawn the acceptance command. Returns
    `(exit_code_or_None, stdout, stderr, env_failure_reason)`.

    `exit_code_or_None` is None when the subprocess could not be
    launched OR timed out; in that case `env_failure_reason` is a
    non-empty string explaining what went wrong (e.g.,
    `command-not-found: pytest`, `timeout-after-120s`,
    `command-parse-error: ...`). When the subprocess ran to completion,
    `exit_code_or_None` holds the integer exit code and
    `env_failure_reason` is empty.

    Environment shape: starts from `os.environ.copy()` so existing tool
    discovery (PATH, HOME, TERM) is preserved, then augments PYTHONPATH
    with the scaffold's `.venv` site-packages (B1 pattern). This is
    DIFFERENT from tier 3.5's strict sandbox — tier 3.7 needs the user's
    env to find the right interpreter / pytest binary, and the
    acceptance command is operator-declared (not LLM-emitted), so the
    threat model is more permissive.
    """
    env = os.environ.copy()
    _augment_pythonpath_with_scaffold_venv(env, scaffold_root)

    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return None, "", "", f"command-parse-error: {exc}"
    if not argv:
        return None, "", "", "empty-command"

    try:
        proc = subprocess.run(
            argv,
            cwd=str(scaffold_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        # Either argv[0] doesn't exist on PATH OR a shebang inside it
        # points at a missing interpreter. Either way: env-side issue.
        return None, "", "", (
            f"command-not-found: {exc.filename or argv[0]}"
        )
    except subprocess.TimeoutExpired as exc:
        out = ""
        err = ""
        if exc.stdout is not None:
            out = (
                exc.stdout.decode("utf-8", "replace")
                if isinstance(exc.stdout, (bytes, bytearray))
                else str(exc.stdout)
            )
        if exc.stderr is not None:
            err = (
                exc.stderr.decode("utf-8", "replace")
                if isinstance(exc.stderr, (bytes, bytearray))
                else str(exc.stderr)
            )
        return None, out, err, f"timeout-after-{timeout_seconds}s"
    except OSError as exc:
        # Catch-all for other subprocess launch errors (PermissionError,
        # etc.). Treat as env-side; the parent can fix the file mode or
        # adjust the command.
        return None, "", "", f"subprocess-launch-failed: {exc}"

    return (
        proc.returncode,
        proc.stdout.decode("utf-8", "replace") if proc.stdout else "",
        proc.stderr.decode("utf-8", "replace") if proc.stderr else "",
        "",
    )


def _run_tier37(
    *,
    phase: PhaseInput,
    scaffold_root: Path,
    acceptance_command: str,
    timeout_seconds: int,
) -> List[str]:
    """Execute the phase's acceptance command and classify the result.

    Returns a list of prefix-tagged finding strings (see VerifyResult
    docstring for the taxonomy). Length is bounded by the size of the
    captured output (truncated for `[ACCEPTANCE_FAILED:N]` only).

    Caller is responsible for the gating check (tier 1 + tier 2 passed,
    acceptance_command non-empty); this function assumes it should run.
    """
    findings: List[str] = []

    exit_code, stdout, stderr, env_reason = _run_acceptance_command(
        command=acceptance_command,
        scaffold_root=scaffold_root,
        timeout_seconds=timeout_seconds,
    )

    # Subprocess never produced an exit code — environment issue.
    if exit_code is None:
        # Determine whether to surface stderr context. For timeout and
        # other subprocess-failure paths we have no useful exit info,
        # but stderr may have partial output (timeout case).
        bits = [f"[ENVIRONMENT:{env_reason}]"]
        if stderr.strip():
            tail = stderr.strip()
            if len(tail) > _TIER37_PER_STREAM_TAIL:
                tail = "...(truncated)...\n" + tail[-_TIER37_PER_STREAM_TAIL:]
            bits.append("stderr (truncated):\n" + tail)
        findings.append(" ".join(bits))
        return findings

    # We have an exit code. Decide on classifier.
    try:
        argv = shlex.split(acceptance_command)
    except ValueError:
        argv = []
    if _looks_like_pytest_command(argv):
        category, prefix = _classify_pytest_exit(exit_code)
    else:
        category, prefix = _classify_general_exit(exit_code)

    if category == "acceptance_passed":
        findings.append(
            f"{prefix} acceptance command exited 0: "
            f"`{acceptance_command}`"
        )
        return findings

    if category == "acceptance_failed":
        body = _truncate_output_for_finding(stdout, stderr)
        if body:
            findings.append(f"{prefix} {body}")
        else:
            findings.append(
                f"{prefix} acceptance command exited {exit_code} "
                "with no captured output"
            )
        return findings

    if category == "environment":
        # pytest exit 5 (no tests collected) is the only path here for
        # pytest commands; the general mapping never produces this
        # category. Surface a hint so the parent knows what to fix.
        bits = [prefix]
        if stderr.strip():
            tail = stderr.strip()
            if len(tail) > _TIER37_PER_STREAM_TAIL:
                tail = "...(truncated)...\n" + tail[-_TIER37_PER_STREAM_TAIL:]
            bits.append("stderr (truncated):\n" + tail)
        findings.append(" ".join(bits))
        return findings

    # category == "inconclusive"
    bits = [prefix]
    if stderr.strip():
        tail = stderr.strip()
        if len(tail) > _TIER37_PER_STREAM_TAIL:
            tail = "...(truncated)...\n" + tail[-_TIER37_PER_STREAM_TAIL:]
        bits.append("stderr (truncated):\n" + tail)
    findings.append(" ".join(bits))
    return findings


__all__ = [
    "Tier",
    "PhaseInput",
    "VerifyResult",
    "verify_phase",
]
