---
type: S0 pre-flight verdict
date: 2026-04-20
campaign: r7.7 Path A
worker: S0 pre-flight
---
# S0 pre-flight

## 1. probe-preflight.sh verdict: FAIL (halted before invocation)

**Failing gate:** `OMLX_API_KEY` not present in the S0 worker's environment.

```
$ test -n "$OMLX_API_KEY" && echo present || echo "FAIL: OMLX_API_KEY not in env"
FAIL: OMLX_API_KEY not in env
```

Secondary check: `OMLX_API_KEY` is not defined in any of `~/.zshrc`, `~/.zshenv`, `~/.zprofile`, `~/.bashrc`, `~/.bash_profile`, `~/.profile`.

Per task instructions the S0 worker must not try to recover oMLX state itself — this is an operator-interaction gate (plan §5.2 + §13.6). The `probe-preflight.sh` script itself was not invoked (instruction step 1 aborts before `./probe-preflight.sh` when `OMLX_API_KEY` is missing).

Script sanity: `probe-preflight.sh` is present and executable; its header confirms it strictly requires `OMLX_API_KEY` to be forwarded for the oMLX gate.

## 2. Local-file md5 verdict: ALL MATCH

| File | md5 observed | §14 expected | verdict |
|------|--------------|--------------|---------|
| probe-preflight.sh | 65b88ec02c1a1b07c88dc195f765331f | 65b88ec02c1a1b07c88dc195f765331f | MATCH |
| CALIBRATION-r7.6-judge-protocol.md | 2ddd2eac5fa26b9f7a1465fb3046503d | 2ddd2eac5fa26b9f7a1465fb3046503d | MATCH |
| variants/hermes/delegate_worker_v2.py | d31876fe987331a26c8640202334fd46 | d31876fe987331a26c8640202334fd46 | MATCH |
| variants/hermes/HERMES-variantF.md | 24e8d1c0f7e1e0e95b26c38af974b8ce | 24e8d1c0f7e1e0e95b26c38af974b8ce | MATCH |
| variants/hermes/HERMES-WORKER.md | f866f52bbee28335964ec50d06bbac68 | f866f52bbee28335964ec50d06bbac68 | MATCH |
| probe-variantH-check.py | 873935f65e1bb91942dde1139dd57f92 | 873935f65e1bb91942dde1139dd57f92 | MATCH |
| probe-variantI-wrapper.sh | f1022e994a46838c180e4bf8da4171ee | f1022e994a46838c180e4bf8da4171ee | MATCH |
| probe-variantH-wrapper.sh | 64b75e00efc1056dcb1883a54e162033 | 64b75e00efc1056dcb1883a54e162033 | MATCH |

No drift. Note: `HERMES-variantF.md` appears in `git status` as modified, but its on-disk md5 matches the §14 post-Fix-4 baseline — git-status `M` is expected (drift from pre-release tag, not from plan baseline).

## 3. VM canonical verdict: PASS

| File | md5 observed | Expected | verdict |
|------|--------------|----------|---------|
| HERMES.md | 0780c232a6cb52e13e432261f0d68ad9 | 0780c232a6cb52e13e432261f0d68ad9 | MATCH |
| SKILL.md (jira-daily-briefing) | fb1a5a5208a6cf2fcb8252aac10397eb | fb1a5a5208a6cf2fcb8252aac10397eb | MATCH |
| jira-briefing.sh | a1dce6e989527686124d0860830627c9 | a1dce6e989527686124d0860830627c9 | MATCH |
| useDashboard.ts | 5503ee1c2ef7d635a020eea275e41239 | 5503ee1c2ef7d635a020eea275e41239 | MATCH |

`delegate_worker_v2.py` staged at `~/.hermes/hermes-agent/tools/`? **NO** — `ls` returned `No such file or directory`. VM is canonical / unstaged as expected.

SSH reachable; no VM unreachable condition.

## 4. Cron timing

- Current time (PT): 2026-04-20 10:32:10 -07:00 (Monday, CDT tz-abbrev from `date` but zoneinfo resolved to PDT/PT correctly in Python)
- Next weekday-08:00 PT cron window: 2026-04-21 08:00:00 -07:00 (Tuesday)
- Hours until: **21.46h**
- Blocking? **NO** — S0/S1/S2 are research-only; probes (S8) are not scheduled to start in the next 21h window per plan §8, and even a full S1+S2 pass finishes well inside the 21h budget. Informational only.

## 5. Artifact integrity

All 9 plan-review artifacts present and non-empty:

- ARTIFACT-r7.7-planreview-SYNTHESIS.md (15,946 B)
- ARTIFACT-r7.7-planreview-JUDGE.md (10,970 B)
- ARTIFACT-r7.7-planreview-EDIT-DIFF.md (13,038 B)
- ARTIFACT-r7.7-planreview-I1-campaign-arc.md (18,053 B)
- ARTIFACT-r7.7-planreview-I2-hermes-architecture.md (21,312 B)
- ARTIFACT-r7.7-planreview-I3-probe-infra.md (7,113 B)
- ARTIFACT-r7.7-planreview-I4-state-verification.md (17,454 B)
- ARTIFACT-r7.7-planreview-R1-cold-start.md (15,975 B)
- ARTIFACT-r7.7-planreview-R2-technical.md (20,106 B)

All present? **YES.**

## 6. Secret scan

Matches for `<raw-key>` across repo (excluding `.git`, `.claude`): **1 match**, in `ARTIFACT-r7.7-planreview-JUDGE.md:14`.

Context inspection:

```
| P0-1 | ACCEPT | `grep -rn '<raw-key>' ...` returned zero matches | Line 104 uses `<REDACTED>` placeholder correctly. |
```

This is a meta-reference: the judge artifact documents the scan command itself (the token appears in a backtick-quoted command string inside a markdown table cell describing a prior P0 check). It is not a payload leak and not embedded secret content. Nonetheless, flagging per step-6 "prominently" guidance — operator can choose to redact this token to `<REDACTED>` in the JUDGE artifact if strict zero-match invariant is required before dispatch.

No other matches. No `.env`-style leaks observed in this scan.

## Overall verdict

**NO-GO** — S1 and S2 cannot be dispatched until `probe-preflight.sh` returns `PREFLIGHT=PASS`. Blocked by `OMLX_API_KEY` absence in the orchestrating shell.

All non-oMLX gates pass cleanly: local md5s match plan §14, VM is canonical, no delegate staging on VM, plan-review artifacts complete, cron non-blocking, secret scan effectively clean (one meta-reference).

## If NO-GO: what operator must do

1. **Export `OMLX_API_KEY` into the orchestrating session's environment** so it is inherited by `probe-preflight.sh`. Per MEMORY.md: key is local-dev only and must not be committed. Suggested: source from a gitignored file under `~/.config/` or the operator's password manager, then run:
   ```
   export OMLX_API_KEY=<value>
   export AGENT_DISPATCH_AVAILABLE=1
   export OMLX_SWAP_MAX_GB=5.5
   ```
2. **Re-dispatch S0** (this worker) to re-run step 1 (`./probe-preflight.sh`). Steps 2-6 already verified and will re-verify in seconds.
3. **If step 1 then reports `PREFLIGHT=FAIL detail=omlx` with DEGRADED:** per MEMORY.md `project_omlx_degradation_contaminates_probes`, restart oMLX before long runs via Mac UI.
4. **Optional:** Redact the `<raw-key>` meta-reference in `ARTIFACT-r7.7-planreview-JUDGE.md:14` to `<REDACTED>` if the operator wants a literal-zero-match secret scan invariant.

## If GO: ready to dispatch S1 (A1 diag) + S2 (A2 hook research) in parallel

Not applicable — see NO-GO above. Once S0 re-runs green, all other preconditions are already verified green in this same artifact and S1/S2 can proceed immediately in parallel.

---

## S0 Retry (2026-04-20)

**Verdict: GO**

Preflight output:
```
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=47.1 (threshold >=20)
  swap_used_gb=3.0 (threshold <=5.5)
  omlx_active_sessions=0 (threshold <=1)
  omlx_loaded_count=0 (advisory)
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
```

Exit code: 0

Env source: `/tmp/r7.7-env.sh` sourced successfully; `OMLX_API_KEY` loaded (length-only check confirmed non-empty), `AGENT_DISPATCH_AVAILABLE=1`, `OMLX_SWAP_MAX_GB=5.5`. Full preflight log at `/tmp/r7.7-s0-retry-preflight.log`.

All four gates (agent_dispatch / omlx / tripwire / vm_idle) green. oMLX is CLEAN with free_mem_gb=47.1 (well above 20 threshold), swap_used_gb=3.0 (under 5.5 ceiling), and zero active sessions. First-run S0 already covered md5s, VM canonical state, cron timing, artifact integrity, and secret scan — no re-verification needed.

S1 + S2 ready to dispatch.
