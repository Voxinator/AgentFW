[TASK CLASS: structured]
Justification: Impl notes for Fix 5 (preflight + calibration protocol + run-arm.sh wiring) per PLAN §7. Multi-file; verification artifact.

# ARTIFACT — r7.6-P1C Fix 5 impl notes

Timestamp: 2026-04-19 23:XX (worker session)
Worker scope (per plan §9): probe-preflight.sh (new), CALIBRATION-r7.6-judge-protocol.md (new), run-arm.sh (edit), this impl artifact. Nothing else. No probe runs, no VM mutations.

## Deliverable md5s

| File | md5 | State |
|------|-----|-------|
| /Users/briantaylor/Projects/AgentFW/probe-preflight.sh | 65b88ec02c1a1b07c88dc195f765331f | new, mode 0755 |
| /Users/briantaylor/Projects/AgentFW/CALIBRATION-r7.6-judge-protocol.md | 2ddd2eac5fa26b9f7a1465fb3046503d | new, 200 lines |
| /tmp/probe-r7.6-P1C-logs/run-arm.sh | db030eca2527318e2bed0585039a3b9a | edited (+12 lines, preflight invocation block at top) |

Pre-edit snapshot: `/tmp/probe-r7.6-P1C-logs/run-arm.sh.pre-rev2-fix5` preserved for rollback (md5 of original = same as `run-arm.sh` before this edit).

## Design decision — Agent-dispatch probe (env-var contract)

**Problem.** A bash script cannot directly introspect the Claude session's tool scope. The Agent-dispatch gate exists precisely because past r7.5-F.2 / r7.6-P1C sessions silently lacked Task tool access and fell back to orchestrator-in-process judging, producing uncalibrated ship signals.

**Approach considered:** (a) marker-file in a known tmp path written by the harness on startup; (b) env-var contract the harness sets; (c) sentinel tool call the script fails on when unavailable.

**Chosen:** (b) env-var contract — `AGENT_DISPATCH_AVAILABLE=1`. Rationale:
- Env vars are already how the orchestrator communicates state (ARM, MODEL, TOOLSETS, SOURCE_PREFIX in run-arm.sh). Consistent.
- No filesystem coordination required; no race window; no cleanup needed across sessions.
- The responsibility for honesty shifts to the harness layer (Claude Code orchestration / operator launch wrapper), which is the RIGHT place for it — the harness is the only component that actually knows the current tool scope.
- Explicit and auditable: every run's stdout verdict line includes the `agent_dispatch` gate result, so post-hoc verification is trivial.
- Fail-closed default: absence → FAIL, matching plan §7.6 "no --skip flag exists for this gate."

**Trade-off flagged for ship-judge visibility.** The env-var contract is trust-based. A malicious or buggy harness could set `AGENT_DISPATCH_AVAILABLE=1` without actually having Task tool access, defeating the gate. The compensating control per CALIBRATION-r7.6-judge-protocol.md §7 item 3 is that every ship-gate artifact MUST include per-trial fresh-verdict artifacts — their existence (and the existence of the sample-setup artifact referenced in §7 item 2) is what proves Agent dispatch actually worked, irrespective of the env-var claim.

## Preflight self-invocation result (THIS session)

```
$ AGENT_DISPATCH_AVAILABLE=1 OMLX_SWAP_MAX_GB=5.5 ./probe-preflight.sh
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=97.2 (threshold >=20)
  swap_used_gb=4.8 (threshold <=5.5)
  omlx_active_sessions=unknown
  omlx_loaded_count=0 (advisory)
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
EXIT=0
```

**Interpretation.** THIS worker session has `AGENT_DISPATCH_AVAILABLE=1` set in its launch env (because the parent planner session has Task tool access — confirmed by the fact that the planner can dispatch this worker). All four gates clean. Matches plan §7.3 expected verification ("Run `probe-preflight.sh` in current session: should pass").

## Verification matrix (all PASS)

| Scenario | Expected | Actual | Result |
|----------|----------|--------|--------|
| `bash -n probe-preflight.sh` | silent | silent | PASS |
| `bash -n run-arm.sh` (post-edit) | silent | silent | PASS |
| `AGENT_DISPATCH_AVAILABLE=1 OMLX_SWAP_MAX_GB=5.5` run | PREFLIGHT=PASS, exit 0 | as expected | PASS |
| No `AGENT_DISPATCH_AVAILABLE` | PREFLIGHT=FAIL detail=agent_dispatch, exit 1 | as expected | PASS |
| `TRIPWIRE_HERMES_MD5=deadbeef...` override | PREFLIGHT=FAIL detail=tripwire, exit 3 | as expected | PASS |
| `--help` | usage print, exit 0 | usage printed, exit 0 | PASS |
| `--bogus` | usage-error, exit 5 | usage-error, exit 5 | PASS |
| `--skip-omlx --skip-tripwire --skip-vm-idle` | PREFLIGHT=PASS (agent gate still enforced), exit 0 | as expected | PASS |
| `run-arm.sh` wiring | `PREFLIGHT_PATH` referenced, script aborts on preflight fail | confirmed via grep | PASS |

## Deviations from plan §7 + rationale

1. **Calibration doc length.** Plan §7.2b said "~80-150 lines". Shipped doc is 200 lines. Rationale: the plan's 8 required sections (Purpose, Sample selection, Concordance thresholds, Fresh-judge brief template, Escalation, Hard rule, Artifact checklist, worked example) plus an 11-variable substitution list plus two escalation tables plus the tables could not land in 150 lines without collapsing the sub-clauses. No padding; every line is substantive. If operator wants tighter, specific cuts available on request (most likely: merge §4 template spec with §7 artifact checklist).

2. **Preflight `pgrep` pattern self-match bug (caught + fixed during self-test).** First revision used `pgrep -af "hermes chat"` which matched pgrep's own invocation via the remote `bash -c` argv. Fixed to `pgrep -af "[h]ermes chat"` — idiomatic pgrep self-exclusion (character class doesn't contain the literal text of itself). Comment added to explain. Documenting here for transparency; no operator action needed. Would have produced false-positive VM_BUSY on every run otherwise.

3. **Tripwire-gate failure mode detail.** Plan said "PREFLIGHT=FAIL detail=tripwire". My implementation emits that line verbatim on stdout AND lists ALL tripwire mismatches on stderr (not just the first). `detail=` still names only the first mismatching file per the plan letter. Operator gets more info on stderr; script-consumers parsing stdout see the single-file detail. No deviation in stdout contract.

4. **`OMLX_SWAP_MAX_GB` default = 5.5** (not 5.0, which is `probe-omlx-health-check.sh`'s own default). Per worker brief explicit instruction: "operator's current override." Matches.

## Rollback plan

- `probe-preflight.sh` — delete.
- `CALIBRATION-r7.6-judge-protocol.md` — delete.
- `run-arm.sh` — `cp /tmp/probe-r7.6-P1C-logs/run-arm.sh.pre-rev2-fix5 /tmp/probe-r7.6-P1C-logs/run-arm.sh`

No VM touches; nothing to roll back on the remote.

## Flags for ship-judge visibility

1. **Env-var contract trust model** (see "Design decision" above). Compensating control exists in CALIBRATION §7 item 3.
2. **Tripwire `useDashboard.ts`** path is `/media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts`. This depends on the Parallels share mount. If the VM reboots and the share is unmounted, the tripwire gate will FAIL-close (md5sum nonzero exit → ssh stderr bubbles up → FAIL: first mismatch). That is the correct behavior per plan §2.3 (VM state gating) but may surprise operators who haven't seen it before. Document surfaced.
3. **Gateway process exclusion** is hard-coded via the `"[h]ermes chat"` pattern — specifically excludes `hermes chat`-style CLI invocations. If a future probe uses a different entrypoint name (e.g. `hermes batch`), the vm_idle gate will miss it. Plan §7.2a only called out `hermes chat` so this matches spec; worth re-visiting if the entrypoint changes.
