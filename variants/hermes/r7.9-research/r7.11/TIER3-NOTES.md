# TIER3-NOTES.md — implementation notes for verify_phase tier 3

Item 3 of the r7.11 implementation order. Pairs with `verify_phase.py`
and `test_verify_phase.py`. Notes here are for future workers (item 4
sub-tier 3.5; item 5 Hermes wrapper) and for the planner reviewing the
deterministic algorithm choices.

## Algorithm choices

**CAT1 (defined-but-never-referenced).** For each top-level def
(function/class/top-level Name target), check whether the name appears
as a non-Store Name node anywhere in the union of phase-N + tolerated
phase-M-on-disk file ASTs. Imports do not count as use (skip-listed).
Dunders (`__*__`) and a small public-API allow-list (`router`, `app`,
`application`, `api`) and `__all__` exports are exempt. Test files
are not scanned for CAT1 (test fixtures + parametrize collect names by
introspection, which AST cannot model).

**CAT2 (imported-but-never-used).** For each `import X` / `from M
import Y` (skipping TYPE_CHECKING-block imports, `__all__`-exported
names, and `*` imports), flag if the bound name is not in the file's
used_names set. Type-only imports inside `if TYPE_CHECKING:` are not
recorded as runtime imports, so they pass.

**CAT3 (test references nonexistent).** Test files only. For each
`from M import X`, resolve M to a phase-N or tolerated-phase-on-disk
file using the same most-specific-first candidate order tier 2 uses.
If resolved AND X is not in the resolved file's defined-names ∪
imported-aliases ∪ `__all__`, flag. Stdlib / venv / cross-phase-not-on-disk
all return None from the resolver and are silently passed (deferred).

**CAT4 (duplicate top-level definition).** Build a `name -> [file, ...]`
map across phase-N + tolerated-on-disk files. Flag any name appearing
in 2+ files when at least one location is in phase-N. Exemptions:
common multi-module top-level dunders (`__all__`, `__version__`,
`__author__`); the test-fixture exception (every duplicate location
is a test file).

**Phase-awareness conservativism.** When `project_phases` declares
paths in OTHER phases that are NOT yet on disk, CAT1 is fully
suppressed — we cannot inspect a not-yet-written consumer for
references, so flagging would be a false positive during phased
construction. CAT2/3/4 are unaffected because they don't depend on
unknown future references. Tier 2's deferred-import behavior continues
to keep cross-phase imports out of the integrity-issue list, so tier 3
sees no redundant violations on the same imports.

## Detection limits (what tier 3 cannot catch — bridge to 3.5)

Pattern-matching on AST cannot resolve runtime-only behavior:

- `importlib.import_module(name_built_at_runtime)` — module name
  computed from a call chain or env var.
- `getattr(module, attr_name_string)` where `module` is dynamically
  reassigned via `setattr` or rebinding.
- `exec(code_string)` / `eval(...)` — arbitrary code generation.
- `globals()[k] = obj` mutation — registers a name AST never sees.
- Conditional registration gated on env vars or first-request lazy
  init — registration doesn't fire at import time.
- Monkey-patching after import — class identity is rewritten post-load.

When tier 3 detects ANY of these markers (importlib.import_module,
__import__, pkgutil.import_module, importlib.util.find_spec/exec_module/
load_module; getattr/setattr on a known-imported module; exec/eval;
`globals()[...] = `/`locals()[...] = `), it sets `tier_3_hint` to:

> "this phase contains dynamic imports; consider invoking tier 3.5
> runtime smoke test for full coverage"

The hint is informational, not a violation — `passed` is unaffected.
The Hermes tool wrapper (item 5) will surface the hint to the parent;
the parent decides whether to re-call `verify_phase` with
`with_runtime_smoke_test=true` (item 4 / sub-tier 3.5).

## Ambiguities flagged for the planner

1. **CAT1 allow-list extensibility.** The default list (`router`,
   `app`, `application`, `api`) is hard-coded as `_PUBLIC_API_ALLOW_LIST`
   in `verify_phase.py`. There's no plumbing yet to extend it from the
   Hermes tool wrapper. If a project standardizes on different
   public-API names (e.g., `bp` for Flask blueprints, `celery_app`),
   item 5 should add a `cat1_extra_allow_list` parameter to the
   wrapper that maps onto `verify_phase` keyword args. **Not blocking
   for first-build trial.**

2. **CAT2 side-effect import false-positive risk.** `import
   logging.config`, `import importlib.metadata`, etc. are sometimes
   imported solely for the side effect of triggering submodule
   registration. Current implementation will flag the bound name
   `logging` if it's not subsequently referenced. We accepted this as
   a calibrated false-positive risk because the alternative (allow
   ALL unused submodule imports) defeats CAT2's purpose. Workaround
   for users: assign to `_` (`import logging.config as _config`) or
   reference the import once.

3. **CAT4 dunder semantics.** `__version__` and `__author__` are
   exempted because they legitimately appear in every package's
   `__init__.py`. If a project structures its plan such that two
   separate phases each write a top-level package init declaring a
   private `__version__`, we will not flag the duplication. This is
   conservative-by-default.
