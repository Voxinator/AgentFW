# HOWTO — `hermes-multi` (r7.11 wrapper substrate)

Operator runbook for the multi-session Hermes wrapper. Distinct from
`HOWTO-r7.11-stage.md` (Hermes-side shim staging); this one covers the
multi-session orchestration loop.

The wrapper is intentionally dumb: it does not modify Hermes, the VM
canonical, or `verified-state.json`. It launches Hermes per phase, polls for
sentinel files, snapshots session state, and routes via `verified-state.json`
(the machine-authoritative source of truth, written ONLY by `verify_phase`).

## Prerequisites

1. Scaffold dir with `PLAN.md` (`## Phase N: <title>` / `Paths:` blocks) and
   `verify-config.json` (sections `verify_phase` + `wrapper`; see
   `VERIFY-CONFIG-SCHEMA.md`).
2. Remote host (default `ubuntu-vm`) with Hermes + r7.11 shims staged via
   `probe-r7.11-stage.sh`.
3. oMLX auth: by default the wrapper inherits whatever's in env and Hermes falls through to `~/.hermes/config.yaml` (`api_key:` field). Set `OMLX_API_KEY` env var only to override.

## Subcommands

```
hermes-multi run    <scaffold_root> [--fresh] [--remote-host=HOST]
hermes-multi resume <scaffold_root>             [--remote-host=HOST]
hermes-multi status <scaffold_root>
```

- **`run`** drives the state machine through every phase. Bootstraps
  `verified-state.json` from `PLAN.md` if absent (or always, with
  `--fresh`). Per phase: launches `hermes chat`, polls
  `<scaffold>/.session-end-signal.json` and `.session-escalate-signal.json`,
  snapshots the session JSON before each `--resume` (Addendum A3), reads
  `verified-state.json` to decide ADVANCE / REVISE / ESCALATE / COMPLETE, and
  appends a `manifest.json` entry to `<scaffold>/.session-archive/`.
- **`resume`** picks up after an `escalate`-pause: clears any stale escalate
  sentinel and re-evaluates the decision tree from current state.
- **`status`** read-only diagnostic: prints scaffold path, per-phase digest of
  `verified-state.json`, sentinel presence, and the last manifest entry.

## Exit codes

| Code | Meaning                            | Operator action                                        |
|------|------------------------------------|--------------------------------------------------------|
| `0`  | All phases verified_passed         | Done. Inspect scaffold contents.                       |
| `2`  | Escalate-pause                     | Read `manifest.json` last entry; remediate; `resume`.  |
| `3`  | Wrapper-internal error             | Read stderr + `wrapper.log`; fix root cause; rerun.    |
| `4`  | `verify-config.json` malformed     | Fix JSON; rerun.                                       |
| `5`  | Canonical drift (RESERVED)         | n/a in this build.                                     |
| `130`| SIGINT (Ctrl-C)                    | State preserved; rerun or `resume`.                    |

## Two-pane operator workflow

```
PANE 1 — driver
  $ hermes-multi run /path/to/scaffold

PANE 2 — observability
  $ tail -f /path/to/scaffold/.session-archive/wrapper.log
  $ watch -n2 'jq .phase_state /path/to/scaffold/verified-state.json'
```

`wrapper.log` lines: `<ISO_TS> <STATE> <DETAIL>` (LAUNCHING, RUNNING,
SENTINEL_DETECTED, ARCHIVING, DECIDING, COMPLETE/ESCALATING/WRAPPER_ERROR).

## Reading `manifest.json`

One entry per session attempt. Key fields:

- `phase_id`, `attempt` — identifies the session.
- `exit_reason` — `end | escalate | timeout | crash | anomalous_exit`.
- `sentinel_kind` — `end-signal | escalate-signal | both | null`.
- `wrapper_decision` — what the wrapper did next: `advance | revise |
  escalate | success | wrapper_error`.
- `verify_state_snapshot` — short digest of all phase statuses at archive time.
- `prior_phase_id` — populated on revise attempts (phase being revised).

The manifest is append-only and atomically written (temp-file + `os.replace`).

## Recovering from each terminal state

**Exit 2 (escalate):**

1. Read the last `manifest.json` entry → check the wrapper-side reason.
2. If `parent_called_escalate`: read `.session-escalate-signal.json` for the
   parent's message + `suggested_action`.
3. If `repeated_anomalous_exits`: parent kept exiting without calling either
   handoff tool — investigate `phase-*-attempt-*.stderr.log`.
4. If `max revisions exceeded`: look at `corrective_dispatch` in the most
   recent verify_phase verdict in `verified-state.json`.
5. Remediate (edit PLAN.md / fix scaffold / etc.) and `hermes-multi resume`.

**Exit 3 (wrapper_error):** almost always file IO, ssh, or `PLAN.md` parse
failure. Read stderr; fix; rerun.

**Exit 4 (config_error):** `verify-config.json` failed strict-schema
validation. Fix per `VERIFY-CONFIG-SCHEMA.md` and rerun.

## Read-only invariant on `verified-state.json`

The wrapper writes `verified-state.json` ONLY at bootstrap (no existing file,
or `--fresh`). After that, all writes go through `verify_phase` inside the
Hermes session. Search the wrapper source for
`_VS_WRITE_FORBIDDEN_INVARIANT` for the in-code assertion.

This is the structural defense against parent fabrication (§6 F2): the parent
cannot deceive the wrapper via narrative because the wrapper does not consult
narrative — only the verifier-written file.

## Troubleshooting

- **`anomalous_exit` every attempt**: parent finishes its turn budget without
  calling `end_session_for_handoff` or `escalate_to_operator`. Suspect the
  shim or the parent's tool prompt.
- **`crash` every attempt**: ssh, oMLX auth, or Hermes invocation issue.
  Check `phase-*-attempt-*.stderr.log`.
- **Sentinel detected but no advance**: check `verified-state.json` — if
  `verify_phase` did not run, no verdict was recorded and the next decision
  matches the last. Either the parent skipped `verify_phase` or the verify
  shim crashed (per-attempt stderr).

## Bootstrap mode

When `<scaffold_root>/PLAN.md` is absent at the start of `hermes-multi run`,
the wrapper drives a **bootstrap session** before entering the phase loop.
This closes the design-doc §2 lifecycle: the BOOTSTRAP SESSION block at the
top of the diagram is the parent's first job — classify the task, write
`PLAN.md`, then call `end_session_for_handoff`.

### When bootstrap fires

| Files at run-start            | Wrapper behavior                          |
|-------------------------------|-------------------------------------------|
| PLAN.md present               | skip bootstrap; existing flow             |
| PLAN.md absent + USER-PROMPT.md present | run bootstrap session, then phase loop |
| PLAN.md absent + USER-PROMPT.md absent  | exit 4 (config error); no Hermes launch |

### USER-PROMPT.md format

A plain-text Markdown file at `<scaffold_root>/USER-PROMPT.md` containing
the operator's task description. The wrapper reads it verbatim and prepends
a short orientation header instructing the parent to write PLAN.md and
call `end_session_for_handoff` (no `delegate_worker` calls in the bootstrap
session — phase work begins post-bootstrap).

### Bootstrap manifest entry

Distinguishable from phase entries by:

- `phase_id`: `null` (bootstrap is not a phase)
- `session_kind`: `"bootstrap"`
- archive filename: `bootstrap-attempt-<M>-<exit_reason>.json` (vs. phase
  pattern `phase-<N>-attempt-<M>-<exit_reason>.json`)
- `verify_state_snapshot`: `"pre-bootstrap (no verified-state.json)"`
  (the wrapper does NOT seed `verified-state.json` until *after* a
  parseable PLAN.md exists; see read-only invariant below).

### Anomalous-exit policy: FAIL-FAST

Bootstrap runs as a **single attempt**. If the bootstrap session crashes,
times out, or exits cleanly without a sentinel, the wrapper escalates
immediately with reason `bootstrap_failed_anomalous_exit`. Justification:
bootstrap loops aren't useful — if the parent can't author PLAN.md once,
retrying without operator intervention is unlikely to help.

### Recovering from `bootstrap_failed_*` escalates

| Reason                                | Diagnose / remediate                                                                                                                |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| `bootstrap_failed_no_plan`            | Parent emitted end-sentinel but never wrote PLAN.md (fabrication shape). Inspect `bootstrap-attempt-1.stdout.log`; check the `write_plan_md` shim is registered; consider clarifying USER-PROMPT.md. |
| `bootstrap_failed_unparseable_plan`   | PLAN.md exists but `parse_plan_md` rejected it (no `## Phase N:` headers, malformed Paths line, etc.). Open the written PLAN.md; either hand-fix it (then `hermes-multi run` again — the existing PLAN.md skips bootstrap) or delete it and rerun. |
| `bootstrap_failed_anomalous_exit`     | Hermes crashed / timed out / exited turn-budget without sentinel. Investigate `bootstrap-attempt-1.stderr.log`; usual suspects: ssh, oMLX auth, parent ran out of turns. |
| `parent_called_escalate_during_bootstrap` | Parent explicitly escalated during bootstrap (read `.session-escalate-signal.json` for `message` + `suggested_action`). Address operator concern, then `hermes-multi run`. |

After remediation: rerun `hermes-multi run <scaffold>`. If you fixed PLAN.md
in place, the wrapper sees it and skips bootstrap; if you only fixed
USER-PROMPT.md, the wrapper attempts bootstrap again from scratch.

### Read-only invariant on `verified-state.json` (bootstrap-aware)

Bootstrap does NOT write `verified-state.json`. The single permitted write
site remains `_bootstrap_state_if_needed`, which fires *after* the bootstrap
session has produced a parseable PLAN.md. Sequence on the bootstrap path:

1. Wrapper sees PLAN.md absent → runs bootstrap session.
2. Bootstrap session writes PLAN.md (parent tool), exits via end-sentinel.
3. Wrapper verifies PLAN.md exists + parseable. If not → escalate (no
   verified-state.json written; scaffold is in the same state as before
   the run, plus a manifest entry).
4. Wrapper calls `_bootstrap_state_if_needed` → seeds verified-state.json
   from PLAN.md (this is the existing, pre-bootstrap-extension write site).
5. Wrapper enters phase loop; from here on, only `verify_phase` writes
   `verified-state.json`.

## Mac-side vs VM-side execution (`--transport`)

`hermes-multi` ships with two production transports. Pick one with the
`--transport {ssh,local}` flag, available on both `run` and `resume`.

| Mode    | Wrapper runs on | Hermes runs on | Scaffold lives on | When to use                                                       |
|---------|-----------------|----------------|-------------------|-------------------------------------------------------------------|
| `ssh`   | Mac             | VM             | path string visible at the *same* path on both machines | Default; backward-compatible. Works only if both hosts agree on the scaffold path. |
| `local` | VM              | VM             | VM                | Operator ssh's into the VM and runs the wrapper there. No ssh-to-self overhead and no path mismatch. |

### Why `local`

The Parallels mount layout means a scaffold at `/tmp/r7.11-item8-scaffold/`
on the VM is not visible at the same path on the Mac. Driving such a
scaffold via `--transport ssh` from the Mac causes the wrapper's
heredoc/scp file ops to read/write the wrong filesystem. The fix is to
co-locate wrapper, Hermes, and scaffold on the VM:

```
operator@mac $ ssh ubuntu-vm
operator@vm  $ cd /path/to/r7.11/checkout
operator@vm  $ python3 hermes_multi.py run --transport local /tmp/r7.11-item8-scaffold
```

`LocalProcessTransport` defaults to:

- Hermes binary: `~/.hermes/hermes-agent/venv/bin/hermes`
- Hermes cwd:    `~/.hermes/hermes-agent`

Both can be overridden by constructing `LocalProcessTransport(hermes_path=…, hermes_cwd=…)`
programmatically (used by tests). The CLI does not currently expose
overrides; the standard staging layout is assumed.

### Mutual exclusion

`--transport local` is incompatible with `--remote-host`. Passing both
fails fast:

```
$ hermes-multi run --transport local --remote-host ubuntu-vm /tmp/scaffold
hermes-multi: error: --transport local is incompatible with --remote-host
$ echo $?
4
```

(exit 4 = config error). The `status` subcommand is read-only on the
local filesystem and does not accept `--transport`.

### Backward compatibility

`--transport` defaults to `ssh`, so existing operator scripts and the
prior smoke harness continue to work unchanged. `wrapper.remote_host` in
`verify-config.json` is still honored on the ssh path.

## Pointers

- Design: `DESIGN-r7.11-architecture.md` §2 (BOOTSTRAP SESSION), §5, §SC-1..SC-11
- Schema: `VERIFY-CONFIG-SCHEMA.md` (`wrapper` section)
- Sentinels: `SENTINEL-SCHEMAS.md`
- Tests: `test_hermes_multi.py` (25 tests; `python3 test_hermes_multi.py`)
- Hermes-side staging: `HOWTO-r7.11-stage.md`, `probe-r7.11-stage.sh`
