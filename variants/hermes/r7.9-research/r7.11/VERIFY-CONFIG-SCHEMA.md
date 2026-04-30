# VERIFY-CONFIG-SCHEMA — verify-config.json (r7.11 item 5)

Operator-supplied configuration consumed by `verify_phase_tool.py` (item 5).
All fields are optional; an absent file means "use defaults". The wrapper
(`hermes-multi`, item 7) loads this once at run start; on a parse error or
schema-version mismatch, the wrapper fails-fast — defaults are NOT silently
substituted.

## Schema (version 1.0)

```json
{
  "schema_version": "1.0",
  "verify_phase": {
    "cat1_extra_allow_list": ["router", "app", "ws_app"],
    "presence_min_bytes": 50,
    "presence_min_nonblank_lines": 3,
    "runtime_smoke_test_timeout": 10,
    "runtime_smoke_test_default": false,
    "acceptance_timeout_seconds": 120
  }
}
```

## Top-level fields

| Field            | Type   | Required | Notes |
|------------------|--------|----------|-------|
| `schema_version` | string | yes      | Must be `"1.0"`. Any other value raises `ConfigError`. |
| `verify_phase`   | object | no       | Section consumed by `verify_phase_tool`. Defaults if absent. |

Unknown additional top-level fields are TOLERATED for forward-compat (the
wrapper and parent are independently versioned and may run skewed).

## `verify_phase` fields

| Field                          | Type    | Default | Effect |
|--------------------------------|---------|---------|--------|
| `cat1_extra_allow_list`        | string[]| `[]`    | Extra top-level symbol names exempt from CAT1 `[CAT1:defined-unused]`. Stacks on top of the built-in `_PUBLIC_API_ALLOW_LIST` (`router, app, application, api`). Use for framework-picked-up names (`ws_app`, `lambda_handler`, `celery_app`) that AST analysis cannot resolve as references. |
| `presence_min_bytes`           | integer | `50`    | Tier-1 minimum file-body size (bytes). |
| `presence_min_nonblank_lines`  | integer | `3`     | Tier-1 minimum non-blank line count. |
| `runtime_smoke_test_timeout`   | integer | `10`    | Tier-3.5 subprocess timeout (seconds). |
| `runtime_smoke_test_default`   | boolean | `false` | Default for tier-3.5 when the tool's `with_runtime_smoke_test` argument is `null`. Explicit `true`/`false` on the tool call overrides this. |
| `acceptance_timeout_seconds`   | integer | `120`   | Tier-3.7 (acceptance-runner) subprocess timeout, in seconds. Bounds the operator-declared `Acceptance Command:` from PLAN.md. A command that exceeds this surfaces an `[ENVIRONMENT:timeout-after-Ns]` finding (sets `passed=false`). Tier 3.7 default-on activation is governed by PLAN.md (the field's presence, not a config flag); this setting only tunes the timeout. |

Unknown additional keys inside `verify_phase` are tolerated (note logged
silently; not raised) — same forward-compat rationale.

## Error semantics

| Condition                                        | Behavior |
|--------------------------------------------------|----------|
| File absent (or `path is None`)                  | Return `VerifyConfig()` (all defaults). |
| File present but unreadable (`OSError`)          | `ConfigError` with file path. |
| File present but invalid JSON                    | `ConfigError` with file path + line/column from `json.JSONDecodeError`. |
| `schema_version` missing                         | `ConfigError` listing the expected version. |
| `schema_version` value other than `"1.0"`        | `ConfigError` with both observed and expected. |
| `verify_phase` not an object                     | `ConfigError`. |
| `cat1_extra_allow_list` not list-of-string       | `ConfigError`. |
| `presence_min_bytes` / `presence_min_nonblank_lines` / `runtime_smoke_test_timeout` / `acceptance_timeout_seconds` not int | `ConfigError`. |
| `runtime_smoke_test_default` not bool            | `ConfigError`. |

`ConfigError` is a `ValueError` subclass; the wrapper substrate (item 7)
expects to fail-fast on it.

## Choices documented (worker decisions on top of operator brief)

- **Bool-rejection for int fields**: Python treats `True`/`False` as ints,
  so `isinstance(True, int)` is `True`. We explicitly reject bool values
  for the integer fields to surface confused config-author intent.
- **Empty file is *not* the same as absent file**: an empty file has zero
  bytes and fails `json.loads`, raising `ConfigError`. Absent file returns
  defaults. This makes "I forgot to write a config" distinguishable from
  "I wrote a broken config".
- **`cat1_extra_allow_list` is purely additive**: the built-in
  `_PUBLIC_API_ALLOW_LIST` (`router`, `app`, `application`, `api`) is
  always honored. The config can extend, never reduce. This keeps a stray
  empty config from regressing existing protections.
- **No nested `tiers` section yet**: future tiers (4 semantic, 5+) get
  their own sub-objects when added; the schema_version bumps in lockstep.
  In v1.0, only `verify_phase` exists at the top level.

## `wrapper` section (item 7 — `hermes_multi.py`)

The `hermes-multi` wrapper substrate (item 7) reads the same
`verify-config.json` file as `verify_phase_tool` but consumes a SEPARATE
top-level key, `wrapper`. The two sections are independent: a config that
sets only `verify_phase` is valid for the verifier; a config that sets only
`wrapper` is valid for the wrapper; both can coexist. Defaults are applied
field-by-field (a missing field falls back to the default; a missing
`wrapper` section means "all wrapper defaults").

```json
{
  "schema_version": "1.0",
  "verify_phase": { ... },
  "wrapper": {
    "phase_max_wall_clock_seconds": 3600,
    "sentinel_grace_seconds": 30,
    "poll_interval_seconds": 1.0,
    "max_anomalous_exits": 3,
    "model": "gemma-4-26B-A4B-it-MLX-8bit",
    "max_turns_per_phase": 40,
    "remote_host": "ubuntu-vm"
  }
}
```

### `wrapper` fields

| Field                          | Type    | Default                              | Effect |
|--------------------------------|---------|--------------------------------------|--------|
| `phase_max_wall_clock_seconds` | integer | `3600`                               | Hard ceiling for a single Hermes session before the wrapper SIGTERMs. Any session exceeding this is recorded as `exit_reason=timeout` and counts as an anomalous exit. |
| `sentinel_grace_seconds`       | integer | `30`                                 | After a sentinel file appears, the wrapper waits this long for Hermes to exit naturally. If the process is still running at the deadline, the wrapper SIGTERMs (then SIGKILLs after 5s). |
| `poll_interval_seconds`        | number  | `1.0`                                | Sentinel polling cadence. Tests use `0.05` for fast execution; production should keep `1.0` to avoid hammering the transport. Accepts int or float; stored as float. |
| `max_anomalous_exits`          | integer | `3`                                  | Threshold for the wrapper-side anomalous-exit guardrail. When the count of `crash + timeout + anomalous_exit` outcomes EXCEEDS this value, the wrapper escalates with reason `repeated_anomalous_exits`. The count is wrapper-internal state only — it is NOT written to `verified-state.json`. |
| `model`                        | string  | `"gemma-4-26B-A4B-it-MLX-8bit"`      | The `--model` flag passed to `hermes chat`. |
| `max_turns_per_phase`          | integer | `40`                                 | The `--max-turns` flag passed to `hermes chat`. Applies per session (each phase). |
| `remote_host`                  | string  | `"ubuntu-vm"`                        | SSH host alias the wrapper drives Hermes against. Override per-invocation with `hermes-multi run --remote-host=<host> <scaffold>`. Tests bypass this entirely by injecting a `LocalFsTransport`. |

### Error semantics (wrapper section)

| Condition                                                                         | Behavior                                          |
|-----------------------------------------------------------------------------------|---------------------------------------------------|
| `wrapper` not an object                                                           | `ConfigError` (wrapper-side) → exit 4.            |
| Any of the integer fields not int (or `bool`)                                     | `ConfigError` → exit 4.                           |
| `model` / `remote_host` not string                                                | `ConfigError` → exit 4.                           |
| `poll_interval_seconds` not int/float                                             | `ConfigError` → exit 4.                           |
| Field absent                                                                      | Default applied silently.                         |
| Unknown extra keys inside `wrapper`                                               | Tolerated (forward-compat).                       |

### Relationship between `verify_phase` and `wrapper` sections

The two sections are **strictly disjoint** and consumed by **different
processes**:

- `verify_phase` is read by `verify_phase_tool.load_verify_config` inside
  the Hermes session (verifier shim → tool callable).
- `wrapper` is read by `hermes_multi.load_wrapper_config` on the operator's
  Mac at `hermes-multi run` startup.

A malformed `verify_phase` section raises `ConfigError` from the verifier
inside Hermes; a malformed `wrapper` section raises `ConfigError` from the
wrapper before any Hermes session is launched. Both share the same
top-level `schema_version` (currently `"1.0"`).
