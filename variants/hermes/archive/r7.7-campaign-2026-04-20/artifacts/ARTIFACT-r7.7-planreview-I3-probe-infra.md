---
type: plan-review artifact
author: worker I3 (probe-infra deep-read)
date: 2026-04-20
plan-under-review: PLAN-r7.7-path-A-child-structural-fixes.md
note: worker produced findings inline; captured here for synthesis.
---

# I3 — Probe infrastructure + calibration review

## 1. Staging-stack architecture (variantF → G → H → I → J)

Each stage adds orthogonal patches to distinct codepaths with non-colliding backup suffixes. No forward dependencies; ordering is operational convenience only.

| Stage | Purpose | Suffix |
|-------|---------|--------|
| variantF | β-fuse delegate_worker_v2 (r7.4) | `.probe-r7.4-orig` |
| variantG | turn-0 β-fuse toolset restriction (r7.5) | `.probe-r7.5-orig` |
| variantH | Gemma parser prefix-tolerance + channel-marker normalization (r7.6-P1A) | `.probe-r7.6-orig` |
| variantI | HERMES-WORKER.md overlay via delegate_tool.py patch (r7.6-P1C) | `.probe-r7.6-worker-orig` |
| **variantJ (proposed)** | A1 child toolset restriction + A2 write-before-claim gate | `.probe-r7.7-orig` |

VariantJ-stage.sh target edits:
- `variants/hermes/delegate_worker_v2.py` (Mac-side → deployed) for A1
- `~/.hermes/hermes-agent/run_agent.py` at ~L9109 for A2
- Optionally new/extended `probe-variantJ-check.py` for a2_gate_outcome inspection

**No namespace or stacking conflicts.** Idempotency checks per stage via markers.

## 2. variantI wrapper Fix 3 + Fix 4 load-bearing features (confirmed present)

- L31 `TIMEOUT_PER_TURN=1500` — raised from 900 for long overlay tasks ✓
- L121-137 `retry_preamble()` — defined + invoked ✓
- L261 anti-child-attachment via base64-encoded content-match of first 80 bytes ✓
- L189 `VIOLATION:EMPTY_SYNTHESIS` correction case ✓

If variantJ derives from variantI, all four inherit.

## 3. probe-preflight.sh gates (order)

1. `agent_dispatch` — checks `AGENT_DISPATCH_AVAILABLE=1`. **Non-bypassable; contract-based** (bash cannot introspect Claude session tools; caller declares truthfully).
2. `oMLX health` — delegates to probe-omlx-health-check.sh; honours `OMLX_SWAP_MAX_GB=5.5` override.
3. `tripwire` — single SSH round-trip; md5-compares 4 protected files. Overridable via `TRIPWIRE_*_MD5` env vars.
4. `vm_idle` — pgrep for `[h]ermes chat` on VM.

All gates non-bypassable; exit codes distinct (1/2/3 respectively).

## 4. oMLX health-check behaviour

Thresholds env-overridable (OMLX_MEM_FREE_MIN_GB, OMLX_SWAP_MAX_GB, OMLX_ACTIVE_SESSIONS_MAX, OMLX_URL, OMLX_API_KEY).

- Mem: `(pages_free + pages_inactive) * page_size` — standard macOS available metric; adapts automatically post-restart.
- Swap: sysctl `vm.swapusage` — live.
- Sessions: `/api/status` auth'd endpoint (when OMLX_API_KEY set); falls back gracefully to `"unknown"` when absent — advisory, does not degrade verdict.

Plan's §3 operator override to 5.5 GB swap is correctly honoured (preflight.sh L64 exports it).

## 5. Calibration protocol decision tree (CALIBRATION-r7.6-judge-protocol.md)

| Agreement (5-sample) | Verdict |
|---------------------|---------|
| 5/5 or 4/5 | PASS (annotate disagreement if 4/5) |
| 3/5 | EXPAND to 10-sample stratified → ≥8/10 PASS, 6-7/10 FAIL, ≤5/10 FAIL+diagnosis |
| ≤2/5 | FAIL; mandatory full re-judge pass |

**Implication for r7.7:** If orchestrator heuristic judge is unchanged from r7.6, prior calibration carries forward. **If judge logic changes (e.g., new a2_gate_outcome heuristic), re-calibration is mandatory.** Plan §9.5 doesn't explicitly state this — polish candidate.

## 6. Judge brief template (ARTIFACT-r7.5-F1-judge-brief.md)

Exists. 11 input variables confirmed:
TRIAL_N, TASK_ID, TASK_CLASS, PARENT_GOAL, PARENT_SESSION_ID, CHILD_SESSION_PATH, GOAL_PATHS, TRIPWIRE_BASELINE, TRIPWIRE_POST, PER_TRIAL_ARTIFACT_PATH, SSH_TARGET.

**a2_gate_outcome compatibility:** field is added to child session JSON by A2 gate; judges can inspect via `jq '.a2_gate_outcome' <child.json>` without template change. Judge brief doesn't need modification for r7.7; optional future extension to 12 vars if scoring becomes explicit.

## 7. run-arm.sh is ephemeral

Mentioned in MORNING-SUMMARY but not present on disk; not required for r7.7. Wrappers ARE the orchestration — each invocation self-contained. Fresh session reconstructs by invoking variantJ-wrapper N times.

## 8. Dual-endpoint support status (not in plan; operator-discussed, deferred)

~4-6h implementation:
- Env vars `OMLX_URL_PRIMARY` / `OMLX_URL_SECONDARY`
- Hermes invocation needs `--api-base-url` flag override (or equivalent); **CLI support unverified** — needs research worker before committing
- Orchestrator needs load-balance + failover logic

**Blocker:** unclear if Hermes CLI exposes a base-URL override without editing HERMES.md (tripwire'd). Deferred correctly.

## 9. Artifact naming convention (r7.7 proposed vs r7.6 actual)

r7.6 used `ARTIFACT-r7.6-judge-REJ-A-T10-run1.md`. Plan §9.5 proposes `ARTIFACT-r7.7-judge-ArmX-T<N>-run<M>.md`. Consistent, no collision.

## 10. §12 Gotchas — coverage by existing infrastructure

| Gotcha | Mitigation |
|--------|-----------|
| Tool-surface regression | ✓ preflight agent_dispatch gate |
| Secret in archive (oMLX dev key) | partial — redaction doc; grep-scan required pre-commit; **plan itself originally contained the secret** (flagged by I4, redacted 2026-04-20) |
| oMLX swap tight (5.5 GB) | ✓ health-check threshold + env override |
| Jira cron tripwires (SKILL.md T9 attractor) | ✓ preflight tripwire gate + skip T9 in r7.7 |
| `<channel\|>` pollution | ✓ variantH CHANGE 2 + check-script detector |
| Pseudo-tool-call parser leak | ✓ variantH CHANGE 1 (r7.6 Fix 2 also patches heuristic; fresh-LLM judge immune) |
| variantI Fix 3+4 preservation | ✓ stage-script idempotency |
| HERMES-variantF.md drift | docs-only — operator decision point §13.2 |
| New LOST mode (β-fuse bypass) | detected post-hoc via missing child path → LOST verdict |

Structural mitigation: 6/8. Documented-only: 2/8.

## 11. Critical observations

1. **A1 diag is load-bearing** — variantJ design cannot finalize until H-A1a/b/c resolved. Plan §8 correctly sequences S1 before S3.
2. **A2 hook-point fragility** — plan §7.2 cites line ~9109; S2 must re-verify against current VM Hermes state before S4 impl. Lines shift across Hermes versions.
3. **Backup-suffix idempotency** — `[[ -f X ]] || cp` pattern ensures backups aren't overwritten on re-stage. Unstage safe.
4. **Calibration-carry-forward assumption** — not explicit in plan; should be stated or re-verified at S0.

## 12. Polish candidates (for the main-session synthesis)

- Plan §9.5 should clarify: "prior r7.6 calibration carries forward unless orchestrator judge changes; re-calibrate if heuristic judge modified."
- Plan §14 references `run-arm.sh` in the Morning Summary — note it's ephemeral and not needed.
- Plan should explicitly note that judge brief template needs no r7.7 changes (just inspect a2_gate_outcome in session JSON).
- Plan §12 coverage table could help a fresh session see which gotchas are already mitigated vs need active attention.
