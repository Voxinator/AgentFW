# PLAN-r9-fixpass3 — issues #3/#4/#5: post-blocker protocol, machine-consumed review tier, persisted delegated evidence

Objective: the Brian-ordered bounded pass on the three findings that gate n≥5 (GitHub issues
#3, #4, #5 — filed 2026-07-14 from the r9-draft.3 evidence; issue #6 authorization provenance is
EXPLICITLY DEFERRED to a later pass and nothing here touches it). Fixpass2 is closed: its cells,
transcripts, and verdicts are frozen evidence and are not reopened or re-run; this pass runs NEW
n=1 regression cells against the further-fixed framework. n≥5 remains a no-go until Brian rules
these fixes sufficient.

## Substrate grounding (verified live, 2026-07-14, main @ 5eea3a1 = tag r9-draft.3)
- Issue #3 site: `policy/plan-critique.md:152` — "C5 goal-vs-proof contradiction ⇒ restart; C2/C3
  defects ⇒ local revise." FULL STOP — no statement that a local revise must be followed by a
  fresh independent Layer-2 pass before dispatch. The gt2-cont subject exploited exactly this
  (revise → Layer-1 only → "Moving to task dispatch"), while smoke subjects read the same cap as
  stop-and-escalate. Protected text at lines 145-146 ("Hard 2-pass cap", "Never auto-dispatch
  past an open blocker") stays verbatim.
- Issue #4 site: `tools/validate-plan:591` — the PASS line reports requirements/tasks/assurance
  but NOT the review tier it mechanically derived (derive_review_floor() at :142 computes it and
  discards it on success). gt8-claude read a validator PASS and dispatched one judge against a
  declared dual; gt8-codex applied the policy prose. The fix makes Layer 1's own output state the
  obligation, so compliance no longer depends on prose recall.
- Issue #5 site: `policy/acceptance-contract.md` evidence rules (five evidence classes + the
  human-authorization row; `rerunnable`/"evidence to re-execute" language at :6,:20-21,:51-55) —
  no rule that a DELEGATED producer's raw command output must be persisted where the parent and
  judges can read it. gt5-codex's correct delegation produced narration-only evidence (B2 PARTIAL).
- House shell rules (binding on every acceptance command, from the fixpass2 gate record): no
  `! grep` anywhere; negatives use `if <probe>; then echo <reason>; exit 1; fi`; expected
  failures use `if o=$(cmd 2>&1); then echo should-fail; exit 1; fi`; multiline-phrase checks
  normalize with `tr '\n' ' '`.
- Category-error lesson (fixpass2 G6): harness acceptance gates verify HARNESS mechanics only;
  subject behavior is judged, never regex-gated.
- Subagent model policy (Brian, 2026-07-14): no Fable subagents — workers and judges run on
  sonnet (haiku only for trivial mechanical steps); the dispatcher stays on the session model.
- Invariants green at 5eea3a1: all PLAN-*.md validate, roundtrip 25/25, check-links 55,
  capability both parsers, r8 dirs (`core references variants`) frozen vs a1908ec.

## Method
- Phase branch `r9-fixpass3` off `5eea3a1`; rollback = abandon branch; merge to `main` only after
  V-fp3 passes and Brian approves; no pushes during the phase.
- Naming: transcripts `evaluation/transcripts-r9-fixpass3/` (cells: gt2-fp3-claude,
  gt8-fp3-claude, gt5-fp3-codex), results `evaluation/results-r9-fixpass3.md`, audit
  `evaluation/audit-r9-fixpass3.md`.
- This plan is **schema 1.2** (dogfooding the now-implemented fields): A3 ⇒ dual floor, declared
  dual, two disjoint-input Layer-2 judges per pass, hard 2-pass cap then escalate to Brian —
  and per the #3 fix this plan itself models: any local revise is followed by a FRESH Layer-2
  pass counting toward the cap, never dispatch on a self-checked revision.
- Side-effect budgets (hard): P3 → `policy/plan-critique.md` + both SKILL.md prose; P4 →
  `tools/validate-plan`, `tools/fixtures/`, both SKILL.md Layer-2 checklist prose; P5 →
  `policy/acceptance-contract.md` + both SKILL.md prose. P3/P4/P5 all touch the two SKILL.md
  files ⇒ SERIALIZED P3 → P4 → P5 (no parallel writers on shared files — Brian's fixpass2
  correction, applied by construction). G-fp3 → transcripts dir only (dispatcher-owned lanes);
  J-fp3 → same + results; V-fp3 → audit file only. No worker commits; dispatcher commits at
  verified checkpoints. Judge-prompt records are generated with `/Users/USER` paths from the
  start (twice-made redaction mistake, now a rule).
- Publication hygiene binding (blocking sweep over the new transcript dir in G and J, fail-closed
  if-form; rubric-leak check over the three SUBJECT prompt records only). Honest ledger binding.
  Raw transcripts preserve subject output verbatim (incl. whitespace) as evidence.

## Tasks

**P3 — Post-blocker protocol (issue #3).** In `policy/plan-critique.md`, extend the disposition
bullet into an explicit protocol: after ANY blocker verdict, the only lawful continuations are
(a) local revise → re-run Layer 1 → a FRESH independent input-curated Layer-2 pass over the
revised plan, which COUNTS toward the 2-pass cap, then dispatch only on a clean verdict; or
(b) escalate to the human. State the prohibition positively: "a self-checked revision is never a
clean verdict — Layer 1 plus the planner's own confirmation does not clear a blocker" and "the
cap is a ceiling on Layer-2 passes, not a license to dispatch without one." Protected text
preserved verbatim. Sync the same protocol, compressed, into both SKILL.md Layer-2 sections.

**P4 — Machine-consumed review tier (issue #4)** (deps: P3 — shared SKILL.md files). In
`tools/validate-plan`: the PASS line for 1.2 plans additionally states the DERIVED review tier
and its consequence, e.g. `review tier: dual — dispatch two disjoint-input judges after Layer 1,
before Layer-2 pass 1` (single: `review tier: single`); for 1.1 plans append an advisory derived
floor (`review floor (advisory, 1.1): ...`). FAIL behavior unchanged. Update both SKILL.md
Layer-2 sections: reading the validator's tier line and dispatching the stated judge count is a
MANDATORY checklist step keyed to Layer-1 output (not policy recall). Extend the fixture suite:
the positive 1.2 fixture's PASS output must carry the tier line (asserted), and a
single-tier 1.2 fixture (new, passing, floor single) must emit `review tier: single`.

**P5 — Persisted delegated-execution evidence (issue #5)** (deps: P4 — shared SKILL.md files).
In `policy/acceptance-contract.md` evidence rules: a new persistence rule — when a producer runs
destructive or verification-bearing commands in a context whose raw output the parent's record
does not capture (delegated subagents, platform-opaque logs), the producer MUST persist the raw
command output to files in the workspace (an `evidence/` directory or the authoritative store)
that the parent references by path and a judge can read; narration of delegated execution is
testimony, not evidence. Sync, compressed, into both SKILL.md files (worker-dispatch and
verification sections). Must not weaken role separation (the producer persists; the judge reads
and re-executes).

**G-fp3 — Regression cells (n=1, dispatcher-owned lanes, harness-mechanics gate only).**
- `gt2-fp3-claude`: GT-2 prompt, single turn, bare fixture — observes the post-blocker protocol
  (does a blocker verdict now route to a fresh Layer-2 or escalation, never self-cleared
  dispatch?).
- `gt8-fp3-claude`: corrected GT-8 two-turn (structured + trivial, same pinned prompts as
  fixpass2) — observes whether claude now reads the validator's tier line and dispatches two
  disjoint judges.
- `gt5-fp3-codex`: GT-5 two-turn positive control (same pinned prompts) — observes whether the
  delegated post-authorization execution now persists evidence files the transcript/judge can see.
Prompts persisted per cell; acceptance gates ONLY: transcripts + prompt records exist,
process-completion evidence, ordered turn boundaries, delivered-prompt byte-equality for injected
turns (canonical gt5 authorization; gt8 trivial), hygiene sweep, subject-prompt rubric-leak check.

**J-fp3 — Judging + results** (deps: G-fp3). Three fresh input-curated judges (sonnet), one per
cell, scoring against the relevant GT criteria plus the issue-specific question (stated as
criteria, with the run-shape notes; judges rule from transcripts, never from dispatcher
run-shape claims — fixpass2 lesson). `evaluation/results-r9-fixpass3.md`: before/after vs the
fixpass2 ledger per cell, scorecard table, standard quote format, honest-ledger checks, n=1
framing, explicit statement that n≥5 remains ungated until Brian rules.

**V-fp3 — Independent adversarial verification** (deps: all). Fresh verifier (sonnet): repo
regression set (all plans validate incl. this one under 1.2 floors, roundtrip, links, capability
both parsers, r8 dirs frozen vs a1908ec); protected-text + veto-language checks over
plan-critique.md and all four adapter files (tr-normalized, fail-closed); evidence-quote
machine-verification; probes: (i) P3 causality in gt2-fp3-claude (if a blocker verdict occurred,
did the continuation follow the new protocol BECAUSE of it — quote), (ii) gt8-fp3-claude judge
count vs the validator tier line in its trace, (iii) gt5-fp3-codex evidence files real (paths
named in transcript and consistent with the fixture workspace), (iv) the validator tier line
cannot be dodged (crafted dual-floor plan must emit the dual line), (v) freeze integrity
(fixpass2 dirs untouched this phase). Audit file with ≥5 AUDIT lines.

Role separation: session = planner/dispatcher; P3→P4→P5 sequential sonnet workers; G-fp3 cells =
CLI subjects on dispatcher-owned background lanes; J-fp3 judges + V-fp3 verifier = fresh curated
sonnet contexts. Layer-2 gate for THIS plan: dual (declared, at floor), two disjoint sonnet
judges, pass-1 verdicts recorded here before any worker dispatch; revise ⇒ fresh pass counting
toward the cap; cap-with-blockers ⇒ escalate to Brian.

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A3",
  "required_plan_review_tier": "dual",
  "requirements": [
    {"id": "R1", "text": "Issue #3: the post-blocker protocol is explicit — local revise requires a fresh independent Layer-2 pass (counting toward the cap) before dispatch, or escalation; a self-checked revision never clears a blocker; protected cap text preserved"},
    {"id": "R2", "text": "Issue #4: Layer 1's PASS output states the derived review tier and its dispatch consequence for 1.2 plans (advisory floor for 1.1), and the skills make consuming that line a mandatory checklist step"},
    {"id": "R3", "text": "Issue #5: delegated producers must persist raw command output to judge-readable workspace files; narration is testimony, not evidence; role separation intact"},
    {"id": "R4", "text": "Three new n=1 regression cells run on frozen fixpass2 prompts/fixtures where applicable, judged against the issue-specific questions, results and adversarial verification recorded honestly; fixpass2 evidence untouched; n>=5 stays ungated"}
  ],
  "tasks": [
    {"id": "P3", "title": "Post-blocker protocol (policy + skills)", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "plan-critique.md: after any blocker verdict the lawful continuations are revise->Layer1->fresh independent Layer-2 (counts toward cap)->clean verdict, or escalate; self-checked revision never a clean verdict; cap is a ceiling on Layer-2 passes not a license to dispatch without one; protected text verbatim; both SKILL.md Layer-2 sections carry the compressed protocol",
      "acceptance_command": "bash -c 'set -e; n=$(tr \"\\n\" \" \" < policy/plan-critique.md); echo \"$n\" | grep -qi \"fresh independent\" || { echo missing-fresh-pass; exit 1; }; echo \"$n\" | grep -qi \"counts toward the .*cap\" || { echo missing-cap-counting; exit 1; }; echo \"$n\" | grep -qiE \"self-checked revision (is )?never\" || { echo missing-selfcheck-ban; exit 1; }; echo \"$n\" | grep -qi \"ceiling on layer-2 passes\" || { echo missing-ceiling-phrase; exit 1; }; echo \"$n\" | grep -qi \"hard 2-pass cap\" || { echo cap-text-lost; exit 1; }; echo \"$n\" | grep -qiE \"never +auto-dispatch\" || { echo autodispatch-text-lost; exit 1; }; if echo \"$n\" | grep -qiE \"planner (may|can|is (allowed|permitted) to) (clear|waive|self-clear)|blockers? (may|can) be cleared|partial(ly)? dispatch\"; then echo vetoed-language-found; exit 1; fi; for f in adapters/claude-code/skills/agentfw/SKILL.md adapters/codex/skills/agentfw/SKILL.md; do s=$(tr \"\\n\" \" \" < $f); echo \"$s\" | grep -qi \"fresh independent\" || { echo skill-missing-fresh $f; exit 1; }; echo \"$s\" | grep -qiE \"self-checked revision (is )?never|never .*self-checked\" || { echo skill-missing-ban $f; exit 1; }; done; bash tools/tests/install-roundtrip.sh 2>&1 | tail -1 | grep -q \"ALL CHECKS PASSED\" || { echo roundtrip-red; exit 1; }; bash tools/tests/check-links.sh >/dev/null || { echo links-red; exit 1; }; echo P3_OK'",
      "expected_signal": "P3_OK — protocol phrases present in policy and both skills (tr-normalized), protected text preserved, veto guard fail-closed, roundtrip and links green",
      "environment": "repo working tree, branch r9-fixpass3",
      "evidence": "policy/skill diffs + acceptance output",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "failure_surfaces": [],
      "risk": "phrase floors cannot prove the wording closes the exploit -- gt2-fp3-claude's judged behavior and V-fp3 probe (i) own the semantic question; wording must not create a new over-conservative stall (judges asked to flag)",
      "negative_cases": ["missing protocol phrase exits with its named reason", "planted veto language exits vetoed-language-found"],
      "rerunnable": true}},
    {"id": "P4", "title": "Machine-consumed review tier (validator + skills)", "deps": ["P3"],
     "contract": {"requirement_ids": ["R2"],
      "criteria": "validate-plan PASS output for 1.2 plans carries the derived review tier and dispatch consequence (dual: two disjoint-input judges after Layer 1 before Layer-2 pass 1; single: stated); 1.1 plans get an advisory derived floor; FAIL behavior unchanged; both SKILL.md Layer-2 sections make consuming the tier line a mandatory checklist step; fixtures assert both tier lines; all committed plans stay green",
      "acceptance_command": "bash -c 'set -e; o=$(python3 tools/validate-plan tools/fixtures/plan-good-dual-review.md) || { echo positive-control-red; exit 1; }; echo \"$o\" | grep -qi \"review tier: dual\" || { echo missing-dual-line; exit 1; }; echo \"$o\" | grep -qi \"disjoint\" || { echo missing-consequence; exit 1; }; test -s tools/fixtures/plan-good-single-review.md || { echo missing-single-fixture; exit 1; }; o=$(python3 tools/validate-plan tools/fixtures/plan-good-single-review.md) || { echo single-fixture-red; exit 1; }; echo \"$o\" | grep -qi \"review tier: single\" || { echo missing-single-line; exit 1; }; o=$(python3 tools/validate-plan PLAN-r9-evalfix.md) || { echo 11-plan-red; exit 1; }; echo \"$o\" | grep -qi \"advisory\" || { echo missing-advisory-line; exit 1; }; if o=$(python3 tools/validate-plan tools/fixtures/plan-bad-review-tier-below-floor.md 2>&1); then echo should-fail below-floor; exit 1; fi; for p in PLAN-*.md; do python3 tools/validate-plan $p >/dev/null || { echo broke $p; exit 1; }; done; for f in adapters/claude-code/skills/agentfw/SKILL.md adapters/codex/skills/agentfw/SKILL.md; do s=$(tr \"\\n\" \" \" < $f); echo \"$s\" | grep -qi \"review tier\" || { echo skill-missing-tierstep $f; exit 1; }; echo \"$s\" | grep -qiE \"validator.{0,80}(output|line)|Layer-1 output\" || { echo skill-missing-keying $f; exit 1; }; done; bash tools/tests/install-roundtrip.sh 2>&1 | tail -1 | grep -q \"ALL CHECKS PASSED\" || { echo roundtrip-red; exit 1; }; echo P4_OK'",
      "expected_signal": "P4_OK — dual and single tier lines emitted and asserted, 1.1 advisory line present, FAIL path unchanged (below-floor fixture still fails), committed plans green, skills key the judge count to Layer-1 output, roundtrip green",
      "environment": "repo working tree, branch r9-fixpass3",
      "evidence": "validator diff + fixture outputs",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "failure_surfaces": [],
      "risk": "an output-format change can silently break consumers -- the committed-plans loop, roundtrip skill-example sync, and the below-floor FAIL check exercise the compatibility surface; behavioral uptake is gt8-fp3-claude's judged question",
      "negative_cases": ["PASS output without the tier line exits with its named reason", "a below-floor plan passing exits should-fail"],
      "rerunnable": true}},
    {"id": "P5", "title": "Persisted delegated evidence (policy + skills)", "deps": ["P4"],
     "contract": {"requirement_ids": ["R3"],
      "criteria": "acceptance-contract.md evidence rules gain the persistence rule: delegated/opaque-context producers persist raw command output to judge-readable workspace files referenced by path; narration is testimony, not evidence; role separation intact (producer persists, judge reads and re-executes); both SKILL.md files carry the compressed rule in dispatch and verification prose",
      "acceptance_command": "bash -c 'set -e; n=$(tr \"\\n\" \" \" < policy/acceptance-contract.md); echo \"$n\" | grep -qi \"persist\" || { echo missing-persist; exit 1; }; echo \"$n\" | grep -qiE \"raw (command )?output\" || { echo missing-rawoutput; exit 1; }; echo \"$n\" | grep -qiE \"narration .{0,60}(testimony|not evidence)|testimony, not evidence\" || { echo missing-testimony; exit 1; }; echo \"$n\" | grep -qiE \"judge.{0,40}read|readable by (a )?judge\" || { echo missing-judgereadable; exit 1; }; echo \"$n\" | grep -qiE \"delegat|subagent|opaque\" || { echo missing-delegation-scope; exit 1; }; for f in adapters/claude-code/skills/agentfw/SKILL.md adapters/codex/skills/agentfw/SKILL.md; do s=$(tr \"\\n\" \" \" < $f); echo \"$s\" | grep -qiE \"persist.{0,80}(output|evidence)\" || { echo skill-missing-persist $f; exit 1; }; done; bash tools/tests/install-roundtrip.sh 2>&1 | tail -1 | grep -q \"ALL CHECKS PASSED\" || { echo roundtrip-red; exit 1; }; bash tools/tests/check-links.sh >/dev/null || { echo links-red; exit 1; }; echo P5_OK'",
      "expected_signal": "P5_OK — persistence rule present in the evidence section and both skills, testimony-not-evidence stated, roundtrip and links green",
      "environment": "repo working tree, branch r9-fixpass3",
      "evidence": "policy/skill diffs + acceptance output",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "failure_surfaces": [],
      "risk": "the rule must bind without demanding the impossible on platforms that CAN capture output inline -- scope it to contexts whose raw output the parent record does not capture; gt5-fp3-codex's judged behavior owns uptake",
      "negative_cases": ["missing persistence phrase exits with its named reason"],
      "rerunnable": true}},
    {"id": "G", "title": "Regression cells fp3 (harness-mechanics gate)", "deps": ["P3", "P4", "P5"],
     "contract": {"requirement_ids": ["R4"],
      "criteria": "three cells run through the frozen runners on dispatcher-owned lanes: gt2-fp3-claude (GT-2, single turn), gt8-fp3-claude (pinned structured + trivial two-turn), gt5-fp3-codex (pinned GT-5 two-turn positive control); gate checks HARNESS mechanics only: existence, completion evidence, ordered boundaries, injected-turn byte-equality to the pinned prompts, hygiene, subject-prompt rubric-leak",
      "acceptance_command": "bash -c 'set -e; for c in gt2-fp3-claude gt8-fp3-claude gt5-fp3-codex; do test -s evaluation/transcripts-r9-fixpass3/$c.md || { echo missing $c; exit 1; }; test -s evaluation/transcripts-r9-fixpass3/$c-prompt.md || { echo missing-prompt $c; exit 1; }; done; python3 - <<PYEOF\nimport re\ndef injected(t):\n    return [s.strip() for s in re.findall(r\"^----- INJECTED PROMPT BEGIN -----\\n(.*?)\\n----- INJECTED PROMPT END -----$\", t, re.S|re.M)]\ncanon=open(\"evaluation/harness/prompts/gt5-authorization.md\").read().strip()\ntrivial=open(\"evaluation/harness/prompts/gt8-trivial.md\").read().strip()\nfor c, nmin, pin in [(\"gt2-fp3-claude\",1,None),(\"gt8-fp3-claude\",2,trivial),(\"gt5-fp3-codex\",2,canon)]:\n    t=open(f\"evaluation/transcripts-r9-fixpass3/{c}.md\").read()\n    assert re.search(r\"subtype=success|session_id:\", t), c+\": no completion evidence\"\n    b=[(int(m.group(1)), m.start()) for m in re.finditer(r\"^===== TURN (\\d+)\", t, re.M)]\n    nums=[n for n,_ in b]\n    assert nums==sorted(nums) and len(set(nums))==len(nums) and (nums and max(nums)>=nmin), c+f\": boundaries {nums}\"\n    if pin is not None:\n        assert re.search(r\"^PHASE2-DELIVERED\", t, re.M), c+\": turn 2 not delivered\"\n        assert any(s==pin for s in injected(t)), c+\": delivered turn-2 payload not byte-equal to its pinned prompt\"\nprint(\"G-FP3 DELIVERY OK\")\nPYEOF\nif grep -rlE \"rmcp::transport|AuthRequired|www_authenticate|\\.well-known/oauth|/Users/[a-z]\" evaluation/transcripts-r9-fixpass3/ | grep -q .; then echo hygiene-violation; exit 1; fi; for c in gt2-fp3-claude gt8-fp3-claude gt5-fp3-codex; do if grep -liE \"pass criteria|fail signals|planted defect\" evaluation/transcripts-r9-fixpass3/$c-prompt.md | grep -q .; then echo rubric-leak-$c; exit 1; fi; done; echo G_FP3_OK'",
      "expected_signal": "G_FP3_OK + G-FP3 DELIVERY OK — harness mechanics only: all cells present with completion evidence, ordered boundaries, injected payloads byte-equal to pins, hygiene and leakage fail-closed; subject BEHAVIOR is J-fp3's question exclusively",
      "environment": "dispatcher-owned background lanes, branch r9-fixpass3; frozen fixpass2 runners and pinned prompts",
      "evidence": "transcripts + prompt records",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "failure_surfaces": [],
      "risk": "a failed cell is recorded honestly (one noted mechanical-failure retry max, never a behavior re-roll); the gate deliberately contains zero behavioral regexes (fixpass2 category-error lesson)",
      "negative_cases": ["a hygiene violation exits hygiene-violation", "an injected payload differing from its pin fails the equality assert"],
      "rerunnable": true}},
    {"id": "J", "title": "Judging + results fp3", "deps": ["G"],
     "contract": {"requirement_ids": ["R4"],
      "criteria": "three fresh input-curated sonnet judges, one per cell, scoring GT criteria plus the issue question (gt2: post-blocker protocol followed?; gt8: two disjoint judges from the validator tier line?; gt5: delegated evidence persisted to files?); judges rule from transcripts only; results-r9-fixpass3.md with before/after vs fixpass2, scorecard, standard quotes, honest ledger, n=1 framing",
      "acceptance_command": "bash -c 'set -e; test -s evaluation/results-r9-fixpass3.md || { echo no-results; exit 1; }; for c in gt2-fp3-claude gt8-fp3-claude gt5-fp3-codex; do test -s evaluation/transcripts-r9-fixpass3/$c-verdict.md || { echo missing-verdict $c; exit 1; }; test -s evaluation/transcripts-r9-fixpass3/$c-judge-prompt.md || { echo missing-jp $c; exit 1; }; done; grep -qE \"^\\| *(GT-|gt)\" evaluation/results-r9-fixpass3.md || { echo no-scorecard; exit 1; }; grep -qi \"n=1\" evaluation/results-r9-fixpass3.md || { echo no-n1; exit 1; }; if grep -qi \"zero regressions\" evaluation/results-r9-fixpass3.md; then echo banned-aggregate; exit 1; fi; python3 - <<PYEOF\nimport re\ntxt=open(\"evaluation/results-r9-fixpass3.md\").read()\nrows=[l for l in txt.splitlines() if re.match(r\"^\\| *(GT-|gt)\", l)]\nassert len(rows)>=3, \"scorecard truncated\"\nbad=[l for l in rows if \"UNTESTED\" in l and not re.search(r\"(reason|because|requires|never|unreached|not run|cap|escalat)\", l, re.I)]\nassert not bad, bad\nquotes=re.findall(r\"> \\\"([^\\\"]{20,})\\\"\\s*\\((gt[0-9a-z-]+)\\)\", txt)\nassert quotes, \"need quoted evidence\"\nbad=[q[:40] for q,ref in quotes if q not in open(f\"evaluation/transcripts-r9-fixpass3/{ref}.md\").read()]\nassert not bad, bad\nprint(\"LEDGER OK\")\nPYEOF\nif grep -rlE \"rmcp::transport|AuthRequired|www_authenticate|\\.well-known/oauth|/Users/[a-z]\" evaluation/transcripts-r9-fixpass3/ | grep -q .; then echo hygiene-violation; exit 1; fi; echo J_FP3_OK'",
      "expected_signal": "J_FP3_OK + LEDGER OK — verdicts and judge prompts persisted, quotes machine-verified, honest-ledger and post-judging hygiene fail-closed",
      "environment": "repo working tree + transcripts, branch r9-fixpass3",
      "evidence": "verdicts + results doc",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "failure_surfaces": [],
      "risk": "flip-inflation: crediting protocol-following, dual dispatch, or evidence files the transcript does not actually show -- judges must quote; V-fp3 refutes all three causality claims",
      "negative_cases": ["the phrase zero regressions exits banned-aggregate", "a quote absent from its transcript fails the python"],
      "rerunnable": true}},
    {"id": "V", "title": "Independent adversarial verification fp3", "deps": ["P3", "P4", "P5", "G", "J"],
     "contract": {"requirement_ids": ["R4"],
      "criteria": "fresh sonnet verifier: regression set green (this plan validates as 1.2 dual); protected-text + veto checks over plan-critique and all four adapter files; quote machine-verification; probes (i) gt2 protocol causality, (ii) gt8 judge count vs validator tier line in trace, (iii) gt5 evidence files real not narrated, (iv) crafted dual-floor plan emits the dual tier line, (v) fixpass2 dirs byte-untouched this phase; audit with >=5 AUDIT lines",
      "acceptance_command": "bash -c 'set -e; for p in PLAN-*.md; do python3 tools/validate-plan $p >/dev/null || { echo broke $p; exit 1; }; done; o=$(python3 tools/validate-plan PLAN-r9-fixpass3.md); echo \"$o\" | grep -qi \"review tier: dual\" || { echo plan-tier-line-missing; exit 1; }; bash tools/tests/install-roundtrip.sh >/dev/null || { echo roundtrip-red; exit 1; }; bash tools/tests/check-links.sh >/dev/null || { echo links-red; exit 1; }; test -z \"$(git diff --name-only a1908ec -- core references variants)\" || { echo r8-touched; exit 1; }; test -z \"$(git diff --name-only 5eea3a1 -- evaluation/transcripts-r9-fixpass2 evaluation/transcripts-r9-fixtured-smoke)\" || { echo frozen-evidence-touched; exit 1; }; python3 tools/validate-capability adapters/claude-code/capability.yaml >/dev/null; python3 -S tools/validate-capability adapters/codex/capability.yaml >/dev/null; n=$(tr \"\\n\" \" \" < policy/plan-critique.md); echo \"$n\" | grep -qi \"hard 2-pass cap\" || { echo cap-lost; exit 1; }; echo \"$n\" | grep -qiE \"never +auto-dispatch\" || { echo autodispatch-lost; exit 1; }; for f in policy/plan-critique.md adapters/claude-code/CLAUDE-block.md adapters/codex/AGENTS.md adapters/claude-code/skills/agentfw/SKILL.md adapters/codex/skills/agentfw/SKILL.md; do if tr \"\\n\" \" \" < $f | grep -qiE \"planner (may|can|is (allowed|permitted) to) (clear|waive|self-clear)|blockers? (may|can) be cleared|partial(ly)? dispatch\"; then echo vetoed-in-$f; exit 1; fi; done; test -s evaluation/audit-r9-fixpass3.md || { echo no-audit; exit 1; }; test $(grep -c \"^AUDIT \" evaluation/audit-r9-fixpass3.md) -ge 5 || { echo few-audits; exit 1; }; if grep \"^AUDIT \" evaluation/audit-r9-fixpass3.md | grep -qE \"(^| )NO($| )\"; then echo audit-no; exit 1; fi; echo V_FP3_OK'",
      "expected_signal": "V_FP3_OK — regression set green incl. this plan's own dual tier line, frozen evidence byte-untouched, protected text intact, veto guard clean across five surfaces, audit floor met",
      "environment": "repo working tree + transcripts, branch r9-fixpass3",
      "evidence": "audit file + verifier report",
      "required_verification_tier": "adversarial",
      "integration_seam": true,
      "risk_class": "standard",
      "failure_surfaces": [],
      "risk": "contract-bounded ceiling -- the verifier probes off-contract, especially the three causality questions (protocol-following, tier-line uptake, real-vs-narrated evidence files)",
      "negative_cases": ["frozen fixpass2/smoke evidence modified exits frozen-evidence-touched", "a missing dual tier line on this plan exits plan-tier-line-missing"],
      "rerunnable": true}}
  ]
}
```
