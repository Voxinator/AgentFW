"""Content-verified scoring of an r7.10/r7.11 multi-session implementation run.

This module mirrors the four r7.10-derived content-verification criteria
distilled in `NOTE-r7.10-budget-n10-r4-rescore.md` (and informed by the
n=10 r4 importlib-shadowing pattern + the n=5 r5 unwired-API+test-stub
pattern). It produces a structured `VerifyReport` that:

  - is importable and used by item 8 (single trial) + item 9 (n=5
    confirmation) as the methodology for evaluating whether an r7.11
    multi-session run produced a real, integrated implementation
    versus fabrication or partial/incoherent work, and
  - is designed so a later tier 4 (r7.12 semantic verifier) LLM judge
    can consume the structured findings + a brief summary text.

Tier-4 hook:
    `VerifyReport.as_judge_brief()` produces a self-contained text
    summary (path-by-path findings + scaffold context) suitable for
    handing to a fresh LLM judge sub-agent. The judge here is NOT
    invoked; only the brief format is produced. tier 4 is responsible
    for spinning up the judge.

Stdlib only (ast, dataclasses, enum, json, pathlib, argparse, typing).

Five checks (composed in `verify_scaffold`):
    C1. Real serializer implementations (no missing/stub/fake bodies).
    C2. Wired API endpoints (import + use serializer; no inlining).
    C3. Test bodies are non-stub (no `raise NotImplementedError`).
    C4. No top-level symbol shadowing (n=10 r4 importlib pattern).
    C5. PLAN.md does not declare files that don't exist (n=5 r4
        fabrication pattern).

Severity model:
    HIGH    — disqualifies strict; large counts disqualify charitable
    MEDIUM  — disqualifies strict (above 1); charitable tolerates a few
    LOW     — informational only

Strict verdict:
    - 0 high-severity findings AND <= 1 medium-severity findings.
Charitable verdict:
    - <= 2 high-severity findings AND <= 4 medium-severity findings.
    Rationale: r7.10 r4 had ~3 high (fake PDF + duplicate symbol +
    registry shadow) and was scored "charitable yes" in the rescore;
    we want charitable to capture "real but flawed" implementations
    (r4, r5) without admitting "extensively broken" ones.

CLI:
    python content_verify.py <scaffold_root> [--plan-md PATH] [--json]
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional, Union

# ---------------------------------------------------------------------------
# Enums and dataclasses
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(str, Enum):
    SERIALIZER_FAKE = "serializer-fake"
    SERIALIZER_MISSING = "serializer-missing"
    SERIALIZER_STUB = "serializer-stub"
    UNWIRED_API = "unwired-api"
    UNWIRED_INLINE = "unwired-inline"
    TEST_STUB = "test-stub"
    TEST_MISSING = "test-missing"
    DUPLICATE_SYMBOL = "duplicate-symbol"
    REGISTRY_SHADOWING = "registry-shadowing"
    FABRICATION = "fabrication"


@dataclass
class Finding:
    """One content-verification finding.

    `category` and `severity` are typed as the enum values for normal
    construction, but accept str on input for forward-compatibility
    (a future tier-4 judge could extend the categories list without
    needing the upstream enum to be patched in lock-step).
    """

    category: Union[Category, str]
    severity: Union[Severity, str]
    path: Optional[str]
    line: Optional[int]
    detail: str
    evidence: dict = field(default_factory=dict)

    def category_value(self) -> str:
        if isinstance(self.category, Category):
            return self.category.value
        return str(self.category)

    def severity_value(self) -> str:
        if isinstance(self.severity, Severity):
            return self.severity.value
        return str(self.severity)


@dataclass
class VerifyReport:
    strict_passed: bool
    charitable_passed: bool
    findings: list[Finding]
    files_inspected: list[str]
    summary: str
    plan_md_phases: list[dict]
    scaffold_root: str

    def as_judge_brief(self) -> str:
        """Self-contained text brief for a fresh LLM judge.

        Format:
            <verdict line>
            <scaffold context block>
            <findings block, one paragraph per finding>

        Length-bounded; no embedded source code. The judge can read
        files itself if it wants finer detail.
        """
        lines: list[str] = []
        lines.append(
            f"VERDICT: strict={self.strict_passed} "
            f"charitable={self.charitable_passed}"
        )
        lines.append(f"SUMMARY: {self.summary}")
        lines.append("")
        lines.append(f"SCAFFOLD: {self.scaffold_root}")
        lines.append(
            f"  files inspected: {len(self.files_inspected)}"
        )
        if self.plan_md_phases:
            lines.append(
                f"  PLAN.md phases: {len(self.plan_md_phases)} "
                f"(ids: "
                f"{[p.get('id') for p in self.plan_md_phases]})"
            )
        else:
            lines.append("  PLAN.md phases: none parsed")
        lines.append("")
        if not self.findings:
            lines.append("FINDINGS: none.")
            return "\n".join(lines)
        lines.append(f"FINDINGS ({len(self.findings)}):")
        for i, f in enumerate(self.findings, 1):
            where = f.path or "<project>"
            if f.line is not None:
                where = f"{where}:{f.line}"
            lines.append(
                f"  {i}. [{f.severity_value()}/"
                f"{f.category_value()}] {where}"
            )
            lines.append(f"     {f.detail}")
            if f.evidence:
                # Compact, deterministic evidence dump
                ev_keys = sorted(f.evidence.keys())
                ev_str = ", ".join(
                    f"{k}={f.evidence[k]!r}" for k in ev_keys
                )
                if len(ev_str) > 240:
                    ev_str = ev_str[:237] + "..."
                lines.append(f"     evidence: {ev_str}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_SKIP_DIR_NAMES = {
    "__pycache__",
    ".venv",
    "venv",
    ".git",
    ".session-archive",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    "tmp-archive",
    "archive",
}

_TOLERATED_DUNDER_NAMES = {
    "__version__",
    "__author__",
    "__all__",
    "__doc__",
    "__name__",
    "__email__",
    "__license__",
}

_PDF_LIBS = ("reportlab", "fpdf", "weasyprint", "pypdf", "pdfkit", "borb")
_CSV_LIBS = ("csv",)
_JSON_LIBS = ("json", "orjson", "ujson", "simplejson")


def _resolve_plan_path(scaffold_root: Path, declared_path: str) -> Path:
    """Resolve a PLAN.md-declared path against scaffold_root.

    If declared_path is absolute (e.g., "/tmp/scaffold/src/x.py"), use
    it as-is — PLAN.md authored with absolute paths is valid and must
    not be joined with scaffold_root (which would yield a path that
    cannot exist and produce a spurious FABRICATION finding; r7.11
    item-8 trial-2 F-4).

    Otherwise treat declared_path as relative to scaffold_root, after
    a defensive `./` strip to tolerate `./src/foo.py`-style entries.
    """
    p = Path(declared_path)
    if p.is_absolute():
        return p
    return scaffold_root / declared_path.lstrip("./")


def _walk_python_files(
    root: Path, *, include_tests: bool = True
) -> list[Path]:
    """Walk `root` and yield .py files, skipping caches/archives."""
    out: list[Path] = []
    for p in sorted(root.rglob("*.py")):
        # Skip if any path component is in skip set
        parts = set(p.relative_to(root).parts)
        if parts & _SKIP_DIR_NAMES:
            continue
        if not include_tests:
            rel = p.relative_to(root)
            if _is_test_path(rel):
                continue
        out.append(p)
    return out


def _is_test_path(rel: Path) -> bool:
    """Heuristic: test files are under tests/ OR match test_*.py / *_test.py."""
    parts = rel.parts
    if "tests" in parts:
        return True
    name = rel.name
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    return False


def _is_serializer_path(rel: Path) -> bool:
    name = rel.name.lower()
    if "serializer" in name or "serialize" in name:
        return True
    # Also: known r7.10 export-format module names
    parts = [p.lower() for p in rel.parts]
    if "export" in parts or "exports" in parts or "formats" in parts:
        # only stems csv/json/pdf/yaml/xml within an export dir
        stem = rel.stem.lower()
        if stem in {"csv", "json", "pdf", "yaml", "xml", "html", "txt"}:
            return True
    return False


def _is_api_path(rel: Path) -> bool:
    parts = [p.lower() for p in rel.parts]
    return ("api" in parts) or ("endpoints" in parts) or (
        "routes" in parts
    )


def _classify_pdf(name: str) -> bool:
    return "pdf" in name.lower()


def _classify_csv(name: str) -> bool:
    return "csv" in name.lower()


def _classify_json(name: str) -> bool:
    n = name.lower()
    # Avoid matching jsonschema etc.
    return n == "json.py" or n.endswith("/json.py") or "_json" in n or (
        "json" in n and "schema" not in n
    )


def _read_text(p: Path) -> Optional[str]:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _parse_module(p: Path) -> tuple[Optional[ast.Module], Optional[str]]:
    text = _read_text(p)
    if text is None:
        return None, None
    try:
        return ast.parse(text), text
    except SyntaxError:
        return None, text


def _is_docstring_only(mod: ast.Module) -> bool:
    """Returns True when the module body is empty OR consists only of
    a leading docstring (Expr/Constant str) plus optional `pass`/empty
    Assign nodes — i.e., no real definitions."""
    nontrivial = []
    for node in mod.body:
        if isinstance(node, ast.Expr) and isinstance(
            node.value, ast.Constant
        ) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.Pass):
            continue
        nontrivial.append(node)
    return len(nontrivial) == 0


def _module_has_def(mod: ast.Module) -> bool:
    for node in mod.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            return True
    return False


def _module_imports(mod: ast.Module) -> set[str]:
    """Return a set of imported root module names (e.g., `reportlab`,
    `csv`, `src.export.csv`)."""
    out: set[str] = set()
    for node in ast.walk(mod):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
                # Also add root component
                out.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.add(node.module)
                out.add(node.module.split(".", 1)[0])
    return out


def _module_imported_names(mod: ast.Module) -> set[str]:
    """Names bound by import statements (used to check usage in bodies).
    For `from x import a, b as c`, yields {"a", "c"}.
    For `import x`, yields {"x"}.
    For `import x.y`, yields {"x"} (the binding name).
    For `import x as y`, yields {"y"}.
    """
    out: set[str] = set()
    for node in ast.walk(mod):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    out.add(alias.asname)
                else:
                    out.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                out.add(alias.asname or alias.name)
    return out


def _names_referenced_in(node: ast.AST) -> set[str]:
    out: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            # Walk chain to root Name
            cur: Any = n
            while isinstance(cur, ast.Attribute):
                cur = cur.value
            if isinstance(cur, ast.Name):
                out.add(cur.id)
    return out


# ---------------------------------------------------------------------------
# C1: Serializer checks
# ---------------------------------------------------------------------------


def _check_serializers(
    scaffold_root: Path,
    plan_phases: list[dict],
) -> list[Finding]:
    findings: list[Finding] = []

    # Collect declared paths from PLAN.md phases that look like
    # serializer/export/format work
    declared_paths: list[str] = []
    for phase in plan_phases:
        title = (phase.get("title") or "").lower()
        if any(kw in title for kw in (
            "serial", "export", "format", "pdf", "csv", "json"
        )):
            declared_paths.extend(phase.get("paths") or [])

    # Heuristically detected serializer files on disk
    detected: list[Path] = []
    for p in _walk_python_files(scaffold_root, include_tests=False):
        rel = p.relative_to(scaffold_root)
        if _is_serializer_path(rel):
            detected.append(p)

    # Union declared + detected paths
    candidates: dict[str, Path] = {}
    for d in detected:
        rel = d.relative_to(scaffold_root)
        candidates[str(rel)] = d
    for dp in declared_paths:
        cand = _resolve_plan_path(scaffold_root, dp)
        # Compute a "rel-style" string for the candidates dict key and
        # for the serializer-shape heuristics. For absolute-path PLAN.md
        # entries we use the path as-is (no scaffold_root anchor); for
        # relative entries we use the original lstrip("./") form.
        if Path(dp).is_absolute():
            norm = str(cand)
        else:
            norm = dp.lstrip("./")
        # Only consider .py
        if cand.suffix != ".py":
            continue
        if "test" in cand.parts[-1].lower():
            continue
        # Skip non-serializer-shaped declared paths (e.g., api files)
        rel_for_check = Path(norm)
        if not (
            _is_serializer_path(rel_for_check)
            or _is_api_path(rel_for_check) is False
            and rel_for_check.stem.lower() in
                {"csv", "json", "pdf", "yaml", "xml"}
        ):
            # Only include if it looks serializer-shaped
            if not _is_serializer_path(rel_for_check):
                continue
        candidates[str(rel_for_check)] = cand

    for rel_str, p in sorted(candidates.items()):
        if not p.exists():
            findings.append(Finding(
                category=Category.SERIALIZER_MISSING,
                severity=Severity.HIGH,
                path=rel_str,
                line=None,
                detail=(
                    "declared serializer path is absent on disk "
                    "(PLAN.md or naming heuristic referenced it but "
                    "no file exists)"
                ),
                evidence={"declared_paths": declared_paths},
            ))
            continue

        text = _read_text(p)
        if text is None:
            findings.append(Finding(
                category=Category.SERIALIZER_MISSING,
                severity=Severity.HIGH,
                path=rel_str,
                line=None,
                detail="file present but unreadable",
                evidence={},
            ))
            continue

        try:
            mod = ast.parse(text)
        except SyntaxError as exc:
            findings.append(Finding(
                category=Category.SERIALIZER_STUB,
                severity=Severity.HIGH,
                path=rel_str,
                line=getattr(exc, "lineno", None),
                detail=f"file does not parse: {exc.msg}",
                evidence={},
            ))
            continue

        if not _module_has_def(mod):
            # Check size only when there are no definitions — a
            # small file with a real def (e.g., a fake-bytes
            # one-liner) is FAKE not STUB.
            nonblank = [ln for ln in text.splitlines() if ln.strip()]
            findings.append(Finding(
                category=Category.SERIALIZER_STUB,
                severity=Severity.HIGH,
                path=rel_str,
                line=None,
                detail=(
                    "module has no function or class definitions; "
                    "docstring-only or empty "
                    f"({len(text)} chars, {len(nonblank)} non-blank "
                    "lines)"
                ),
                evidence={
                    "size_chars": len(text),
                    "nonblank_lines": len(nonblank),
                },
            ))
            continue

        # Fake-implementation detection
        is_pdf = _classify_pdf(rel_str)
        is_csv_file = _classify_csv(rel_str) and not is_pdf
        is_json_file = (
            "json" in rel_str.lower() and not is_pdf and not is_csv_file
        )
        imports = _module_imports(mod)

        if is_pdf:
            findings.extend(_pdf_fake_findings(
                rel_str=rel_str, mod=mod, imports=imports
            ))
        elif is_csv_file:
            findings.extend(_simple_fake_findings(
                rel_str=rel_str,
                mod=mod,
                imports=imports,
                expected_libs=_CSV_LIBS,
                kind="csv",
            ))
        elif is_json_file:
            findings.extend(_simple_fake_findings(
                rel_str=rel_str,
                mod=mod,
                imports=imports,
                expected_libs=_JSON_LIBS,
                kind="json",
            ))

    return findings


def _pdf_fake_findings(
    *, rel_str: str, mod: ast.Module, imports: set[str]
) -> list[Finding]:
    """Detect: (1) function returns hardcoded short bytes literal AND
    no PDF lib imported (n=10 r4 pattern); (2) function returns a
    string containing "%PDF" instead of bytes (n=5 r5 pattern)."""
    findings: list[Finding] = []
    has_pdf_lib = any(
        any(lib in imp for lib in _PDF_LIBS) for imp in imports
    )

    for fn in ast.walk(mod):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # Walk return statements in the function body only
        for node in ast.walk(fn):
            if not isinstance(node, ast.Return) or node.value is None:
                continue
            v = node.value
            # Pattern (1): short bytes literal
            if isinstance(v, ast.Constant) and isinstance(v.value, bytes):
                if len(v.value) < 100 and not has_pdf_lib:
                    findings.append(Finding(
                        category=Category.SERIALIZER_FAKE,
                        severity=Severity.HIGH,
                        path=rel_str,
                        line=node.lineno,
                        detail=(
                            f"function {fn.name!r} returns a hardcoded "
                            f"bytes literal ({len(v.value)} bytes) and "
                            "no PDF library is imported; this is the "
                            "n=10 r4 fake-PDF pattern"
                        ),
                        evidence={
                            "function": fn.name,
                            "bytes_len": len(v.value),
                            "imports": sorted(imports),
                        },
                    ))
            # Pattern (2): str containing "%PDF" (n=5 r5)
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                if "%PDF" in v.value:
                    findings.append(Finding(
                        category=Category.SERIALIZER_FAKE,
                        severity=Severity.HIGH,
                        path=rel_str,
                        line=node.lineno,
                        detail=(
                            f"function {fn.name!r} returns a *string* "
                            "containing '%PDF' (not bytes); n=5 r5 "
                            "fake-PDF text-string pattern"
                        ),
                        evidence={"function": fn.name},
                    ))
            # Pattern (2b): JoinedStr / f-string containing "%PDF"
            if isinstance(v, ast.JoinedStr):
                for sub in v.values:
                    if (
                        isinstance(sub, ast.Constant)
                        and isinstance(sub.value, str)
                        and "%PDF" in sub.value
                    ):
                        findings.append(Finding(
                            category=Category.SERIALIZER_FAKE,
                            severity=Severity.HIGH,
                            path=rel_str,
                            line=node.lineno,
                            detail=(
                                f"function {fn.name!r} returns an "
                                "f-string containing '%PDF' (not "
                                "bytes); n=5 r5 fake-PDF pattern"
                            ),
                            evidence={"function": fn.name},
                        ))
                        break
    return findings


def _simple_fake_findings(
    *,
    rel_str: str,
    mod: ast.Module,
    imports: set[str],
    expected_libs: tuple,
    kind: str,
) -> list[Finding]:
    """For CSV/JSON: flag MEDIUM-severity SERIALIZER_FAKE only if a
    function body is empty / `pass` / `return None` / `return ""` AND
    none of the expected libs is imported. CSV/JSON are simple enough
    to implement correctly without their stdlib helpers, so we are
    cautious here."""
    findings: list[Finding] = []
    has_lib = any(
        any(lib == imp or imp.startswith(lib + ".") for lib in
            expected_libs)
        for imp in imports
    )

    for fn in ast.walk(mod):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = fn.body
        # Strip leading docstring
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]

        if not body:
            continue

        # Trivial body shapes
        trivial = False
        if len(body) == 1:
            stmt = body[0]
            if isinstance(stmt, ast.Pass):
                trivial = True
            elif isinstance(stmt, ast.Return):
                if stmt.value is None:
                    trivial = True
                elif (
                    isinstance(stmt.value, ast.Constant)
                    and stmt.value.value in (None, "", b"", 0)
                ):
                    trivial = True

        if trivial and not has_lib:
            findings.append(Finding(
                category=Category.SERIALIZER_FAKE,
                severity=Severity.MEDIUM,
                path=rel_str,
                line=fn.lineno,
                detail=(
                    f"{kind} function {fn.name!r} has a trivial body "
                    f"(empty/pass/return None/empty) and no "
                    f"{kind} library is imported"
                ),
                evidence={"function": fn.name, "kind": kind},
            ))
    return findings


# ---------------------------------------------------------------------------
# C2: Wired API checks
# ---------------------------------------------------------------------------


def _check_wired_api(
    scaffold_root: Path,
    plan_phases: list[dict],
) -> list[Finding]:
    findings: list[Finding] = []

    # Find serializer modules (importable names) on disk
    serializer_modules: set[str] = set()
    serializer_top_paths: set[str] = set()
    for p in _walk_python_files(scaffold_root, include_tests=False):
        rel = p.relative_to(scaffold_root)
        if _is_serializer_path(rel):
            # Compute dotted module name (e.g., src.export.csv)
            parts = list(rel.parts)
            if parts[-1] == "__init__.py":
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1][:-3]  # strip .py
            dotted = ".".join(parts)
            if dotted:
                serializer_modules.add(dotted)
                serializer_top_paths.add(parts[-1])

    # Find API files
    api_files: list[Path] = []
    for p in _walk_python_files(scaffold_root, include_tests=False):
        rel = p.relative_to(scaffold_root)
        if _is_api_path(rel):
            api_files.append(p)

    # Add API files declared in PLAN.md "api"/"endpoint" phases
    for phase in plan_phases:
        title = (phase.get("title") or "").lower()
        if any(kw in title for kw in ("api", "endpoint", "route")):
            for dp in phase.get("paths") or []:
                cand = _resolve_plan_path(scaffold_root, dp)
                if cand.suffix == ".py" and cand not in api_files:
                    if cand.exists():
                        api_files.append(cand)

    if not serializer_modules:
        # Nothing to wire to; skip C2 silently.
        return findings

    for p in sorted(set(api_files)):
        # API file may be outside scaffold_root if PLAN.md declared an
        # absolute path; fall back to the absolute path for display.
        try:
            rel_str = str(p.relative_to(scaffold_root))
        except ValueError:
            rel_str = str(p)
        text = _read_text(p)
        if text is None:
            continue
        try:
            mod = ast.parse(text)
        except SyntaxError:
            continue

        if not _module_has_def(mod):
            # Empty/docstring-only API file isn't an UNWIRED finding —
            # it's a different problem (essentially a stub) that the
            # serializer-check would not catch but that is captured
            # implicitly by the absence of any endpoints.
            continue

        imports = _module_imports(mod)
        imported_names = _module_imported_names(mod)

        # Does it import any serializer module?
        imports_serializer = False
        matched_serializer_modules: list[str] = []
        for sm in serializer_modules:
            if sm in imports:
                imports_serializer = True
                matched_serializer_modules.append(sm)
                continue
            # Also accept partial matches (the scaffold might be
            # rooted slightly differently from import paths)
            for imp in imports:
                if imp.endswith("." + sm) or sm.endswith("." + imp):
                    imports_serializer = True
                    matched_serializer_modules.append(sm)
                    break

        # Detect inline string-construction patterns (n=5 r5):
        # Heuristic — any string literal in the body that looks like
        # a CSV header (contains commas + a newline) OR contains "%PDF".
        inline_csv = False
        inline_pdf = False
        inline_line: Optional[int] = None
        for node in ast.walk(mod):
            if isinstance(node, ast.Constant) and isinstance(
                node.value, str
            ):
                s = node.value
                # Skip docstrings (top-level / function-level)
                if not s:
                    continue
                if "%PDF" in s:
                    inline_pdf = True
                    inline_line = inline_line or getattr(
                        node, "lineno", None
                    )
                if "," in s and "\n" in s and len(s) < 500:
                    # Heuristic CSV header literal; require at least
                    # 2 commas to reduce false positives
                    if s.count(",") >= 2:
                        # And not a docstring (rough check: contains
                        # no spaces around the commas would suggest CSV)
                        inline_csv = True
                        inline_line = inline_line or getattr(
                            node, "lineno", None
                        )

        if not imports_serializer:
            # Per UNWIRED-consolidation rule (mirrors REGISTRY_SHADOWING):
            # an API file with both no-serializer-import AND inlined
            # serialization represents ONE architectural defect — endpoints
            # bypass the serializer layer. Emit a single consolidated finding
            # rather than UNWIRED_API + UNWIRED_INLINE doubled-up.
            if inline_csv or inline_pdf:
                findings.append(Finding(
                    category=Category.UNWIRED_INLINE,
                    severity=Severity.HIGH,
                    path=rel_str,
                    line=inline_line,
                    detail=(
                        "API file does not import any serializer module "
                        f"(serializer modules in project: "
                        f"{sorted(serializer_modules)}) AND inlines "
                        f"serialization (csv-shape={inline_csv}, "
                        f"pdf-shape={inline_pdf}); n=5 r5 "
                        "unwired-inline pattern (consolidated single "
                        "architectural defect)"
                    ),
                    evidence={
                        "api_imports": sorted(imports),
                        "serializer_modules": sorted(serializer_modules),
                        "csv_shape": inline_csv,
                        "pdf_shape": inline_pdf,
                        "consolidated_from": [
                            "unwired-api", "unwired-inline"
                        ],
                    },
                ))
            else:
                findings.append(Finding(
                    category=Category.UNWIRED_API,
                    severity=Severity.HIGH,
                    path=rel_str,
                    line=None,
                    detail=(
                        "API file does not import any serializer module "
                        f"(serializer modules in project: "
                        f"{sorted(serializer_modules)}); "
                        "endpoints likely inline serialization or return "
                        "raw data"
                    ),
                    evidence={
                        "api_imports": sorted(imports),
                        "serializer_modules": sorted(serializer_modules),
                    },
                ))
            continue

        # Imports a serializer — but does it actually USE it?
        # Find function bodies (incl. async) and check whether any of
        # the imported names appear there.
        used = False
        for fn in ast.walk(mod):
            if not isinstance(
                fn, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                continue
            refs = _names_referenced_in(fn)
            if refs & imported_names:
                # Check whether the referenced names came from a
                # serializer import. We don't have a perfect mapping,
                # so we accept any imported name from a serializer
                # ImportFrom.
                if _refs_include_serializer_import(
                    mod, fn, serializer_modules
                ):
                    used = True
                    break

        if not used:
            # Same consolidation: dead serializer import + inlined
            # serialization on the same file = one architectural defect.
            if inline_csv or inline_pdf:
                findings.append(Finding(
                    category=Category.UNWIRED_INLINE,
                    severity=Severity.HIGH,
                    path=rel_str,
                    line=inline_line,
                    detail=(
                        "API file imports a serializer module but never "
                        "uses any of its symbols inside endpoint function "
                        "bodies AND inlines serialization "
                        f"(csv-shape={inline_csv}, pdf-shape={inline_pdf}); "
                        "consolidated single architectural defect"
                    ),
                    evidence={
                        "matched_serializer_modules":
                            sorted(matched_serializer_modules),
                        "csv_shape": inline_csv,
                        "pdf_shape": inline_pdf,
                        "consolidated_from": [
                            "unwired-dead-import", "unwired-inline"
                        ],
                    },
                ))
            else:
                findings.append(Finding(
                    category=Category.UNWIRED_INLINE,
                    severity=Severity.HIGH,
                    path=rel_str,
                    line=None,
                    detail=(
                        "API file imports a serializer module but never "
                        "uses any of its symbols inside endpoint function "
                        "bodies"
                    ),
                    evidence={
                        "matched_serializer_modules":
                            sorted(matched_serializer_modules),
                    },
                ))

    return findings


def _refs_include_serializer_import(
    mod: ast.Module,
    fn: ast.AST,
    serializer_modules: set[str],
) -> bool:
    """Return True iff any name referenced inside `fn` was bound by
    an import whose source module matches a serializer module."""
    # Build map: bound_name -> source_module
    bound: dict[str, str] = {}
    for node in ast.walk(mod):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                key = alias.asname or alias.name
                bound[key] = node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                key = alias.asname or alias.name.split(".", 1)[0]
                bound[key] = alias.name

    refs = _names_referenced_in(fn)
    for name in refs:
        src = bound.get(name)
        if not src:
            continue
        # Match against serializer modules (exact or suffix)
        for sm in serializer_modules:
            if src == sm or src.endswith("." + sm) or sm.endswith(
                "." + src
            ):
                return True
            # Also: src might be the parent (e.g., "src.export") and
            # name is "csv" — match if "src.export.csv" in serializer_modules
            if (src + "." + name) in serializer_modules:
                return True
    return False


# ---------------------------------------------------------------------------
# C3: Test stub checks
# ---------------------------------------------------------------------------


def _check_test_stubs(scaffold_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    test_files: list[Path] = []
    for p in _walk_python_files(scaffold_root, include_tests=True):
        rel = p.relative_to(scaffold_root)
        if _is_test_path(rel):
            test_files.append(p)

    if not test_files:
        return findings

    file_results: list[tuple[Path, int, int, list[int]]] = []
    # (path, total_test_fns, stub_test_fns, stub_lines)

    for p in test_files:
        text = _read_text(p)
        if text is None:
            continue
        try:
            mod = ast.parse(text)
        except SyntaxError:
            continue

        total = 0
        stubs = 0
        stub_lines: list[int] = []
        for node in ast.walk(mod):
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and node.name.startswith("test_"):
                total += 1
                if _function_raises_notimpl(node):
                    stubs += 1
                    stub_lines.append(node.lineno)

        file_results.append((p, total, stubs, stub_lines))

    if not file_results:
        return findings

    # Per-file findings, then consolidation:
    # - Each file with stubs gets a per-file finding (severity per file).
    # - All-stub files are HIGH; mixed files are MEDIUM.
    # - When MULTIPLE files in the same project all have stubs, this
    #   represents one architectural defect ("parent left test stubs
    #   uncorrected") — consolidate into ONE HIGH finding listing all
    #   affected files. Same precedent as REGISTRY_SHADOWING (multiple
    #   shadow entries → one defect) and UNWIRED consolidation (multiple
    #   per-file findings on the same defect → one).
    per_file: list[Finding] = []
    for p, total, stubs, stub_lines in file_results:
        if stubs == 0:
            continue
        rel_str = str(p.relative_to(scaffold_root))
        all_stub = total > 0 and stubs == total
        if all_stub:
            sev = Severity.HIGH
            detail = (
                f"all {total} test function(s) raise "
                "NotImplementedError; file is a pure stub"
            )
        else:
            sev = Severity.MEDIUM
            detail = (
                f"{stubs} of {total} test function(s) raise "
                "NotImplementedError; file is partially stubbed"
            )
        per_file.append(Finding(
            category=Category.TEST_STUB,
            severity=sev,
            path=rel_str,
            line=stub_lines[0] if stub_lines else None,
            detail=detail,
            evidence={
                "total_tests": total,
                "stub_tests": stubs,
                "stub_lines": stub_lines,
            },
        ))

    # Consolidate: if 2+ HIGH-severity TEST_STUB findings, collapse to one.
    # MEDIUM findings stay per-file (they signal partial work; less
    # architecturally uniform). The consolidation matches the rescore
    # methodology where "2 of 4 test files stubbed" was one defect, not two.
    high_stubs = [f for f in per_file if f.severity == Severity.HIGH]
    medium_stubs = [f for f in per_file if f.severity == Severity.MEDIUM]
    if len(high_stubs) >= 2:
        files_listing = sorted(f.path for f in high_stubs if f.path)
        consolidated = Finding(
            category=Category.TEST_STUB,
            severity=Severity.HIGH,
            path=None,
            line=None,
            detail=(
                f"{len(high_stubs)} test files contain only "
                "NotImplementedError stub bodies; parent left test "
                "stubs uncorrected (consolidated single architectural "
                f"defect): {', '.join(files_listing)}"
            ),
            evidence={
                "stub_files": files_listing,
                "stub_count": len(high_stubs),
                "consolidated_from": ["test-stub-per-file"],
            },
        )
        findings.append(consolidated)
        findings.extend(medium_stubs)
    else:
        findings.extend(per_file)

    return findings


def _function_raises_notimpl(fn: ast.AST) -> bool:
    """True if the function body contains a top-level (or
    short-circuit) `raise NotImplementedError` and nothing else of
    substance."""
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    body = list(fn.body)
    # Strip leading docstring
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    # Look for any Raise of NotImplementedError. If body has any
    # other statement that's not a Pass / docstring, it's still a
    # stub if the only "real" statement is the raise.
    has_raise_notimpl = False
    has_other_substantive = False
    for stmt in body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Raise) and stmt.exc is not None:
            exc = stmt.exc
            name = None
            if isinstance(exc, ast.Name):
                name = exc.id
            elif isinstance(exc, ast.Call) and isinstance(
                exc.func, ast.Name
            ):
                name = exc.func.id
            if name == "NotImplementedError":
                has_raise_notimpl = True
                continue
        has_other_substantive = True
    return has_raise_notimpl and not has_other_substantive


# ---------------------------------------------------------------------------
# C4: Duplicate-symbol check (and registry-shadowing upgrade)
# ---------------------------------------------------------------------------


def _check_duplicate_symbols(
    scaffold_root: Path,
) -> list[Finding]:
    findings: list[Finding] = []

    # name -> list of (rel_str, line, kind)
    sym_map: dict[str, list[tuple[str, int, str]]] = {}
    # Cache modules by rel path for the registry-shadowing pattern
    module_cache: dict[str, ast.Module] = {}

    for p in _walk_python_files(scaffold_root, include_tests=True):
        rel = p.relative_to(scaffold_root)
        rel_str = str(rel)
        text = _read_text(p)
        if text is None:
            continue
        try:
            mod = ast.parse(text)
        except SyntaxError:
            continue
        module_cache[rel_str] = mod

        for node in mod.body:
            names: list[tuple[str, int, str]] = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.append((node.name, node.lineno, "function"))
            elif isinstance(node, ast.ClassDef):
                names.append((node.name, node.lineno, "class"))
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                # Top-level constant assignments
                targets: list[ast.AST] = []
                if isinstance(node, ast.Assign):
                    targets = list(node.targets)
                elif isinstance(node, ast.AnnAssign):
                    targets = [node.target]
                for t in targets:
                    if isinstance(t, ast.Name):
                        names.append((t.id, node.lineno, "assign"))

            for name, line, kind in names:
                sym_map.setdefault(name, []).append((rel_str, line, kind))

    # Build the test-files set
    test_paths = {
        str(p.relative_to(scaffold_root))
        for p in _walk_python_files(scaffold_root, include_tests=True)
        if _is_test_path(p.relative_to(scaffold_root))
    }

    # Detect importlib auto-load shadowing pattern, once
    has_importlib_autoload = _detect_importlib_autoload(module_cache)

    # Two passes:
    #   1. Collect all duplicate symbols (skipping tolerated/test-only).
    #   2. If importlib auto-load is detected and ANY of the dups
    #      involves a formats_init-shaped file, emit ONE consolidated
    #      REGISTRY_SHADOWING finding (the auto-load is one
    #      architectural defect; multiple shadowed classes are
    #      symptoms of that single defect, not independent issues).
    #      Remaining non-shadowing dups are emitted individually as
    #      DUPLICATE_SYMBOL findings.
    candidates: list[tuple[str, list[tuple[str, int, str]]]] = []
    for name, locs in sorted(sym_map.items()):
        if len(locs) < 2:
            continue
        if name in _TOLERATED_DUNDER_NAMES:
            continue
        if all(loc[0] in test_paths for loc in locs):
            continue
        candidates.append((name, locs))

    shadow_group: list[tuple[str, list[tuple[str, int, str]]]] = []
    plain_dups: list[tuple[str, list[tuple[str, int, str]]]] = []
    for name, locs in candidates:
        is_shadow = False
        if has_importlib_autoload:
            file_names = [Path(loc[0]).name for loc in locs]
            if any("formats_init" in fn for fn in file_names) and len(
                set(file_names)
            ) >= 2:
                is_shadow = True
        if is_shadow:
            shadow_group.append((name, locs))
        else:
            plain_dups.append((name, locs))

    if shadow_group:
        all_names = [n for n, _ in shadow_group]
        all_files: set[str] = set()
        for _, locs in shadow_group:
            for loc in locs:
                all_files.add(loc[0])
        findings.append(Finding(
            category=Category.REGISTRY_SHADOWING,
            severity=Severity.HIGH,
            path=None,
            line=None,
            detail=(
                f"importlib auto-load shadows {len(all_names)} "
                f"symbol(s) {all_names!r} via a formats_init-style "
                "module; this is the n=10 r4 silent-shadowing "
                "pattern (real impl in one file, fake impl in "
                "formats_init.py registered via auto-load). "
                "Counted as a single architectural finding."
            ),
            evidence={
                "names": all_names,
                "files": sorted(all_files),
                "importlib_autoload": True,
            },
        ))

    for name, locs in plain_dups:
        findings.append(Finding(
            category=Category.DUPLICATE_SYMBOL,
            severity=Severity.HIGH,
            path=None,
            line=None,
            detail=(
                f"symbol {name!r} is defined in 2+ non-test files "
                "(possible silent shadowing or copy-paste)"
            ),
            evidence={
                "name": name,
                "files": [loc[0] for loc in locs],
                "lines": [loc[1] for loc in locs],
            },
        ))

    return findings


def _detect_importlib_autoload(
    module_cache: dict[str, ast.Module],
) -> bool:
    """Best-effort: scan modules for `importlib.import_module(...)`
    calls whose first arg starts with '.' (relative import) or is a
    known formats_init name. The static analog is imperfect; we err
    on the side of detection for the formats_init case specifically."""
    for rel_str, mod in module_cache.items():
        for node in ast.walk(mod):
            if isinstance(node, ast.Call):
                func = node.func
                fname = None
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "import_module"
                ):
                    fname = "import_module"
                elif (
                    isinstance(func, ast.Name)
                    and func.id == "import_module"
                ):
                    fname = "import_module"
                if fname is None:
                    continue
                # First positional arg
                args = node.args
                if not args:
                    continue
                first = args[0]
                if isinstance(first, ast.Constant) and isinstance(
                    first.value, str
                ):
                    s = first.value
                    if s.startswith(".") or "formats_init" in s:
                        return True
    return False


# ---------------------------------------------------------------------------
# C5: PLAN.md fabrication
# ---------------------------------------------------------------------------


def _check_plan_fabrication(
    scaffold_root: Path,
    plan_phases: list[dict],
) -> list[Finding]:
    findings: list[Finding] = []
    for phase in plan_phases:
        for dp in phase.get("paths") or []:
            if not dp or not dp.strip():
                continue
            cand = _resolve_plan_path(scaffold_root, dp)
            # For absolute paths use the path as-is in the report; for
            # relative paths preserve the original norm style.
            if Path(dp).is_absolute():
                norm = str(cand)
            else:
                norm = dp.lstrip("./")
                if not norm:
                    continue
            if cand.exists():
                continue
            findings.append(Finding(
                category=Category.FABRICATION,
                severity=Severity.HIGH,
                path=norm,
                line=None,
                detail=(
                    f"PLAN.md phase {phase.get('id')} declares path "
                    f"{norm!r} which does not exist on disk; "
                    "n=5 r4 fabrication pattern"
                ),
                evidence={
                    "phase_id": phase.get("id"),
                    "phase_title": phase.get("title"),
                    "declared_path": norm,
                },
            ))
    return findings


# ---------------------------------------------------------------------------
# PLAN.md parsing (with verify_phase_tool fallback)
# ---------------------------------------------------------------------------


def _load_plan_phases(
    scaffold_root: Path,
    plan_md_path: Optional[Path],
) -> list[dict]:
    """Returns a list of dicts: {id, title, paths}.

    Order of resolution:
      1. If `plan_md_path` provided and exists, parse it.
      2. Else: try `<scaffold_root>/PLAN.md`.
      3. Else: return [].

    Tries `verify_phase_tool.parse_plan_md` first (richer, well-tested
    parser) and falls back to a minimal inline parser on import failure
    or ToolError.
    """
    if plan_md_path is not None:
        p = Path(plan_md_path)
    else:
        p = scaffold_root / "PLAN.md"

    if not p.exists():
        return []

    # Try the well-tested parser first
    try:
        # Add this directory to sys.path temporarily so we can import
        here = Path(__file__).parent
        if str(here) not in sys.path:
            sys.path.insert(0, str(here))
        from verify_phase_tool import parse_plan_md  # type: ignore
        try:
            phases = parse_plan_md(p)
            return [
                {"id": ph.id, "title": ph.title, "paths": list(ph.paths)}
                for ph in phases
            ]
        except Exception:
            pass
    except Exception:
        pass

    # Fallback inline parser: extract `## Phase N:` blocks and
    # `Paths: ...` lines, comma-split.
    text = _read_text(p)
    if text is None:
        return []
    import re
    phase_re = re.compile(
        r"^##\s+Phase\s+(\d+)\s*:?\s*(.*?)\s*$", re.IGNORECASE
    )
    lines = text.splitlines()
    headers: list[tuple[int, int, str]] = []
    for i, raw in enumerate(lines):
        m = phase_re.match(raw)
        if m:
            try:
                pid = int(m.group(1))
            except ValueError:
                continue
            headers.append((i, pid, m.group(2).strip()))

    phases: list[dict] = []
    for j, (start, pid, title) in enumerate(headers):
        end = headers[j + 1][0] if j + 1 < len(headers) else len(lines)
        paths_list: list[str] = []
        for bl in lines[start + 1:end]:
            stripped = bl.strip().lstrip("-* \t")
            low = stripped.lower()
            if low.startswith("paths:"):
                idx = stripped.lower().find("paths:")
                rest = stripped[idx + len("paths:"):].strip()
                if rest:
                    paths_list = [
                        s.strip() for s in rest.split(",") if s.strip()
                    ]
                break
        phases.append({"id": pid, "title": title, "paths": paths_list})
    return phases


# ---------------------------------------------------------------------------
# Verdict computation
# ---------------------------------------------------------------------------


def _severity_value(f: Finding) -> str:
    if isinstance(f.severity, Severity):
        return f.severity.value
    return str(f.severity)


def _compute_verdicts(
    findings: list[Finding],
) -> tuple[bool, bool]:
    """Strict: 0 high, <= 1 medium.
    Charitable: <= 2 high, <= 4 medium.

    Rationale (per brief): r7.10 r4 had ~3 high (fake PDF + duplicate
    symbol + registry shadow) and was scored "charitable yes" in the
    rescore; we want charitable to capture "real but flawed" without
    admitting "extensively broken" implementations.
    """
    high = sum(
        1 for f in findings if _severity_value(f) == Severity.HIGH.value
    )
    medium = sum(
        1 for f in findings if _severity_value(f) == Severity.MEDIUM.value
    )
    strict = (high == 0) and (medium <= 1)
    charitable = (high <= 2) and (medium <= 4)
    return strict, charitable


def _sort_findings(findings: list[Finding]) -> list[Finding]:
    order = {
        Severity.HIGH.value: 0,
        Severity.MEDIUM.value: 1,
        Severity.LOW.value: 2,
    }
    return sorted(
        findings,
        key=lambda f: (
            order.get(_severity_value(f), 3),
            (f.path or ""),
            (f.line or 0),
        ),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def verify_scaffold(
    scaffold_root: Union[str, Path],
    *,
    plan_md_path: Union[str, Path, None] = None,
) -> VerifyReport:
    """Run all five content-verification checks and return a
    VerifyReport. Pure: no mutation, no network, no subprocess."""
    root = Path(scaffold_root).resolve()
    plan_p = Path(plan_md_path).resolve() if plan_md_path else None

    plan_phases = _load_plan_phases(root, plan_p)

    findings: list[Finding] = []
    findings.extend(_check_serializers(root, plan_phases))
    findings.extend(_check_wired_api(root, plan_phases))
    findings.extend(_check_test_stubs(root))
    findings.extend(_check_duplicate_symbols(root))
    findings.extend(_check_plan_fabrication(root, plan_phases))

    findings = _sort_findings(findings)
    strict, charitable = _compute_verdicts(findings)

    files_inspected = sorted(
        str(p.relative_to(root))
        for p in _walk_python_files(root, include_tests=True)
    )

    if strict:
        summary = (
            f"strict pass — {len(findings)} finding(s), all "
            "low-severity"
        )
    elif charitable:
        high_n = sum(
            1 for f in findings
            if _severity_value(f) == Severity.HIGH.value
        )
        summary = (
            f"charitable pass — {high_n} high-severity finding(s); "
            "real-but-flawed implementation"
        )
    else:
        high_n = sum(
            1 for f in findings
            if _severity_value(f) == Severity.HIGH.value
        )
        summary = (
            f"both verdicts fail — {high_n} high-severity finding(s); "
            "fabrication or extensive incoherence"
        )

    return VerifyReport(
        strict_passed=strict,
        charitable_passed=charitable,
        findings=findings,
        files_inspected=files_inspected,
        summary=summary,
        plan_md_phases=plan_phases,
        scaffold_root=str(root),
    )


def report_to_dict(report: VerifyReport) -> dict:
    return {
        "scaffold_root": report.scaffold_root,
        "strict_passed": report.strict_passed,
        "charitable_passed": report.charitable_passed,
        "summary": report.summary,
        "files_inspected": report.files_inspected,
        "plan_md_phases": report.plan_md_phases,
        "findings": [
            {
                "category": f.category_value(),
                "severity": f.severity_value(),
                "path": f.path,
                "line": f.line,
                "detail": f.detail,
                "evidence": _json_safe(f.evidence),
            }
            for f in report.findings
        ],
    }


def _json_safe(obj: Any) -> Any:
    """Recursively coerce evidence dicts to JSON-safe primitives."""
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(x) for x in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    return repr(obj)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Content-verified scoring of an r7.10/r7.11 scaffold. "
            "Returns exit 0 if strict_passed, 1 otherwise."
        ),
    )
    parser.add_argument("scaffold_root")
    parser.add_argument(
        "--plan-md",
        default=None,
        help="explicit PLAN.md path (default: <scaffold_root>/PLAN.md)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON to stdout",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="emit the tier-4 judge brief format to stdout",
    )
    args = parser.parse_args(argv)

    report = verify_scaffold(
        args.scaffold_root, plan_md_path=args.plan_md
    )

    if args.json:
        print(json.dumps(report_to_dict(report), indent=2,
                         sort_keys=True))
    elif args.brief:
        print(report.as_judge_brief())
    else:
        print(
            f"strict: {report.strict_passed}, "
            f"charitable: {report.charitable_passed}"
        )
        print(f"summary: {report.summary}")
        print(f"scaffold_root: {report.scaffold_root}")
        print(
            f"files_inspected: {len(report.files_inspected)} "
            ".py file(s)"
        )
        if report.plan_md_phases:
            print(
                f"plan_md_phases: {len(report.plan_md_phases)} phase(s)"
            )
        if not report.findings:
            print("findings: none.")
        else:
            print(f"findings ({len(report.findings)}):")
            for f in report.findings:
                where = f.path or "<project>"
                if f.line is not None:
                    where = f"{where}:{f.line}"
                print(
                    f"  [{f.severity_value()}/"
                    f"{f.category_value()}] {where}: {f.detail}"
                )

    return 0 if report.strict_passed else 1


if __name__ == "__main__":
    sys.exit(_main())
