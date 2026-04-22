[TASK CLASS: structured]
Justification: Fresh-context judge verdict on Fix 5 deliverables (preflight script + calibration protocol + run-arm.sh wiring). Multi-artifact structural verification with live invocations.

# ARTIFACT — r7.6-P1C Fix 5 fresh-judge verdict

Timestamp: 2026-04-19
Judge scope (read-only on artifacts under review; live preflight invocation is non-mutating): `/Users/briantaylor/Projects/AgentFW/probe-preflight.sh`, `/Users/briantaylor/Projects/AgentFW/CALIBRATION-r7.6-judge-protocol.md`, `/tmp/probe-r7.6-P1C-logs/run-arm.sh` (+ pre-rev2-fix5 snapshot for diff), `PLAN-r7.6-P1C-fixes-implementation.md` §7 (spec-of-record), `ARTIFACT-r7.6-P1C-fix5-impl.md` (worker claims).

## Verdict: ACCEPT

All seven verification checks PASS. Fixes 2/3/4 are cleared to depend on this gate's correctness.

## Per-check evidence

### Check 1 — Agent-dispatch gate non-bypassable

- Only occurrence of `skip-agent` in `probe-preflight.sh` is a documentation comment (line 13) asserting its absence: `"There is NO --skip-agent flag."` No case arm in the argument parser for it (lines 96-107 handle only `--skip-omlx`, `--skip-tripwire`, `--skip-vm-idle`, `--help`/`-h`; anything else falls into the error arm and exits 5).
- Env-var contract is the sole path: gate block at lines 115-127 reads `"${AGENT_DISPATCH_AVAILABLE:-0}"` with default `"0"`, so absence of the var defaults to FAIL. The only pass condition is exact string `"1"`. Live test with `AGENT_DISPATCH_AVAILABLE=true` (not-literal-1) FAILs the gate (confirmed — see check 7).
- The gate fires BEFORE any `--skip-*` flag can take effect relative to it (--skip flags apply only to gates 2-4). The control-flow is literally unreachable to skip gate 1.

### Check 2 — Exit-code mapping per plan §7.2a

All six exit codes reachable and labeled:

| Code | Line(s) | Gate |  Matching stdout detail |
|------|---------|------|-------------------------|
| 0    | 239     | all pass | `PREFLIGHT=PASS` (line 238) |
| 1    | 126     | agent_dispatch | `PREFLIGHT=FAIL detail=agent_dispatch` (line 125) |
| 2    | 138, 149 | omlx | `PREFLIGHT=FAIL detail=omlx` (lines 137, 148) |
| 3    | 169, 208 | tripwire | `PREFLIGHT=FAIL detail=tripwire` (lines 168, 207) |
| 4    | 225, 232 | vm_idle / vm_busy | `PREFLIGHT=FAIL detail=vm_idle` (lines 224, 231) |
| 5    | 104     | usage error | (stderr usage block, no stdout verdict) |

Exit semantics in the header (lines 23-29) match the `usage()` print (lines 89-90) match the actual control flow. No ambiguity; no dead branches.

### Check 3 — Calibration protocol thresholds match operator pre-commit

Table at §3 lines 58-62 (5-sample):
- 5/5 → PASS
- 4/5 → PASS (with annotation)
- 3/5 → EXPAND to 10-sample
- ≤2/5 → FAIL ship-blocked

Table at §3 lines 67-70 (10-sample, reached via expand):
- ≥8/10 → PASS
- 6-7/10 → FAIL (mandatory full re-judge)
- ≤5/10 → FAIL (mandatory code-level diagnosis)

Matches the operator pre-commit verbatim (≥4/5 on 5-sample; ≥8/10 on 10-sample; ≤2/5 blocks ship). Escalation path is named at §5 (lines 112-132) with all three steps in the required order: (1) fix heuristic judge + re-sample, (2) expand to 10-sample, (3) full fresh-LLM re-judgment.

### Check 4 — Hard rule + ship-gate artifact calibration reference

- Hard rule: §6 line 137 states verbatim `"Orchestrator-in-process heuristic judging (Python regex + sub-criterion scorer) is a DOCUMENTED FALLBACK, not the primary path."` followed by enumeration of its allowed roles (§6 lines 138-144).
- Ship-gate artifact requirement: §7 lines 156-181 enumerate 8 required items; item 1 is explicit "Calibration reference — path to this protocol file AND to the calibration run's artifacts." Item 8 is "Pre-flight verdict snapshot." §7 line 180-181: "A ship-gate artifact missing ANY of items 1-4 and 8 does not satisfy this protocol and MUST NOT be used to gate a ship decision."
- Explicit "skip calibration only if documented" path: §6 lines 149-153 declare that if fresh-judge dispatch is unavailable (preflight gate 1 FAIL), the campaign is flagged uncalibrated and ship decisions are "explicitly forbidden." Structural enforcement through the preflight gate is called out explicitly.

### Check 5 — run-arm.sh wiring

Diff vs `/tmp/probe-r7.6-P1C-logs/run-arm.sh.pre-rev2-fix5` is a single additive block inserted at line 9-22 (before any ARM/MODEL/TOOLSETS export, before any `capture_tripwires` or `run_task_batch` call). The block:

1. Sets `PREFLIGHT_PATH` with a project-root default.
2. Checks for existence and executability — aborts with exit 1 and clear message if missing.
3. Invokes the preflight and aborts with exit 1 + clear message on nonzero.

Exactly one preflight invocation added. No other lines modified. Diff size +14 lines.

### Check 6 — Live preflight PASS path

Invocation: `AGENT_DISPATCH_AVAILABLE=1 OMLX_SWAP_MAX_GB=5.5 /Users/briantaylor/Projects/AgentFW/probe-preflight.sh`

```
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=97.0 (threshold >=20)
  swap_used_gb=4.8 (threshold <=5.5)
  omlx_active_sessions=unknown
  omlx_loaded_count=0 (advisory)
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
EXIT=0
```

Stdout final line is exactly `PREFLIGHT=PASS`. Exit code 0. Matches spec.

### Check 7 — Live preflight FAIL path (no AGENT_DISPATCH_AVAILABLE)

Invocation 1 — unset:
```
[GATE: agent_dispatch] FAIL: AGENT_DISPATCH_AVAILABLE is not '1' — invoking harness must declare Task/Agent tool availability. See plan §7.6: no --skip flag exists for this gate.
PREFLIGHT=FAIL detail=agent_dispatch
EXIT=1
```

Invocation 2 — `AGENT_DISPATCH_AVAILABLE=0`: identical output. Exit 1.

Invocation 3 — `AGENT_DISPATCH_AVAILABLE=true` (non-literal-"1"): identical FAIL. Confirms strict string-equality check. Exit 1.

Bonus — `--bogus-flag` argument: prints usage to stderr and exits 5. Confirms usage-error exit-code labeling.

All three variants correctly fail-closed. Stdout emits the exact `PREFLIGHT=FAIL detail=agent_dispatch` contract line. Exit code 1 consistently.

## Syntax + permissions

- `bash -n probe-preflight.sh` silent (exit 0).
- `bash -n run-arm.sh` silent (exit 0).
- `probe-preflight.sh` mode 0755.
- `run-arm.sh` mode 0755.

## Consistency check against impl notes

Worker artifact `ARTIFACT-r7.6-P1C-fix5-impl.md` claims independently reproduced:

| Claim | Re-verified? |
|-------|--------------|
| All 6 exit codes reachable | YES (lines 104/126/138,149/169,208/225,232/239) |
| `AGENT_DISPATCH_AVAILABLE=1` → PASS exit 0 | YES (live test, check 6) |
| Absence of var → FAIL detail=agent_dispatch exit 1 | YES (live test, check 7) |
| Bogus flag → usage error exit 5 | YES (live test, check 7 bonus) |
| Single preflight invocation added to run-arm.sh at top | YES (diff shows +14 lines, one `"$PREFLIGHT_PATH"` call) |
| No `--skip-agent` flag | YES (only comment mention at line 13) |
| Idiomatic pgrep self-exclusion via `[h]ermes chat` | YES (line 222) |
| Doc length 200 lines (vs plan's 80-150 target) | YES (file spans 201 lines) |

No inconsistencies detected between impl notes and actual artifact content. Impl worker's self-reported live-run transcript matches this judge's independently re-run transcript to within swap_used/free_mem drift (4.8 GB swap, 97.0 vs 97.2 free — environmental noise, not a discrepancy).

## Minor observations (non-blocking)

1. **Doc length deviation.** Shipped calibration protocol is 201 lines vs plan §7.2b's "~80-150 line" hint. Worker flagged this in impl notes with rationale (8 required sections + 11-variable substitution list + two escalation tables cannot fit in 150 lines without collapsing sub-clauses). Content is non-redundant; every section maps to a plan requirement. Acceptable.
2. **Env-var contract trust model.** The gate depends on the harness honestly declaring `AGENT_DISPATCH_AVAILABLE=1`. Worker correctly identified this as a trust-based contract and pointed to the compensating control: ship-gate artifact checklist §7 item 3 (per-trial fresh-verdict artifacts) — their existence is what actually proves Agent dispatch worked. Acceptable; flagged for ship-judge visibility.
3. **Tripwire `useDashboard.ts` depends on Parallels share mount.** Impl notes flag this fail-close behavior on mount loss. Correct per plan §2.3. Non-blocking; documented.
4. **`vm_idle` pattern specificity.** Hard-coded `"[h]ermes chat"` matches only `hermes chat`-style invocations. If a future probe introduces `hermes batch` or similar, the gate won't catch it. Plan §7.2a explicitly named only `hermes chat`, so this matches spec. Worth revisiting if the entrypoint changes.

None of these block acceptance.

## Recommendation

**ACCEPT.** Fixes 2/3/4 may now depend on this gate's correctness. Specifically:

- Fix 2 (heuristic judge expanded detectors) — its judge dispatch gate is now structurally protected by the preflight.
- Fix 3 (wrapper timeout + backport) — its judge verification likewise depends on Agent dispatch; preflight now guards it.
- Fix 4 (diag + impl) — judge dispatch precondition met.

The calibration protocol is referenced from the preflight FAIL-path comment (`see CALIBRATION-r7.6-judge-protocol.md`) and the doc itself references the preflight as structural enforcement (§6 lines 149-153). The two artifacts are mutually-referential and coherent as a single control-pair.

Green light.
