---
type: plan-review synthesis
date: 2026-04-20
plan-under-review: PLAN-r7.7-path-A-child-structural-fixes.md
input-artifacts: planreview-{I1,I2,I3,I4,R1,R2}.md
---

# PLAN-r7.7 review — synthesis & prioritized punch list

40 distinct findings across 6 workers, deduplicated and tiered by blast-radius.

**Headline:** plan's core mechanism (A1 + A2) is technically sound — A1 hypothesis H-A1c confirmed by code inspection (I2), A2 hook point verified at line 9109 (I2), infrastructure stack verified (I3), 9/9 repo md5s + 4/4 VM tripwires MATCH (I4). Issues are concentrated in (a) accuracy of framing, (b) A2 runtime details, (c) ship-gate math, (d) fresh-agent executability.

---

## Tier P0 — must fix BEFORE the plan is shared, committed, or handed off

### P0-1. Secret leak in plan itself (I4 §5)
Lines 104 and 562 originally contained the raw oMLX dev key in plain text (redacted 2026-04-20 immediately on detection). Plan violated its own §12 policy (`<REDACTED>` placeholder requirement). If the plan had been committed as-is, the key would have landed in git history permanently. Redaction keeps all four P0 items addressable; the cascade into review artifacts (I4/I3/R1/SYNTHESIS quoted the original text) was also cleaned 2026-04-20.

**Fix:** Redact line 104 to `Operator's dev key lives in OMLX_API_KEY env var (value <REDACTED>; local dev only).` Redact line 562 similarly.

### P0-2. "Main drifted post-tag" framing is factually wrong (I4 §7, R1 #7)
`git log r7.5-hermes-prerelease..HEAD` is EMPTY. HEAD commit == tag commit. What §3 calls "drift" is (a) one uncommitted working-tree edit to HERMES-variantF.md, and (b) 164 untracked files. Fresh agent will `git log tag..HEAD`, see nothing, and waste time hunting phantom commits.

**Fix:** Rewrite §3 first paragraph: "main working-tree has drifted post-tag (1 uncommitted edit to `variants/hermes/HERMES-variantF.md`, +1 line; 164 untracked artifacts from the r7.6 overnight). `git log r7.5-hermes-prerelease..HEAD` is empty — HEAD commit is the tag commit. The drift is uncommitted, not history."

### P0-3. §3 names wrong files for .probe-*-orig backup chains (I4 §4)
Plan says `delegate_worker.py`, `delegate_worker_v2.py` have the backup chains. Actual VM state: the chains belong to `model_tools.py`, `run_agent.py`, `toolsets.py`. `delegate_worker_v2.py` isn't even at `~/.hermes/hermes-agent/` top level in canonical state. Fresh agent following §10's "`.probe-r7.7-orig` coexists with `.probe-r7.6-orig`" will look for files that don't exist.

**Fix:** Rewrite §3 staging bullet: "Source patch chains on VM (each with `.probe-d-orig` through `.probe-r7.6-orig` backups): `model_tools.py`, `run_agent.py`, `toolsets.py`. `delegate_worker_v2.py` is staged INTO `tools/` when variantF is applied and removed when unstaged — no backup chain."

### P0-4. Wrappers H/I claimed to have drifted — they didn't (I4 §7)
§3 lists `probe-variantI-wrapper.sh` and `probe-variantH-wrapper.sh` as having Fix 3/Fix 4 patches post-tag. `git status` shows them unmodified. The patches were either committed IN the tag or never applied. Narrative "drifted" is misleading.

**Fix:** Remove the wrappers from the "drift" list in §3, or clarify that Fix 3+4 patches are already part of the pre-release commit (if that's true — worth verifying with diff-at-tag vs diff-at-HEAD).

---

## Tier P1 — must fix before fresh-session execution (blockers / correctness gates)

### P1-5. OMLX_API_KEY provenance undocumented (R1 #1)
§5 line 175: `export OMLX_API_KEY="$OMLX_API_KEY"`. No-op if operator's shell doesn't have it exported. Plan never says how to load it. Fresh autonomous session fails preflight silently.

**Fix:** Replace with explicit check: `test -n "$OMLX_API_KEY" || { echo "OMLX_API_KEY not set — confirm with operator before continuing"; exit 2; }`. Add §17 checklist item: "☐ Confirm operator has exported OMLX_API_KEY; do not proceed without it."

### P1-6. probe-preflight.sh existence not verified (R1 #2)
§5 references the script but it's untracked on disk (new in r7.6 Fix 5 per MORNING-SUMMARY). Fresh session can't prove it's present before running it.

**Fix:** Pre-flight line 0: `test -x probe-preflight.sh || { echo "preflight script missing — see ARTIFACT-r7.6-P1C-fix5-impl.md to reconstruct"; exit 2; }`.

### P1-7. ssh alias `ubuntu-vm` never declared (R1 #5)
§3 implies it once. All worker briefs (§6.3, §6.4, §7.6) rely on VM-path greps. Without the alias declared + verified, sub-agents break on VM reads.

**Fix:** Add §5.1 subsection: "All VM access uses `ssh ubuntu-vm --`. Alias is configured in `~/.ssh/config`. Verify with `ssh ubuntu-vm -- true` in preflight; halt if fails."

### P1-8. AGENT_DISPATCH_AVAILABLE=1 is defeat-the-guard (R1 #12)
§5 line 171 tells fresh agent to hand-set this to 1 unconditionally. But the whole point of Fix 5 was that this env var reflects REALITY (does current session have Agent tool), not user override. Setting it to 1 when it's 0 bypasses the preflight gate.

**Fix:** Replace hand-export with a verification step: "Verify current session can dispatch Agent via a trivial probe (spawn sub-agent that invokes Agent tool; if succeeds, preflight will pass). Do NOT hand-set the env var."

### P1-9. oMLX restart is manual UI step (R1 #4)
§5 line 189: "restart oMLX via Mac UI BEFORE any long probe." §10 authorizes autonomous execution. Fresh agent in autonomous mode cannot click Mac UI buttons.

**Fix:** Either (a) document the CLI restart recipe (e.g., `launchctl kickstart -k user/$UID/com.omlx.server` or equivalent — needs verification), or (b) add to §13 decision points as mandatory operator-interaction-required gate in autonomous mode.

### P1-10. A2 hook point anchored to volatile line number (R1 #6, R2 concurs)
§7.2 says "at `run_agent.py:~9109`". Upstream Hermes updates shift that. On next Hermes version, fresh agent patches wrong line.

**Fix:** Replace with grep anchor: "Locate with `grep -n 'def run_conversation' run_agent.py`, then find the first `_persist_session` call inside it. A2 gate fires immediately before that call."

### P1-11. A2 write-tool list has 2 ghost names + unverified skill_manage (R2 F14, I2 §4)
§7.4 frozenset includes `edit_file` and `apply_diff` which don't exist in toolsets.py. `skill_manage` inclusion is questionable — may be metadata-only, not file-write.

**Fix:** Trim to `{write_file, patch, execute_code, terminal, skill_manage}` with comment "verify skill_manage file-write semantics at S2; drop if metadata-only." Keep prefix matcher for forward-compat.

### P1-12. A2 SIGTERM safety — try/except can't catch signals (R2 F5)
§11 R4 mitigation says "try/except/finally". Python exception machinery doesn't catch SIGTERM. Per B.0 research, save is inline at 9109; A2 injection adds window where SIGTERM during gate leaves session state worse than without A2.

**Fix:** R4 mitigation must specify (a) `signal.signal(SIGTERM, ...)` handler that saves current messages before exit, (b) hard wall-clock cap on retries (60s per retry, 120s total exposure window).

### P1-13. A2 runtime regex precision uncalibrated (R2 F6)
§7.3 reuses F4A judge-time regex. Runtime-side firing is different context (partial turns, clarification loops, out-of-context summaries). I1 Mode 4 ("out-of-context investigation") generates prose the verb `written` may misfire on. No runtime-calibration shown.

**Fix:** Add to S6 as ship-blocking: feed gate 10 synthetic + 10 real r7.6 session JSONs (mix of FABRICATED, honest-blocked, normal PASS). Require ≥9/10 precision + ≥8/10 recall before S7 smoke.

### P1-14. A1 helper corner case — empty toolset risk (R2 F11)
§6.4 sketch: `_derive_restricted_child_toolset(parent_agent)` "reads the parent's enabled toolsets, removes todo." Per I2: delegate_tool.py has a three-way fallback (enabled_toolsets → valid_tool_names → DEFAULT_TOOLSETS). If parent's `enabled_toolsets is None`, naive helper returns `[]` → child has zero tools. 

**Fix:** Helper must mirror the fallback: `lambda parent: [t for t in _resolve_parent_toolsets(parent) if t != "todo"]` where `_resolve_parent_toolsets` is factored out of delegate_task's path. Add unit test: `enabled_toolsets=None` → default-minus-todo, not empty.

### P1-15. Missing R7 — substrate migration (R2 F4)
Plan §4 flags that A1 may push children from `todo` → `terminal`, worsening near-tripwire pressure. §11 Risks doesn't promote this.

**Fix:** Add R7: "Substrate migration — A1 may move fabrication energy from `todo` to `terminal`, increasing near-tripwire-breach attempts." Mitigation: pre-probe tripwire md5 baseline; mid-probe md5 check every 5 trials; halt on drift.

### P1-16. §1 TL;DR overstates A1 (R2 F13)
"A1 removes the substrate" — but §9.7 admits only partial lift. A1 removes ONE substrate; prose-only and pseudo-tool-call fabrication paths remain.

**Fix:** Rewrite §1 A1 bullet: "A1 removes the dominant `todo`-as-write substrate (per r7.6 T10 fabrication trials). Other fabrication routes (prose-only claim, pseudo-tool-call emission) are caught post-hoc by A2 but not structurally prevented."

### P1-17. Ship-gate arithmetic miscalibrated (R2 F1)
§9.7 says "centered around 13/20." Midpoint sum of stated priors (T4=4.5, T5=1.5, T6=3.5, T10=4.0) = 13.5. Under uniform independent priors, P(ship ≥15/20) ≈ 20-25% — not negligible.

**Fix:** Replace "centered around 13/20" with "centered around 13.5/20; P(SHIP) ≈ 20-25% under stated priors." This calibrates expectations and anchors the EV case for running at all (see P1-19).

### P1-18. RETREAT threshold lacks significance guard (R2 F3)
§9.6 RETREAT fires at "Arm F < r7.6 Arm B = <8/20." Arm B=8 has 95% CI ~[4,13] at n=20. A single 7/20 triggers RETREAT but is within noise.

**Fix:** RETREAT = Arm F ≤ 5/20 AND per-task regression on T4 (scaffold-known-good). Bands 6-8/20 = HOLD-with-note "indistinguishable at n=20."

### P1-19. Missing EV articulation under expected HOLD-CLOSE (R2 F18)
§9.7 honestly predicts ~13/20 (not SHIP). §15 treats ship decision as load-bearing. If the expected case isn't SHIP, why run 13h?

**Fix:** Add §18 or amend §9.7: "Why run this even if HOLD-CLOSE is expected:
- (1) Arm G ablation separates A1 lift from A2 lift — drives r7.8 scope.
- (2) Formal HOLD-CLOSE evidence is the justification for r7.8 deeper structural restriction.
- (3) `a2_gate_outcome` field is reusable infra for future campaigns.
- P(SHIP) ≈ 25%; running Path A buys 25% ship + 75% campaign-load-bearing negative. Positive-EV at 13h."

### P1-20. Timeline underestimates oMLX drag (R2 F16)
§16 says S8 Arm F = 4h. r7.5/r7.6 wall-clock shows 6-9h with oMLX restarts (MEMORY.md orphaned-session accumulation). §9.2 "12-15h" contradicts §16 "9-10h parallelized."

**Fix:** §16 S8 → 5-7h with restarts. Parallelized total → 11-14h without ablation, 14-17h with. Reconcile §9.2's "12-15h" framing.

### P1-21. Judge-rejection restart protocol missing (R1 #17)
§8 sequence matrix doesn't state what happens when S5/S6 REJECT. CLAUDE.md says "dispatch new worker" but plan doesn't specify per-step.

**Fix:** Add §8.5: "Judge rejection protocol: on S5 or S6 REJECT, main session reads judge findings, dispatches NEW worker with fresh context (do not reuse S3/S4 context). Max 2 iterations per fix. After 2 iterations, halt and escalate."

### P1-22. Modes 3/4/5 missing from §12 (R2 F8/F9/F10, I1 findings)
I1 identified three failure modes beyond fabrication + thrash: (3) pseudo-tool-call leak still occurs 3/20 post-Fix-2; (4) out-of-context wrong-cwd investigation; (5) SCOPE-resolution on ambiguous paths. §12 partially covers (3), doesn't name (4) or (5).

**Fix:** Update §12 pseudo-tool-call entry to "Fix 2 reduced but did not eliminate; 3/20 in r7.6 P1-C — if rate >2/20 in r7.7, dispatch F3A'." Add §12 entries for out-of-context child deployment and ambiguous-path SCOPE resolution.

### P1-23. `variantG` used without introduction (R1 #8)
§9.2 arm table references `variantG` staged; §14 mentions `probe-variantG-*` as pre-release frozen but never describes what it does. Fresh agent hunts.

**Fix:** Either drop variantG from §9.2 (if it's a typo/redundancy with F+H+I), or add §14 one-liner describing variantG's role.

---

## Tier P2 — polish / fix-forward acceptable (~18 items)

**Framing/clarity:**
- P2a. Role-separation ambiguity §8 S7/S8 "main session" vs "main session dispatches worker" — normalize (R1 #10).
- P2b. §9.5 main-dispatches-judges: explicitly state this IS role-separated, not a fallback (R1 #11).
- P2c. §6.4 A2 vs A1 symmetry — A1 edits Mac-side file, A2 edits VM file; make symmetric or state asymmetry explicitly (R1 #15).
- P2d. §17 autonomous-mode defaults for the 5 decision points (Arm F only, 15/20 firm, HOLD-CLOSE halt-with-summary) (R1 #24).
- P2e. §5 VM pre-stage order — add "at S0, verify variantF+variantI staged via stage scripts; halt if VM not pre-staged" (R1 #13).

**Preconditions:**
- P2f. §5 add Mac swap check (vm_stat before long probes) (R1 #16).
- P2g. §6.3 research worker: specify `ssh ubuntu-vm -- rg` or scp+local-grep (R1 #14).
- P2h. S0 sequential-vs-parallel reading (6 docs ~7-10min each = 45-60m) (R1 #20).

**Predictions that rot:**
- P2i. `/tmp/probe-r7.6-P1C-logs/judge-trial.py` md5 — mark ephemeral, recoverable from Fix 2 impl artifact (R1 #3, I4 §7).
- P2j. `md5` vs `md5sum` ambiguity — specify `md5 -q` on macOS (R1 #3).
- P2k. Arm B re-baseline "≤2 weeks stale" trigger clarification (R1 #19).
- P2l. Jira cron timing — `date +%u` check before long probes (R1 #23).
- P2m. §14 VM md5s "expected-if-idle" framing (R1 #25).

**Mechanism details:**
- P2n. Dead zone at 14/20 — nest ship ladder explicitly (R2 F2).
- P2o. A2 bare-path FN for T10 — add "path-is-ready" regex branch (R2 F15).
- P2p. A1 doesn't cover prose-only fabrication — doc note (R2 F12).
- P2q. Calibration-carry-forward explicit trigger (I3, R2 F7/F17).
- P2r. Untracked count 164 vs ~50+ framing (I4 §6) — set expectations for commit cleanup.

---

## What's NOT wrong (verified MATCH)

- All 9 repo-file md5s in §14 match exactly (I4 §1).
- All 4 VM tripwire md5s match (I4 §4).
- Hermes version v2026.4.8 / commit 86960cdb / Python 3.11.15 — all match (I4 §4).
- All plan-referenced artifacts exist on disk (I4 §2).
- Pre-release tag exists and is immutable (I4 §3).
- VM net-state IS canonical / unstaged as claimed (I4 §4).
- HERMES-variantF.md working-tree IS the post-Fix-4 value as claimed (I4 §3).
- A1 hypothesis H-A1c is correct (I2 §1); patch pattern to `delegate_worker_v2.py` is architecturally sound.
- A2 hook point at `run_agent.py:9109` is correct at this moment (I2 §3); risk is just that line shifts with Hermes upgrades.
- Probe infra stack (variantF→G→H→I) is sound; variantJ layering is conflict-free (I3 §1).
- variantI wrapper Fix 3+4 features all present and load-bearing (I3 §2).
- Preflight gate correctly non-bypassable on agent_dispatch (I3 §3).
- Judge brief template fits r7.7 without modification (I3 §6).
- Campaign arc table accurate; failure-mode framing verified (I1 §1-2).

---

## Recommended edit sequence

1. **P0-1 first.** Redact the secret. No other work proceeds until this is done — if context rotates and plan gets committed by accident, the secret leaks.
2. **P0-2 through P0-4** together — one edit pass on §3.
3. **P1-5 through P1-11** (pre-flight + A2 write-tool list) — one edit pass on §5 + §7.4.
4. **P1-12 through P1-14** (A2 SIGTERM/regex/A1 helper) — one edit pass on §7, §11, §6.4.
5. **P1-15 through P1-19** (risks, TL;DR, math, EV) — one edit pass on §1, §9, §11, new §18.
6. **P1-20 through P1-22** (timeline, restart protocol, modes) — one edit pass on §8, §12, §16.
7. **P1-23 + P2 bucket** — one sweep pass.

Total: 7 edit passes, est. 1.5-2h wall-clock to produce the polished plan.
