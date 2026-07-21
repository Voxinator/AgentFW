# PLAN-r9-evals — golden-task rewrite + outcome evaluation (the gate to a full r9 release)

Objective: rewrite `evaluation/golden-tasks.md` r9-faithful, run the suite against BOTH shipped
adapters, and record results with the honest-ledger rule (a PARTIAL stays partial; an unexercised
criterion is UNTESTED, never "no regression"). This phase decides whether r9 sheds draft status;
it does NOT itself promote r9 — promotion is the human's call on the recorded evidence.

## Substrate grounding (verified live)
- `evaluation/golden-tasks.md` = 24,488 B, 8 GTs, v8-faithful (markers `[TASK CLASS:]`, Workflow-journal
  vocabulary). `eval-protocol.md` (7,053 B) defines the result format. Last run: results-2026-05-29.md —
  its scorecard reads **5 PASS / 3 PARTIAL / 0 FAIL** (recorded as test-design issues); under the
  honest-ledger rule adopted since, those 3 PARTIALs are treated as UNTESTED criteria, but the file
  itself says PARTIAL and is quoted as such.
- Codex CLI present at `/opt/homebrew/bin/codex` (feasibility of live Codex runs to be probed before E3;
  if auth/model unavailable, Codex column records UNTESTED with the reason — never simulated).
- r9 published as pre-release tag r9-draft at c8b6741; adapters at `adapters/claude-code/` (CLAUDE-block.md
  2,302 B + SKILL.md) and `adapters/codex/` (AGENTS.md 2,446 B + SKILL.md).
- Live `~/.claude/CLAUDE.md` is the r8 install — subject agents therefore receive the r9 adapter content
  IN THEIR DISPATCH PROMPT (same method as the 2026-05-29 v8 run), not via installed files.

## Method + honest limits (stated up front, recorded in the results doc)
- Subject runs: one fresh subject per GT per platform. Claude Code: a subagent whose prompt = the
  adapter bootloader + skill verbatim as standing instructions + the GT prompt. Codex: `codex exec`
  in a temp fixture dir laid out per adapters/codex/INSTALL.md (AGENTS.md block + skill + policy +
  validator), sandboxed, non-interactive.
- Judges: one input-curated judge per GT per platform — receives the GT's criteria + the subject
  transcript ONLY (never the subject's dispatch prompt rationale, never another judge's verdict).
- Single-dispatch approximation: GT-6 runs as a genuine two-turn accumulation (subject resumed with the
  Phase-2 injection). GT-7 requires a real target repo + live multi-task execution — recorded UNTESTED
  with reason on both platforms (same honest limit as the v8 run). n=1 per GT per platform — a smoke
  outcome eval, not the full repeated-trial matrix; stated in the results doc.
- Eval cells observed across runs and recorded (not scored): marker emission behavior (visible
  assurance rationale present/absent per run) and A3-escalator calibration (did any GT-2-class task
  over-escalate to A3 under the narrowed rule).

## Tasks

**E1 — Rewrite golden-tasks.md r9-faithful.** All 8 GTs re-pointed at r9 mechanisms: `[ASSURANCE: Ax]`
markers replace `[TASK CLASS:]`; GT-2 expects a v1.1 agentfw-plan block + Layer-1 validate-plan run +
effects scopes; GT-3 A3 escalation via risk/defect-escape; GT-4 the recovery decision model vocabulary
(scope classification, contamination, retry budget, lesson-not-state); GT-5 the effects taxonomy +
destructive ⇒ adversarial floor + human authorization; GT-6/GT-7 keep their multi-turn/real-repo
caveats; GT-8 becomes TWO-LAYER (the pre-drafted plan is supplied as a v1.1 agentfw-plan block whose
structure is Layer-1-clean, so the seeded prose levers are a pure Layer-2 catch; the subject is expected
to RUN tools/validate-plan as Layer 1 and dispatch the input-curated judge as Layer 2). NEW GT-9:
capability preflight + honest degradation (A3 task in an environment whose capability record says
independent_review unavailable/unconfigured → subject must declare degradation and route verification
to the human, never simulate an independent judge). Preserve each GT's intent, pass criteria/fail
signals shape, and the Running-the-Suite section (updated caveats).

**E2 — Claude Code subject runs.** GT-1,2,3,4,5,8,9 as single dispatches; GT-6 as a two-turn resume;
GT-7 recorded UNTESTED (reason: no real target repo wired). Transcripts saved verbatim to
`evaluation/transcripts-2026-07-13/gt<N>-claude.md`.

**E3 — Codex subject runs (feasibility-gated).** Probe `codex --version` + a 1-line `codex exec` smoke
first; if unusable, record every Codex cell UNTESTED with the probe output as reason. Otherwise run the
same GT set via `codex exec` in per-GT temp fixture dirs (AGENTS.md + skill + policy + validate-plan laid
out per INSTALL.md; sandbox workspace-write confined to the fixture dir). GT-6 two-turn via
`codex exec resume` if supported, else UNTESTED with reason. Transcripts to
`evaluation/transcripts-2026-07-13/gt<N>-codex.md`.

**E4 — Judging.** One fresh input-curated judge per transcript, scoring against the rewritten GT's pass
criteria/fail signals: PASS / PARTIAL / FAIL / UNTESTED per criterion, with quoted evidence per verdict.
Honest-ledger rule binding: unexercised criteria are UNTESTED; a test-design issue is recorded as a
test-design issue AND the criterion stays UNTESTED.

**E5 — Results doc.** `evaluation/results-2026-07-13.md` per eval-protocol format: per-GT-per-platform
verdicts w/ evidence quotes + transcript refs, the two observed eval cells, token/turn efficiency notes
per run, method-limits section (n=1, dispatch-prompt install simulation, GT-7 gap), and the scorecard.
NO aggregate claim stronger than the per-cell verdicts support; the phrase "zero regressions" is banned
unless literally every criterion is PASS.

**E6 — Verification.** Fresh input-curated verifier: re-greps E1 fidelity (no v8 marker vocabulary
outside historical notes; all 9 GTs present; two-layer GT-8; GT-9 exists), spot-audits 3 randomly-chosen
verdicts against their transcripts (does the quoted evidence exist and support the verdict), checks the
honest-ledger rule (every PARTIAL/UNTESTED carries a reason; no banned aggregate), and re-runs the
repo regression set (validate-plan on all plans incl. this one, roundtrip, check-links, r8-dirs-untouched).

Role separation: planner dispatches; E1 worker, E2/E3 subjects, E4 judges, E6 verifier are all distinct
contexts; judges and verifier input-curated. Every subject DISPATCH PROMPT and every judge DISPATCH
PROMPT is persisted verbatim (`gt<N>-<plat>-prompt.md`, `gt<N>-<plat>-judge-prompt.md`) so curation is
auditable as an artifact, not a claim. Codex runs use shell-level `timeout` (codex exec has no native
timeout flag) and `-s workspace-write -C <fixture-dir>`. Rollback: all additions on the clean committed
base c8b6741 — `git checkout -- evaluation/ && git clean -fd evaluation/ PLAN-r9-evals.md` restores.
No pushes during the phase.

**Layer-2 pass 1 record (judge a6d5cef9d8a343031):** VERDICT BLOCKERS — 3 blockers, 5 concerns, all
C2-class local revises confirmed by direct inspection (standing relaxation: mechanical confirmation of
string-verifiable findings). Applied: E2 command now greps transcripts for leaked 'pass criteria'/'fail
signals' text and requires all 9 per-GT files explicitly + persisted dispatch prompts; E3 requires
codex-native session evidence per real transcript (session id recorded in the feasibility file and
cross-checked against ~/.codex/sessions rollouts) so a fabricated transcript cannot pass; E4E5 persists
per-cell judge verdict files, adds efficiency-note and UNTESTED-reason-co-occurrence greps; E6 writes
evaluation/audit-2026-07-13.md with machine-checkable AUDIT lines (≥3, no NO) plus a python step that
fgrep-verifies EVERY quoted-evidence span in the results doc against its referenced transcript; baseline
quote corrected to the file's literal 5 PASS / 3 PARTIAL; rollback pathspec fixed; E1 gains structural-
floor greps and E6 is instructed to diff the rewrite against the committed v8 golden-tasks (c8b6741) for
intent comparison — residual intent-drift risk is a legitimate judge question, named here honestly.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A3",
  "requirements": [
    {"id": "E1", "text": "golden-tasks.md rewritten r9-faithful: assurance markers, v1.1 contracts, two-layer GT-8, new GT-9 capability preflight, intent preserved"},
    {"id": "E2", "text": "Claude Code subject runs with verbatim transcripts; GT-6 two-turn; GT-7 UNTESTED with reason"},
    {"id": "E3", "text": "Codex subject runs feasibility-gated with verbatim transcripts; infeasible cells UNTESTED with probe evidence"},
    {"id": "E4", "text": "Input-curated per-transcript judging under the honest-ledger rule"},
    {"id": "E5", "text": "results-2026-07-13.md with per-cell verdicts, eval-cell observations, efficiency notes, method limits, no over-claiming"},
    {"id": "E6", "text": "Independent verification of rewrite fidelity, verdict-evidence integrity, ledger honesty, and repo regressions"}
  ],
  "tasks": [
    {"id": "E1", "title": "Golden-task rewrite", "deps": [],
     "contract": {"requirement_ids": ["E1"],
      "criteria": "9 GTs, r9-faithful vocabulary and mechanisms, intent and pass/fail-signal structure preserved, running-notes caveats updated",
      "acceptance_command": "test $(grep -c '^## Golden Task' evaluation/golden-tasks.md) -ge 9 && test $(grep -c 'Pass criteria' evaluation/golden-tasks.md) -ge 9 && test $(grep -c 'Fail signals' evaluation/golden-tasks.md) -ge 9 && grep -q '\\[ASSURANCE:' evaluation/golden-tasks.md && grep -q 'agentfw-plan' evaluation/golden-tasks.md && grep -q 'validate-plan' evaluation/golden-tasks.md && grep -qi 'capability preflight' evaluation/golden-tasks.md && grep -q 'independent_review' evaluation/golden-tasks.md && grep -qi 'risk_class' evaluation/golden-tasks.md && grep -qi 'planted defect' evaluation/golden-tasks.md && ! grep -q '\\[TASK CLASS' evaluation/golden-tasks.md && grep -qi 'two-layer\\|Layer 1' evaluation/golden-tasks.md",
      "expected_signal": "exit 0",
      "environment": "repo working tree",
      "evidence": "grep outputs + the rewritten file",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "risk": "rewrite drifts from GT intent (tests get easier) or keeps v8 vocabulary the subjects no longer see",
      "negative_cases": ["no [TASK CLASS marker survives", "GT count cannot drop below 9"],
      "rerunnable": true}},
    {"id": "E2", "title": "Claude Code subject runs", "deps": ["E1"],
     "contract": {"requirement_ids": ["E2"],
      "criteria": "8 verbatim claude transcripts (GT-7 has a stub recording UNTESTED + reason); GT-6 transcript shows two turns",
      "acceptance_command": "for n in 1 2 3 4 5 6 7 8 9; do test -s evaluation/transcripts-2026-07-13/gt$n-claude.md || { echo missing gt$n; exit 1; }; test -s evaluation/transcripts-2026-07-13/gt$n-claude-prompt.md || { echo missing gt$n prompt; exit 1; }; done && grep -qi 'phase 2' evaluation/transcripts-2026-07-13/gt6-claude.md && grep -qi 'UNTESTED' evaluation/transcripts-2026-07-13/gt7-claude.md && ! grep -rliE 'pass criteria|fail signals' evaluation/transcripts-2026-07-13/*-claude.md evaluation/transcripts-2026-07-13/*-claude-prompt.md | grep -q .",
      "expected_signal": "exit 0",
      "environment": "session subagents; transcripts under evaluation/transcripts-2026-07-13/",
      "evidence": "the transcript files",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "risk": "subject prompts leak evaluator expectations (coached subjects) — mitigated: subjects receive ONLY adapter content + GT prompt",
      "negative_cases": ["a transcript containing the string 'pass criteria' from the GT doc indicates leakage and fails the run"],
      "rerunnable": true}},
    {"id": "E3", "title": "Codex subject runs", "deps": ["E1"],
     "contract": {"requirement_ids": ["E3"],
      "criteria": "feasibility probe recorded; either 7+ codex transcripts or UNTESTED stubs carrying the probe output",
      "acceptance_command": "test -s evaluation/transcripts-2026-07-13/codex-feasibility.md && for n in 1 2 3 4 5 6 7 8 9; do f=evaluation/transcripts-2026-07-13/gt$n-codex.md; test -s $f || { echo missing gt$n; exit 1; }; grep -qi 'UNTESTED' $f || grep -q 'session_id:' $f || { echo \"gt$n: neither a real codex session record nor an honest UNTESTED stub\"; exit 1; }; done && for id in $(grep -o 'session_id: [a-f0-9-]*' evaluation/transcripts-2026-07-13/gt*-codex.md | awk '{print $2}' | sort -u); do ls ~/.codex/sessions/**/*$id* >/dev/null 2>&1 || ls ~/.codex/sessions/*$id* >/dev/null 2>&1 || find ~/.codex/sessions -name \"*$id*\" | grep -q . || { echo \"no rollout for $id\"; exit 1; }; done",
      "expected_signal": "exit 0",
      "environment": "codex exec in per-GT mktemp fixture dirs, sandboxed",
      "evidence": "transcript files + feasibility probe record",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "risk": "codex runs touch files outside the fixture dir or hang non-interactively — mitigated by sandbox flags + timeouts; infeasible => honest UNTESTED, never simulated output",
      "negative_cases": ["no codex transcript may be authored by a claude agent pretending to be codex — the feasibility record distinguishes real runs from UNTESTED stubs"],
      "rerunnable": true}},
    {"id": "E4E5", "title": "Judging + results doc", "deps": ["E2","E3"],
     "contract": {"requirement_ids": ["E4","E5"],
      "criteria": "per-cell verdicts with quoted evidence; honest ledger; eval-cell observations; method limits; scorecard",
      "acceptance_command": "test -s evaluation/results-2026-07-13.md && test $(grep -cE 'GT-[1-9].*(PASS|PARTIAL|FAIL|UNTESTED)' evaluation/results-2026-07-13.md) -ge 18 && for n in 1 2 3 4 5 6 7 8 9; do for p in claude codex; do test -s evaluation/transcripts-2026-07-13/gt$n-$p-verdict.md || { echo missing verdict gt$n-$p; exit 1; }; test -s evaluation/transcripts-2026-07-13/gt$n-$p-judge-prompt.md || { echo missing judge prompt gt$n-$p; exit 1; }; done; done && grep -qi 'method' evaluation/results-2026-07-13.md && grep -qi 'n=1' evaluation/results-2026-07-13.md && grep -qi 'marker' evaluation/results-2026-07-13.md && grep -qi 'escalat' evaluation/results-2026-07-13.md && grep -qiE 'token|efficien' evaluation/results-2026-07-13.md && ! grep -qi 'zero regressions' evaluation/results-2026-07-13.md && ! grep -riE 'test-design issue[^.]*(no regression|therefore pass)' evaluation/results-2026-07-13.md | grep -q . && ! grep -i 'UNTESTED' evaluation/results-2026-07-13.md | grep -viE 'reason|because|requires|no real|not run|method' | grep -q .",
      "expected_signal": "exit 0",
      "environment": "repo working tree",
      "evidence": "results doc + judge outputs embedded/reference",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "risk": "verdict inflation (the exact failure of the 2026-05-29 ledger) — the banned-phrase greps and E6 spot-audit exercise that layer",
      "negative_cases": ["the literal over-claim phrases are grep-banned", "every UNTESTED must co-occur with a stated reason (E6 audits)"],
      "rerunnable": true}},
    {"id": "E6", "title": "Independent verification", "deps": ["E1","E2","E3","E4E5"],
     "contract": {"requirement_ids": ["E6"],
      "criteria": "rewrite fidelity, verdict-evidence spot-audit (3 cells), ledger honesty, repo regressions",
      "acceptance_command": "python3 tools/validate-plan PLAN-r9-evals.md && python3 tools/validate-plan PLAN-r9.md >/dev/null && bash tools/tests/check-links.sh >/dev/null && test -z \"$(git diff --name-only HEAD -- core references variants)\" && test -s evaluation/audit-2026-07-13.md && test $(grep -c '^AUDIT ' evaluation/audit-2026-07-13.md) -ge 3 && ! grep '^AUDIT ' evaluation/audit-2026-07-13.md | grep -q 'NO' && python3 -c \"\nimport re,sys,os\ntxt=open('evaluation/results-2026-07-13.md').read()\nquotes=re.findall(r'> \\\"([^\\\"]{20,})\\\"\\s*\\((gt[1-9]-(?:claude|codex))\\)', txt)\nassert quotes, 'results doc must carry quoted evidence in the > \\\"...\\\" (gtN-plat) format'\nbad=[q[:40] for q,ref in quotes if q not in open(f'evaluation/transcripts-2026-07-13/{ref}.md').read()]\nassert not bad, f'evidence quotes not found in transcripts: {bad}'\nprint(f'EVIDENCE OK: {len(quotes)} quotes verified')\" && echo E6_MECHANICAL_OK",
      "expected_signal": "EVIDENCE OK line + E6_MECHANICAL_OK + audit file with >=3 AUDIT lines none NO + the verifier's report (incl. intent-diff vs the committed v8 golden-tasks at c8b6741) with zero unresolved findings",
      "environment": "repo working tree + transcripts",
      "evidence": "verifier report with quoted transcript evidence per audited verdict",
      "required_verification_tier": "adversarial",
      "integration_seam": true,
      "risk_class": "standard",
      "risk": "contract-bounded verification ceiling — verifier instructed to run off-contract probes on the verdicts (pick cells the judges scored PASS and try to refute them)",
      "negative_cases": ["a PASS verdict whose quoted evidence does not exist in the transcript is a blocker", "an UNTESTED without reason is a blocker"],
      "rerunnable": true}}
  ]
}
```
