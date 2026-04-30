# TIER35-NOTES — runtime smoke test (item 4)

Companion notes to `verify_phase.py`'s tier 3.5 implementation. Tier 3.5
exists specifically to catch the n=10 r4 archetype (importlib-shadowing
of a registry entry) deterministically, by importing the phase's
PLAN.md modules in a sandboxed subprocess and inspecting registry-
shaped objects for entries whose runtime `__module__` does not match
PLAN.md's declared paths.

Tier 3.5 is **opt-in**: default `with_runtime_smoke_test=False`. The
Hermes wrapper (item 5) decides when to invoke it; this module just
executes when asked. The trigger heuristic the wrapper SHOULD use is:
opt in when tier 3 sets `tier_3_hint` (dynamic-imports detected) or
when the operator explicitly requests it.

## (a) Sandbox guarantees and platform gaps

The probe runs via `subprocess.run` with:

- `cwd = scaffold_root` — relative imports work; the subprocess never
  sees the parent's working directory.
- `env` is **constructed from scratch**, not inherited. Variables set:
  `PYTHONPATH = scaffold_root`, `PATH = os.defpath` (minimal stdlib
  default), `HOME = /tmp`, `LANG/LC_ALL = C.UTF-8`, `PYTHONUNBUFFERED
  = 1`, `PYTHONDONTWRITEBYTECODE = 1`. Crucially, `OMLX_API_KEY`,
  `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, etc. — anything in the
  parent environment — does NOT leak in. Verified by test F5.
- `timeout` = `runtime_smoke_test_timeout` (default 10s; configurable).
  On `TimeoutExpired` the subprocess is killed and `[INCONCLUSIVE:
  timeout]` is reported.
- POSIX-only resource limits (set in the probe-script preamble):
  `RLIMIT_CPU` = (30s soft, 60s hard), `RLIMIT_AS` = 1 GB. Failures
  to set the limits (e.g. on Windows where `resource` is unavailable)
  are silently ignored; the subprocess timeout still applies.

**Platform gaps:**

- **Network isolation is not enforced at the kernel level.** We strip
  proxy variables from env, but do not run the probe inside a network
  namespace (`unshare -n`) or equivalent. A cooperative module that
  honors HTTP_PROXY won't reach the network; a determined module that
  hard-codes a connection still can. Documented limitation; full
  network isolation needs Linux-specific tooling and was deemed out
  of scope for an opt-in deterministic check.
- **Windows**: `resource` module is unavailable, so the CPU/memory
  rlimits don't apply. The subprocess timeout still bounds wall time.
  No cross-platform test currently runs this; the unit tests assume
  POSIX.
- **macOS**: `RLIMIT_AS` is treated as advisory by some Mach kernels;
  setting it doesn't always halt over-allocation. CPU limit is
  reliable.

## (b) Registry detection algorithm and limits

The probe scans `sys.modules` for modules whose name starts with any
top-level package declared by ANY phase (computed from the phase
plan). For each, it inspects module-level attributes:

1. **Name-pattern dict registries.** A `dict` whose attribute name is
   one of the canonical patterns OR whose lowercase name contains one
   of the substring patterns:
   - Canonical (case-sensitive): `_REGISTRY`, `REGISTRY`, `_FORMATS`,
     `FORMATS`, `registry`, `_registry`, `_handlers`, `HANDLERS`,
     `_serializers`, `SERIALIZERS`.
   - Substring (case-insensitive): `_registry`, `_handlers`,
     `_serializers`.
2. **Duck-typed registries.** A non-class instance with both
   `register()` and `get()` callable methods. The probe tries to dump
   entries by inspecting the instance's `__dict__` for the largest
   contained `dict`.

For each detected registry, every `(key, value)` pair is dumped with:
`key_repr`, `value.__module__` (for a class, the class's; for an
instance, its class's), `value.__qualname__`, `value_is_class`, and
(for instances) `repr(value)`.

The verifier then classifies each entry:

- `__module__` is in this phase's declared modules → `[CHECKED:
  entry-matches-declared]`.
- `__module__` is in another phase's declared modules →
  `[SHADOWING:registry-entry-other-phase]`.
- `__module__` is in-project (top-level pkg matches a declared root)
  but not declared by ANY phase → `[SHADOWING:registry-entry-
  undeclared]`. **This is the n=10 r4 archetype.**
- `__module__` is third-party / stdlib (no in-project top-level pkg
  match) → `[CHECKED:entry-third-party]`.

## (c) Failure-mode taxonomy

Tier 3.5 distinguishes verification-failures from tool-errors:

- `[SHADOWING:...]` — verification-failure. Sets `passed=False`.
  Contributes a registry-resolution prescription to
  `corrective_dispatch`.
- `[CHECKED:...]` — informational audit trail. Does NOT affect
  `passed`. Includes per-entry `[CHECKED:entry-matches-declared]`,
  `[CHECKED:entry-third-party]`, `[CHECKED:empty-registry]`, and
  `[CHECKED:no-registries-detected]` (the latter when scanning ran
  cleanly but matched nothing).
- `[INCONCLUSIVE:...]` — tool-error. Does NOT affect `passed`. Tier
  1-3 verdict alone determines pass/fail in this case. Sub-types:
  - `[INCONCLUSIVE:timeout]` — subprocess exceeded `timeout`.
  - `[INCONCLUSIVE:subprocess-crashed]` — non-zero exit, no parseable
    sentinel; carries a stderr excerpt.
  - `[INCONCLUSIVE:malformed-output]` — exit 0 but no findings
    sentinel found in stdout.
  - `[INCONCLUSIVE:import-error]` — a specific module raised at
    import time (other modules may still have imported and produced
    findings; this entry is informational alongside any [CHECKED]/
    [SHADOWING] entries from successful imports).
  - `[INCONCLUSIVE:no-importable-modules]` — phase declared no `.py`
    paths whose names map to valid Python identifiers.
  - `[INCONCLUSIVE:sandbox-setup-failed]` — could not spawn the
    subprocess at all (OSError) or the verifier itself raised an
    unexpected exception during setup.
- `[SKIPPED]` — emitted when `with_runtime_smoke_test=True` but tier
  1 or tier 2 failed. Tier 3.5 is gated on tiers 1+2 because there's
  no point importing files that won't parse.

The subprocess output protocol uses sentinel lines
`===TIER35-FINDINGS-START===` / `===TIER35-FINDINGS-END===` bracketing
a JSON payload; this allows the parent to extract structured findings
even if the subprocess emits other stdout (warnings, prints) before
or after.

## (d) What tier 3.5 does NOT catch (honest scope-limit)

Tier 3.5 catches:

- The importlib-shadowing pattern (n=10 r4): a registry receives a
  registration from a module unexpected per PLAN.md.
- Direct module imports that resolve registered classes/instances to
  unexpected files at runtime.

Tier 3.5 does NOT catch:

- **Logically wrong implementations that import cleanly.** A CSV
  exporter that runs but produces malformed output passes tier 3.5
  silently. (Tier 4 is the intended catcher; deferred to r7.12.)
- **Race conditions, threading, async timing.** Single-process
  import has none of these.
- **Input-dependent failures.** The probe doesn't call into the
  imported code; it only inspects module-level state after import.
- **Network-dependent runtime behavior.** Sandbox strips proxy env,
  but doesn't enforce zero-network at the kernel level.
- **Custom registry patterns the heuristic misses.** A dict named
  `lookup_table` or a registry implemented as a dataclass without
  `register`/`get` won't be detected. R4 in the test rubric pins
  this as a known limit.
- **Decorator-based registration where the registry isn't a
  module-level attribute.** If a `@register("foo")` decorator stores
  state inside a closure or module-private structure not surfaced via
  a discoverable name, it won't be inspected.
- **Side effects that occur outside import time.** Registration that
  fires on first request, on a specific env-var trigger, or via a
  late-binding hook is invisible to the smoke import.

When tier 3.5 finds nothing, it does NOT mean the implementation is
correct. The `[CHECKED]` entries are the audit trail: the
operator/parent can read which registries were inspected and what
each registered entry resolved to, and decide whether the surface is
sufficient. False negatives are inherent to the heuristic; false
positives are bounded by the classifier (only an in-project
__module__ that's not declared by this phase produces SHADOWING).
