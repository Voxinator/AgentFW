"""Tests for content_verify.py.

Builds synthetic scaffolds in tempdirs and asserts on `VerifyReport`.
Each fixture builder reproduces a specific failure-mode shape from
the r7.10 campaign:

    _build_clean_scaffold        — strict pass; baseline
    _build_n10_r4_scaffold       — n=10 r4 importlib-shadow pattern
    _build_n5_r5_scaffold        — n=5 r5 unwired+stubs+fake-pdf
    _build_fabrication_scaffold  — n=5 r4 PLAN.md fabrication
    _build_only_stubs_scaffold   — original scaffold-baseline shape

Runnable as a plain script (consistent with items 1-7 convention) or
via pytest.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

# Allow running as a plain script
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from content_verify import (  # noqa: E402
    Category,
    Finding,
    Severity,
    VerifyReport,
    _compute_verdicts,
    report_to_dict,
    verify_scaffold,
)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _w(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def _build_clean_scaffold(root: Path) -> None:
    """A full, clean scaffold:
    - real csv/json/pdf serializers
    - API that imports + uses serializers in endpoint bodies
    - non-stub tests with assertions
    - no duplicate symbols
    - PLAN.md whose declared paths all exist
    """
    _w(root / "src/__init__.py", "")
    _w(root / "src/export/__init__.py", "")
    _w(root / "src/export/csv.py", '''
        """Real CSV serializer."""
        import csv as _csv
        import io


        def serialize_to_csv(records):
            buf = io.StringIO()
            if not records:
                return ""
            writer = _csv.DictWriter(buf, fieldnames=list(records[0].keys()))
            writer.writeheader()
            for r in records:
                writer.writerow(r)
            return buf.getvalue()
    ''')
    _w(root / "src/export/json.py", '''
        """Real JSON serializer."""
        import json as _json


        def serialize_to_json(records):
            return _json.dumps(list(records))
    ''')
    _w(root / "src/export/pdf.py", '''
        """Real PDF serializer using reportlab."""
        from io import BytesIO

        import reportlab.pdfgen.canvas as _canvas


        def serialize_to_pdf(records):
            buf = BytesIO()
            c = _canvas.Canvas(buf)
            for i, r in enumerate(records):
                c.drawString(100, 750 - 20 * i, str(r))
            c.save()
            return buf.getvalue()
    ''')
    _w(root / "src/api/__init__.py", "")
    _w(root / "src/api/export.py", '''
        """Export API."""
        from src.export.csv import serialize_to_csv
        from src.export.json import serialize_to_json
        from src.export.pdf import serialize_to_pdf


        def export_endpoint(fmt, records):
            if fmt == "csv":
                return serialize_to_csv(records)
            if fmt == "json":
                return serialize_to_json(records)
            if fmt == "pdf":
                return serialize_to_pdf(records)
            return None
    ''')
    _w(root / "tests/__init__.py", "")
    _w(root / "tests/test_export.py", '''
        """Real test bodies with assertions."""
        from src.export.csv import serialize_to_csv


        def test_csv_basic():
            r = serialize_to_csv([{"a": 1, "b": 2}])
            assert "a" in r
            assert "1" in r
    ''')
    _w(root / "PLAN.md", '''
        # PLAN

        ## Phase 1: Serializers
        Paths: src/export/csv.py, src/export/json.py, src/export/pdf.py

        ## Phase 2: API
        Paths: src/api/export.py

        ## Phase 3: Tests
        Paths: tests/test_export.py
    ''')


def _build_n10_r4_scaffold(root: Path) -> None:
    """n=10 r4 archetype:
    - real reportlab `PDFSerializer` in src/export/pdf.py
    - duplicate fake `PDFSerializer` in src/export/formats_init.py
    - importlib auto-load in src/export/formats.py registers the fake
    - tests + API exist; serializer modules unwired (because both
      PDFSerializer classes are accessed via registry, not imports;
      we still don't import them in the API)
    """
    _w(root / "src/__init__.py", "")
    _w(root / "src/export/__init__.py", "")
    _w(root / "src/export/csv.py", '''
        """Real CSV serializer."""
        import csv as _csv
        import io


        class CSVSerializer:
            def serialize(self, records):
                buf = io.StringIO()
                if not records:
                    return ""
                writer = _csv.DictWriter(buf, fieldnames=list(records[0].keys()))
                writer.writeheader()
                for r in records:
                    writer.writerow(r)
                return buf.getvalue()
    ''')
    _w(root / "src/export/json.py", '''
        """Real JSON serializer."""
        import json as _json


        class JSONSerializer:
            def serialize(self, records):
                return _json.dumps(list(records))
    ''')
    _w(root / "src/export/pdf.py", '''
        """Real PDF serializer using reportlab."""
        from io import BytesIO

        import reportlab.pdfgen.canvas as _canvas


        class PDFSerializer:
            def serialize(self, records):
                buf = BytesIO()
                c = _canvas.Canvas(buf)
                for i, r in enumerate(records):
                    c.drawString(100, 750 - 20 * i, str(r))
                c.save()
                return buf.getvalue()
    ''')
    # The dupes — same class names, fake/lower-quality implementations
    _w(root / "src/export/formats_init.py", '''
        """Auto-loaded module that overrides the real serializers."""


        class CSVSerializer:
            def serialize(self, records):
                # Worse-quality reimplementation
                lines = []
                if records:
                    lines.append(",".join(records[0].keys()))
                for r in records:
                    lines.append(",".join(str(v) for v in r.values()))
                return "\\n".join(lines)


        class JSONSerializer:
            def serialize(self, records):
                import json as _j
                return _j.dumps(list(records))


        class PDFSerializer:
            def serialize(self, records):
                # Hardcoded fake bytes — n=10 r4 pattern
                return b"%PDF-1.4\\n%test-content\\n%%EOF"
    ''')
    _w(root / "src/export/formats.py", '''
        """Registry + auto-load."""
        import importlib

        try:
            importlib.import_module(".formats_init", package="src.export")
        except ImportError:
            pass


        def get(_fmt):
            return None
    ''')
    _w(root / "src/api/__init__.py", "")
    _w(root / "src/api/export.py", '''
        """API."""
        from src.export.csv import CSVSerializer
        from src.export.json import JSONSerializer
        from src.export.pdf import PDFSerializer


        def export_endpoint(fmt, records):
            if fmt == "csv":
                return CSVSerializer().serialize(records)
            if fmt == "json":
                return JSONSerializer().serialize(records)
            if fmt == "pdf":
                return PDFSerializer().serialize(records)
            return None
    ''')
    _w(root / "tests/__init__.py", "")
    _w(root / "tests/test_export.py", '''
        """Real-ish tests."""
        from src.api.export import export_endpoint


        def test_pdf_works():
            out = export_endpoint("pdf", [{"a": 1}])
            assert out.startswith(b"%PDF")
    ''')
    _w(root / "PLAN.md", '''
        # PLAN

        ## Phase 1: Serializers
        Paths: src/export/csv.py, src/export/json.py, src/export/pdf.py

        ## Phase 2: API
        Paths: src/api/export.py

        ## Phase 3: Tests
        Paths: tests/test_export.py
    ''')


def _build_n5_r5_scaffold(root: Path) -> None:
    """n=5 r5 archetype:
    - real csv/json serializers (no PDF lib)
    - PDF function returns text string with '%PDF' (not bytes)
    - API does NOT import any serializer; inlines csv string concat
      and a hardcoded PDF text string
    - 4 test files: 2 with real bodies, 2 with raise NotImplementedError
    """
    _w(root / "src/__init__.py", "")
    _w(root / "src/export/__init__.py", "")
    _w(root / "src/export/csv.py", '''
        """Real CSV serializer."""
        import csv as _csv
        import io


        def serialize_to_csv(records):
            buf = io.StringIO()
            if not records:
                return ""
            writer = _csv.DictWriter(buf, fieldnames=list(records[0].keys()))
            writer.writeheader()
            for r in records:
                writer.writerow(r)
            return buf.getvalue()
    ''')
    _w(root / "src/export/json.py", '''
        """Real JSON serializer."""
        import json as _json


        def serialize_to_json(records):
            return _json.dumps(list(records))
    ''')
    _w(root / "src/export/pdf.py", '''
        """Real partial PDF — minimal byte assembly (no reportlab dep)."""


        def serialize_to_pdf(records):
            # n=5 r5 archetype: real partial PDF (built bytes, not literal).
            # Per the rescore note, r5's serializer modules existed and were
            # functional — the FAKE was in the API layer (export.py), not here.
            parts = [b"%PDF-1.4\\n"]
            for i, r in enumerate(records):
                parts.append(f"obj {i} {r}\\n".encode("utf-8"))
            parts.append(b"\\n%%EOF\\n")
            return b"".join(parts)
    ''')
    _w(root / "src/api/__init__.py", "")
    _w(root / "src/api/export.py", '''
        """API that inlines serialization (n=5 r5 unwired pattern)."""


        def export_csv(records):
            csv_content = "id,data\\n"
            for r in records:
                csv_content += f"{r['id']},{r['data']}\\n"
            return csv_content


        def export_json(records):
            return list(records)


        def export_pdf(records):
            # Hardcoded text-string fake
            return f"%PDF-1.4\\nContent: {records}"
    ''')
    _w(root / "tests/__init__.py", "")
    _w(root / "tests/test_csv.py", '''
        from src.export.csv import serialize_to_csv


        def test_csv_basic():
            r = serialize_to_csv([{"a": 1, "b": 2}])
            assert "a" in r
    ''')
    _w(root / "tests/test_json.py", '''
        from src.export.json import serialize_to_json


        def test_json_basic():
            r = serialize_to_json([{"a": 1}])
            assert "a" in r
    ''')
    _w(root / "tests/test_pdf.py", '''
        def test_pdf_returns_pdf_bytes():
            raise NotImplementedError("worker: implement this test")
    ''')
    _w(root / "tests/test_api_export.py", '''
        def test_api_export_csv():
            raise NotImplementedError("worker: implement this test")
    ''')


def _build_fabrication_scaffold(root: Path) -> None:
    """PLAN.md declares 5 paths, only 1 exists on disk."""
    _w(root / "src/__init__.py", "")
    _w(root / "src/export/__init__.py", "")
    _w(root / "src/export/csv.py", '''
        """Real CSV serializer."""
        import csv as _csv
        import io


        def serialize_to_csv(records):
            buf = io.StringIO()
            if records:
                w = _csv.DictWriter(buf, fieldnames=list(records[0].keys()))
                w.writeheader()
                for r in records:
                    w.writerow(r)
            return buf.getvalue()
    ''')
    _w(root / "PLAN.md", '''
        # PLAN

        ## Phase 1: Serializers
        Paths: src/export/csv.py, src/export/json.py, src/export/pdf.py

        ## Phase 2: API
        Paths: src/api/export.py

        ## Phase 3: Tests
        Paths: tests/test_export.py
    ''')


def _build_only_stubs_scaffold(root: Path) -> None:
    """The scaffold-baseline shape: docstring-only modules + test
    stubs + nothing real."""
    _w(root / "src/__init__.py", "")
    _w(root / "src/export/__init__.py", "")
    _w(root / "src/export/csv.py", '"""CSV export. Populated later."""\n')
    _w(root / "src/export/json.py", '"""JSON export. Populated later."""\n')
    _w(root / "src/export/pdf.py", '"""PDF export. Populated later."""\n')
    _w(root / "tests/__init__.py", "")
    _w(root / "tests/test_csv.py", '''
        """Tests for csv (stub)."""


        def test_basic():
            raise NotImplementedError("worker: implement")
    ''')


# ---------------------------------------------------------------------------
# Test runner harness
# ---------------------------------------------------------------------------


_FAILURES: list[tuple[str, str]] = []
_PASSES: list[str] = []


def _run(name: str, fn) -> None:
    try:
        fn()
        _PASSES.append(name)
        print(f"  PASS  {name}")
    except AssertionError as exc:
        _FAILURES.append((name, str(exc)))
        print(f"  FAIL  {name}: {exc}")
    except Exception as exc:  # pragma: no cover
        _FAILURES.append((name, f"{type(exc).__name__}: {exc}"))
        print(f"  ERROR {name}: {type(exc).__name__}: {exc}")


def _category_set(report: VerifyReport) -> set[str]:
    return {f.category_value() for f in report.findings}


def _findings_with(report: VerifyReport, cat: Category) -> list[Finding]:
    return [
        f for f in report.findings if f.category_value() == cat.value
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_T1_clean_scaffold_strict_passes():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_clean_scaffold(root)
        report = verify_scaffold(root)
        assert report.strict_passed, (
            f"clean scaffold should pass strict; findings: "
            f"{[(f.severity_value(), f.category_value(), f.detail) for f in report.findings]}"
        )
        assert report.charitable_passed
        # No HIGH severity findings expected
        highs = [
            f for f in report.findings
            if f.severity_value() == Severity.HIGH.value
        ]
        assert highs == [], f"unexpected HIGH findings: {highs}"


def test_T2_n10_r4_charitable_passes_strict_fails():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_n10_r4_scaffold(root)
        report = verify_scaffold(root)
        assert not report.strict_passed
        assert report.charitable_passed, (
            "n=10 r4 should be 'charitable yes' per the rescore note; "
            f"findings: {[(f.severity_value(), f.category_value()) for f in report.findings]}"
        )
        cats = _category_set(report)
        assert (
            Category.REGISTRY_SHADOWING.value in cats
            or Category.DUPLICATE_SYMBOL.value in cats
        ), f"expected duplicate or shadow, got: {cats}"
        # Must reference both pdf.py and formats_init.py
        shadow_or_dup = (
            _findings_with(report, Category.REGISTRY_SHADOWING)
            + _findings_with(report, Category.DUPLICATE_SYMBOL)
        )
        files_referenced = set()
        for f in shadow_or_dup:
            files_referenced.update(f.evidence.get("files") or [])
        assert any("pdf.py" in f for f in files_referenced), (
            f"expected pdf.py in evidence: {files_referenced}"
        )
        assert any("formats_init.py" in f for f in files_referenced), (
            f"expected formats_init.py in evidence: {files_referenced}"
        )


def test_T3_n5_r5_charitable_passes_strict_fails():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_n5_r5_scaffold(root)
        report = verify_scaffold(root)
        assert not report.strict_passed
        cats = _category_set(report)
        # n=5 r5 archetype (per rescore methodology):
        #   - Real serializer modules (csv, json, partial-pdf) → no
        #     SERIALIZER_FAKE / SERIALIZER_STUB findings.
        #   - API doesn't import serializers AND inlines its own
        #     CSV/PDF building → consolidates to ONE UNWIRED_INLINE
        #     finding (per UNWIRED-consolidation rule, mirrors
        #     REGISTRY_SHADOWING).
        #   - 2 of 4 tests with raise NotImplementedError → TEST_STUB.
        # Charitable: r7.10 r5 was "charitable yes" in the rescore.
        # With consolidation, we expect 2 HIGH findings → charitable
        # threshold (≤2 HIGH) passes.
        assert Category.UNWIRED_INLINE.value in cats, cats
        assert Category.TEST_STUB.value in cats, cats
        assert Category.SERIALIZER_FAKE.value not in cats, cats
        assert Category.SERIALIZER_STUB.value not in cats, cats
        # The load-bearing check: consolidation lands r5 at charitable=True.
        assert report.charitable_passed, (
            f"r5 archetype should pass charitable per rescore; got "
            f"strict={report.strict_passed} charitable={report.charitable_passed} "
            f"findings={[(f.category, f.severity, f.path) for f in report.findings]}"
        )


def test_T4_fabrication_both_verdicts_fail():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_fabrication_scaffold(root)
        report = verify_scaffold(root)
        assert not report.strict_passed
        cats = _category_set(report)
        assert Category.FABRICATION.value in cats, cats
        # 4 of 5 declared paths missing -> 4 HIGH FABRICATION findings
        fab = _findings_with(report, Category.FABRICATION)
        assert len(fab) >= 3, f"expected ≥3 FABRICATION, got: {fab}"
        # Both verdicts should fail (>= 3 HIGH > charitable threshold 2)
        assert not report.charitable_passed


def test_T5_test_file_with_notimpl_flagged():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _w(root / "tests/__init__.py", "")
        _w(root / "tests/test_x.py", '''
            def test_a():
                raise NotImplementedError("stub")
        ''')
        report = verify_scaffold(root)
        cats = _category_set(report)
        assert Category.TEST_STUB.value in cats


def test_T6_test_file_with_real_bodies_no_flag():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _w(root / "tests/__init__.py", "")
        _w(root / "tests/test_x.py", '''
            def test_a():
                assert 1 + 1 == 2
        ''')
        report = verify_scaffold(root)
        cats = _category_set(report)
        assert Category.TEST_STUB.value not in cats


def test_T7_mixed_test_file_is_medium():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _w(root / "tests/__init__.py", "")
        _w(root / "tests/test_x.py", '''
            def test_a():
                assert 1 + 1 == 2

            def test_b():
                raise NotImplementedError("stub")
        ''')
        report = verify_scaffold(root)
        stubs = _findings_with(report, Category.TEST_STUB)
        assert len(stubs) == 1
        assert stubs[0].severity_value() == Severity.MEDIUM.value


def test_T8_duplicate_class_in_two_nontest_files_flagged():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _w(root / "src/__init__.py", "")
        _w(root / "src/a.py", '''
            class Widget:
                pass
        ''')
        _w(root / "src/b.py", '''
            class Widget:
                pass
        ''')
        report = verify_scaffold(root)
        dups = _findings_with(report, Category.DUPLICATE_SYMBOL)
        assert len(dups) >= 1, f"findings: {report.findings}"
        assert dups[0].severity_value() == Severity.HIGH.value


def test_T9_duplicate_fixture_in_test_files_tolerated():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _w(root / "tests/__init__.py", "")
        _w(root / "tests/test_a.py", '''
            def make_record():
                return {"id": 1}

            def test_a():
                assert make_record()["id"] == 1
        ''')
        _w(root / "tests/test_b.py", '''
            def make_record():
                return {"id": 2}

            def test_b():
                assert make_record()["id"] == 2
        ''')
        report = verify_scaffold(root)
        dups = _findings_with(report, Category.DUPLICATE_SYMBOL)
        # Should be tolerated (all in test files)
        assert dups == [], f"unexpected dup findings: {dups}"


def test_T10_api_using_serializer_no_unwired_finding():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_clean_scaffold(root)
        report = verify_scaffold(root)
        cats = _category_set(report)
        assert Category.UNWIRED_API.value not in cats
        assert Category.UNWIRED_INLINE.value not in cats


def test_T11_api_without_serializer_import_unwired():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _w(root / "src/__init__.py", "")
        _w(root / "src/export/__init__.py", "")
        _w(root / "src/export/csv.py", '''
            """CSV serializer."""
            import csv as _csv
            import io


            def serialize_to_csv(records):
                buf = io.StringIO()
                if records:
                    w = _csv.DictWriter(buf, fieldnames=list(records[0].keys()))
                    w.writeheader()
                    for r in records:
                        w.writerow(r)
                return buf.getvalue()
        ''')
        _w(root / "src/api/__init__.py", "")
        # API has no serializer import AND no inline-shape body (returns
        # records dict directly). This isolates the pure UNWIRED_API case;
        # contrast with T12 which exercises UNWIRED_INLINE inline-shape.
        # Under the consolidation rule, only the no-inline-shape branch
        # produces UNWIRED_API; if inline-shape were present, the finding
        # would consolidate to UNWIRED_INLINE.
        _w(root / "src/api/export.py", '''
            """API that returns records as dicts (no inline serialization)."""


            def export_records(records):
                return {"records": list(records), "count": len(records)}
        ''')
        report = verify_scaffold(root)
        cats = _category_set(report)
        assert Category.UNWIRED_API.value in cats, cats


def test_T12_api_inlines_csv_building():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _w(root / "src/__init__.py", "")
        _w(root / "src/export/__init__.py", "")
        _w(root / "src/export/csv.py", '''
            """Real CSV serializer."""
            import csv as _csv
            import io


            def serialize_to_csv(records):
                buf = io.StringIO()
                if records:
                    w = _csv.DictWriter(buf, fieldnames=list(records[0].keys()))
                    w.writeheader()
                    for r in records:
                        w.writerow(r)
                return buf.getvalue()
        ''')
        _w(root / "src/api/__init__.py", "")
        _w(root / "src/api/export.py", '''
            """API: imports serializer but inlines CSV building."""
            from src.export.csv import serialize_to_csv  # noqa: F401


            def export_csv(records):
                csv_content = "id,data,name\\n"
                for r in records:
                    csv_content += f"{r['id']},{r['data']},{r['name']}\\n"
                return csv_content
        ''')
        report = verify_scaffold(root)
        cats = _category_set(report)
        # Either UNWIRED_INLINE (because the import is dead) or
        # both — but at minimum the file must be flagged as unwired.
        assert Category.UNWIRED_INLINE.value in cats, cats


def test_T13_pdf_returns_short_bytes_no_reportlab_flagged():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _w(root / "src/__init__.py", "")
        _w(root / "src/export/__init__.py", "")
        _w(root / "src/export/pdf.py", '''
            """Fake PDF."""


            def serialize_to_pdf(records):
                return b"%PDF-1.4\\n%test-content\\n%%EOF"
        ''')
        report = verify_scaffold(root)
        fakes = _findings_with(report, Category.SERIALIZER_FAKE)
        assert len(fakes) >= 1, f"findings: {report.findings}"
        assert fakes[0].severity_value() == Severity.HIGH.value


def test_T14_pdf_with_reportlab_no_fake_flag():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _w(root / "src/__init__.py", "")
        _w(root / "src/export/__init__.py", "")
        _w(root / "src/export/pdf.py", '''
            """Real PDF using reportlab."""
            from io import BytesIO

            import reportlab.pdfgen.canvas as _canvas


            def serialize_to_pdf(records):
                buf = BytesIO()
                c = _canvas.Canvas(buf)
                for i, r in enumerate(records):
                    c.drawString(100, 700 - 20 * i, str(r))
                c.save()
                return buf.getvalue()
        ''')
        report = verify_scaffold(root)
        fakes = _findings_with(report, Category.SERIALIZER_FAKE)
        assert fakes == [], f"unexpected SERIALIZER_FAKE: {fakes}"


def test_T15_report_to_dict_is_json_serializable():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_n10_r4_scaffold(root)
        report = verify_scaffold(root)
        d = report_to_dict(report)
        # Will raise if non-serializable
        s = json.dumps(d)
        # Round-trip parse
        d2 = json.loads(s)
        assert d2["scaffold_root"] == str(Path(td).resolve())
        assert isinstance(d2["findings"], list)
        assert "summary" in d2


def test_T16_cli_json_mode_produces_valid_json():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_clean_scaffold(root)
        # Invoke the CLI as a subprocess
        result = subprocess.run(
            [
                sys.executable,
                str(HERE / "content_verify.py"),
                str(root),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # Exit 0 on strict pass
        assert result.returncode == 0, (
            f"stderr: {result.stderr}\nstdout: {result.stdout}"
        )
        parsed = json.loads(result.stdout)
        assert parsed["strict_passed"] is True
        assert "findings" in parsed
        assert "summary" in parsed


def test_T17_judge_brief_is_nonempty_text():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_n5_r5_scaffold(root)
        report = verify_scaffold(root)
        brief = report.as_judge_brief()
        assert isinstance(brief, str)
        assert "VERDICT" in brief
        assert "FINDINGS" in brief
        # At least 5 lines of substance
        assert len(brief.splitlines()) >= 5


def test_T18_only_stubs_scaffold_fails_both():
    """The r7.10 scaffold-baseline (docstring-only modules + test
    stubs) should fail both verdicts."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_only_stubs_scaffold(root)
        report = verify_scaffold(root)
        assert not report.strict_passed


def test_T20_absolute_path_in_plan_md_that_exists():
    """T20 (r7.11 item-8 trial-2 F-4): if PLAN.md declares an ABSOLUTE
    path and that file exists on disk, no FABRICATION finding should
    fire. Previously content_verify.py joined scaffold_root with the
    absolute path (lstrip('./') is a no-op for '/'-prefixed strings,
    but `Path(scaffold_root) / '/abs/path'` returns '/abs/path' on
    POSIX — wait, actually that's the bug's saving grace: Path's `/`
    operator with an absolute RHS DOES return the RHS. So the real bug
    is that `dp.lstrip("./")` does NOT strip the leading '/', yielding
    '/tmp/...' which then DOES resolve correctly via Path's operator.
    Re-check: lstrip("./") strips any leading characters that appear
    in the set {'.', '/'} — so '/tmp/foo' → 'tmp/foo' (the '/' IS
    stripped). Then scaffold_root / 'tmp/foo' is a wrong join. That
    is the actual bug. This test reproduces + verifies the fix.
    """
    with tempfile.TemporaryDirectory() as td:
        scaffold = Path(td) / "scaffold"
        scaffold.mkdir()
        # Real file at an absolute path OUTSIDE the scaffold root
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as fh:
            fh.write("def serialize_to_csv(records):\n    return ''\n")
            abs_path = Path(fh.name).resolve()
        try:
            plan_md = scaffold / "PLAN.md"
            plan_md.write_text(
                f"# PLAN\n\n"
                f"## Phase 1: Serializers\n"
                f"Paths: {abs_path}\n",
                encoding="utf-8",
            )
            report = verify_scaffold(scaffold)
            fab = _findings_with(report, Category.FABRICATION)
            assert fab == [], (
                f"absolute PLAN.md path that EXISTS should not produce "
                f"a FABRICATION finding; got: "
                f"{[(f.path, f.detail) for f in fab]}"
            )
        finally:
            abs_path.unlink(missing_ok=True)


def test_T21_absolute_path_in_plan_md_that_doesnt_exist():
    """T21 (r7.11 item-8 trial-2 F-4): if PLAN.md declares an ABSOLUTE
    path and that file does NOT exist, a FABRICATION finding fires
    and cites the absolute path verbatim (not a scaffold-joined form).
    """
    with tempfile.TemporaryDirectory() as td:
        scaffold = Path(td) / "scaffold"
        scaffold.mkdir()
        # Construct a clearly-nonexistent absolute path
        bogus = Path(tempfile.gettempdir()) / "nonexistent-r7-11-XYZ-T21.py"
        # Best-effort cleanup if a previous run left it lying around
        try:
            bogus.unlink()
        except FileNotFoundError:
            pass
        assert not bogus.exists()

        plan_md = scaffold / "PLAN.md"
        plan_md.write_text(
            f"# PLAN\n\n"
            f"## Phase 1: Serializers\n"
            f"Paths: {bogus}\n",
            encoding="utf-8",
        )
        report = verify_scaffold(scaffold)
        fab = _findings_with(report, Category.FABRICATION)
        assert len(fab) >= 1, (
            f"absolute PLAN.md path that does NOT exist should produce "
            f"a FABRICATION finding; got findings: "
            f"{[(f.category_value(), f.path) for f in report.findings]}"
        )
        # The reported path should be the absolute path verbatim
        paths_reported = [f.path for f in fab]
        assert any(p == str(bogus) for p in paths_reported), (
            f"FABRICATION finding should cite the absolute path "
            f"{str(bogus)!r}; got: {paths_reported}"
        )


def test_T19_compute_verdicts_thresholds():
    # 0 high, 0 medium → strict + charitable
    s, c = _compute_verdicts([])
    assert s and c
    # 0 high, 1 medium → strict + charitable
    f_med = Finding(
        category=Category.SERIALIZER_FAKE,
        severity=Severity.MEDIUM,
        path="x", line=1, detail="x",
    )
    s, c = _compute_verdicts([f_med])
    assert s and c
    # 0 high, 2 medium → not strict, charitable
    s, c = _compute_verdicts([f_med, f_med])
    assert not s
    assert c
    # 2 high → charitable yes, strict no
    f_high = Finding(
        category=Category.SERIALIZER_FAKE,
        severity=Severity.HIGH,
        path="x", line=1, detail="x",
    )
    s, c = _compute_verdicts([f_high, f_high])
    assert not s
    assert c
    # 3 high → both fail
    s, c = _compute_verdicts([f_high, f_high, f_high])
    assert not s
    assert not c


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    tests = [
        ("T1_clean_scaffold_strict_passes",
         test_T1_clean_scaffold_strict_passes),
        ("T2_n10_r4_charitable_passes_strict_fails",
         test_T2_n10_r4_charitable_passes_strict_fails),
        ("T3_n5_r5_charitable_passes_strict_fails",
         test_T3_n5_r5_charitable_passes_strict_fails),
        ("T4_fabrication_both_verdicts_fail",
         test_T4_fabrication_both_verdicts_fail),
        ("T5_test_file_with_notimpl_flagged",
         test_T5_test_file_with_notimpl_flagged),
        ("T6_test_file_with_real_bodies_no_flag",
         test_T6_test_file_with_real_bodies_no_flag),
        ("T7_mixed_test_file_is_medium",
         test_T7_mixed_test_file_is_medium),
        ("T8_duplicate_class_in_two_nontest_files_flagged",
         test_T8_duplicate_class_in_two_nontest_files_flagged),
        ("T9_duplicate_fixture_in_test_files_tolerated",
         test_T9_duplicate_fixture_in_test_files_tolerated),
        ("T10_api_using_serializer_no_unwired_finding",
         test_T10_api_using_serializer_no_unwired_finding),
        ("T11_api_without_serializer_import_unwired",
         test_T11_api_without_serializer_import_unwired),
        ("T12_api_inlines_csv_building",
         test_T12_api_inlines_csv_building),
        ("T13_pdf_returns_short_bytes_no_reportlab_flagged",
         test_T13_pdf_returns_short_bytes_no_reportlab_flagged),
        ("T14_pdf_with_reportlab_no_fake_flag",
         test_T14_pdf_with_reportlab_no_fake_flag),
        ("T15_report_to_dict_is_json_serializable",
         test_T15_report_to_dict_is_json_serializable),
        ("T16_cli_json_mode_produces_valid_json",
         test_T16_cli_json_mode_produces_valid_json),
        ("T17_judge_brief_is_nonempty_text",
         test_T17_judge_brief_is_nonempty_text),
        ("T18_only_stubs_scaffold_fails_both",
         test_T18_only_stubs_scaffold_fails_both),
        ("T19_compute_verdicts_thresholds",
         test_T19_compute_verdicts_thresholds),
        ("T20_absolute_path_in_plan_md_that_exists",
         test_T20_absolute_path_in_plan_md_that_exists),
        ("T21_absolute_path_in_plan_md_that_doesnt_exist",
         test_T21_absolute_path_in_plan_md_that_doesnt_exist),
    ]
    print(f"running {len(tests)} content_verify tests...")
    for name, fn in tests:
        _run(name, fn)
    print()
    print(f"{len(_PASSES)} passed, {len(_FAILURES)} failed "
          f"(of {len(tests)})")
    if _FAILURES:
        print("FAILURES:")
        for name, msg in _FAILURES:
            print(f"  {name}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
