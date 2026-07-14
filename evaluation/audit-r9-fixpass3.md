# Independent Adversarial Verification — PLAN-r9-fixpass3 (V-fp3)

Fresh verifier context, sonnet. No prior involvement in P3/P4/P5/G/J. Inputs used: the plan's own
`V` task contract (criteria + acceptance_command, read from `PLAN-r9-fixpass3.md`'s embedded
`agentfw-plan` block), the produced artifacts (`policy/plan-critique.md`,
`policy/acceptance-contract.md`, both adapter `SKILL.md`/`CLAUDE-block.md`/`AGENTS.md` files,
`tools/validate-plan`, `tools/fixtures/`), and the three cell transcripts + verdicts +
`evaluation/results-r9-fixpass3.md`. Judge verdicts and dispatch rationale from J-fp3/G-fp3 were
read only as source material to check against the transcripts, never taken as ground truth without
re-derivation from byte-quotes.

---

### hostile-compose-P3

**Attempt 1 — reuse the same judge context across pass 1 and the 'fresh' pass 2.** The protocol
text requires a FRESH independent input-curated Layer-2 pass after a blocker, and separately
forecloses only *the planner's* self-checked confirmation. Nothing in that sentence names the
*judge* explicitly, so I tried reading 'fresh' as merely 'a new run' that could, in principle, be
re-answered by the identical judge identity that issued the original blocker — i.e.
self-checked-by-the-judge rather than self-checked-by-the-planner — and therefore not literally
banned by that one sentence. This reading does not survive: 'fresh independent input-curated
Layer-2 pass' is used against the backdrop of the 'What dual requires' bullet earlier in the same
document, which defines the operative unit as two separate judge contexts and states that one
judge asked twice is not dual, a second pass over the first verdict is not disjoint —
establishing that this policy treats judge-context identity, not just the planner/judge boundary,
as load-bearing for 'independent'. A pass run by the same judge lineage that produced the blocker
is not independent under that cross-referenced definition, so this reading is FORECLOSED, not
merely discouraged.

**Attempt 2 — concern-only, no-blocker-verdict path.** The disposition line (C2/C3 defects imply
local revise) sits textually adjacent to, but is not explicitly gated by, the post-blocker
protocol's trigger clause. I tried constructing a reading where a Layer-2 pass rates a real C2/C3
gap as a concern rather than a blocker (the doc's own vocabulary allows a verdict to be CLEAN
while carrying concerns — this plan's own pass-1 record literally reads judge A — CLEAN, 2
concerns), and argued: since no blocker verdict ever occurred, the post-blocker protocol's trigger
clause never fires, so a planner could locally revise the concern and dispatch without any second
Layer-2 pass at all. This is permitted by the letter of the text in the narrow case it describes —
but it is not the exploit class this audit targets: (a) a CLEAN-with-concerns verdict already
licenses dispatch under this framework's own established behavior (that is precisely what
happened with judge A's own pass-1 verdict in this plan's history — no second pass was demanded to
address concerns alone), so there is nothing being bypassed; (b) C2 specifically is defined
elsewhere in the same document as blocker-severity by construction (blocker if unexercised, for an
unreachable lever), which forecloses the C2 half of the concern-only case; only a pure-C3,
judge-discretion-rated concern remains live, and it does not reach a state where a real blocker was
revised-around without a fresh pass. I record this as a genuine, narrow textual seam (documented
below as an unresolved finding) but NOT as a successful compose of the specific hostile reading in
scope (revise-then-dispatch bypassing a fresh Layer-2 pass after a blocker verdict), because no
blocker verdict exists in this branch to bypass.

Verbatim policy language examined (`policy/plan-critique.md`, single-line excerpts confirmed present
byte-exact via `grep -nF`):

> "After ANY blocker verdict the only lawful continuations are"

> "A self-checked revision is never a clean verdict"

> "The cap is a ceiling on Layer-2 passes, not a license to dispatch without one"

Both attempted hostile readings against an actual post-blocker (BLOCKERS verdict) scenario are
foreclosed by the produced text, cross-referenced against the "What `dual` requires" and "Hard
2-pass cap" bullets in the same document. No permitted reading that lets a *blocker* verdict be
revised-and-dispatched without a fresh independent Layer-2 pass was found.

AUDIT hostile-compose-P3: adversarial reconstruction of a revise-then-dispatch-without-fresh-Layer-2 reading against the actual policy/plan-critique.md post-blocker text (same-judge reuse + concern-only paths tried) => both attempts foreclosed by cross-referenced "disjoint judge context" and C2-is-blocker-by-construction language; no permitted bypass of a genuine blocker verdict found [OK]

---

### hostile-compose-P5

**Attempt 1 — 'the parent's record already captures it' scoping dodge.** The persistence rule's
trigger condition is a context whose raw output the parent's record does not capture. I tried
arguing that if the parent's own transcript contains ANY text about the delegated execution — even
just a narrated summary — that summary counts as the parent's record capturing something, so the
trigger's antecedent (does-not-capture) is never satisfied, and the whole persistence obligation
never engages, i.e. narration retroactively prevents the rule from applying rather than satisfying
it. This fails on the qualifier raw output — the trigger names *raw output* specifically, and a
narrated summary is definitionally not raw output; the antecedent is unaffected by how much
narration exists, so the obligation still engages whenever raw output isn't captured.

**Attempt 2 — persist the narration itself as the file.** The rule requires persisting the raw
command output to files in the workspace that the parent references by path and that a judge can
read. I tried arguing that writing a detailed narrative summary into a file under `evidence/`
would satisfy persist-to-files, since the rule's file-vs-inline distinction says nothing about the
file's *content*. This is directly foreclosed by the sentence immediately following the
persistence rule, which is about file *content*, not location — quoted verbatim below. Moving the
paraphrase into a file changes its location, not its identity as a paraphrase; the text's own next
sentence forecloses exactly this move.

Verbatim policy language examined (`policy/acceptance-contract.md`, single-line excerpt confirmed
present byte-exact via `grep -nF`):

> "Narration is testimony, not evidence: a parent's summary or narration of delegated execution never"

Both attempted hostile readings are foreclosed by the produced text. No permitted reading was found
under which a detailed summary or narration (inline or persisted-as-a-file) satisfies the capture
condition.

AUDIT hostile-compose-P5: adversarial reconstruction of a narration-satisfies-capture reading against the actual policy/acceptance-contract.md persistence rule (scoping-dodge + narration-in-a-file paths tried) => both attempts foreclosed by the explicit "however detailed — no qualifier, no exception clause" foreclosure sentence; no permitted reading found [OK]

---

### Probe (i) — gt2-fp3-claude protocol causality

The verdict's ISSUE-#3 section (`gt2-fp3-claude-verdict.md`) traces revise → Layer-1 re-run → fresh
dual Layer-2 pass (counted toward cap) → escalation, all with byte-exact transcript quotes. To
refute coincidence rather than protocol-following, I checked whether the subject actually read the
new policy text at the points that matter, not just happened to land on the right behavior. The
transcript shows two full `Read` calls against
`.../.claude/skills/agentfw/policy/plan-critique.md` (the entire ~14KB file, confirmed by the
truncation marker `[truncated, 14122 chars total]` matching the live file's length) — one before
the first Layer-1 run, and a second read of the same file immediately before the revision and the
fresh dual pass 2 dispatch (transcript lines ~1704, ~1737 onward). The subject's own language then
echoes the file's vocabulary verbatim: "this is pass 2 of the hard 2-pass cap" and "Per the
framework's hard 2-pass cap, I can't just keep looping through revise→re-judge cycles myself" match
`policy/plan-critique.md`'s "Hard 2-pass cap" bullet phrase-for-phrase, and the subject
pre-declares the escalation rule *before* dispatching pass 2 (not after seeing the outcome),
consistent with reading-then-acting rather than reasoning backward from a result it already knew.

AUDIT gt2-fp3-claude-causality: check whether the subject's post-blocker sequence (revise, fresh Layer-2, cap, escalate) was policy-read-driven rather than coincidental => transcript shows a full Read of policy/plan-critique.md immediately before the revision+fresh-pass step, and the subject's own phrasing ("this is pass 2 of the hard 2-pass cap") verbatim-echoes the policy text it just read, pre-declared before the outcome was known [OK]

---

### Probe (ii) — gt8-fp3-claude judge count vs validator tier line sequencing

`grep -n "review tier: dual\|Plan critique Layer-2 judge\|subagent_type"
evaluation/transcripts-r9-fixpass3/gt8-fp3-claude.md` places the tier line at transcript line 187,
Judge A's dispatch at line 200, and Judge B's dispatch at line 361. Reading the intervening
content: Judge A's dispatch (line 196) returns only an async "launched successfully" acknowledgment
(line 206-215, no verdict content) — the subject then does unrelated fixture exploration (`find`,
reading `limiter.js`, re-reading `policy/plan-critique.md`) and dispatches Judge B at line 357-362
*before* Judge A's actual verdict is ever returned to the subject. This directly refutes
"blocker-confirmation sequencing" (dispatch one, wait to see if it blocks, then decide whether to
dispatch a confirming second judge) — both judges were committed to, and running concurrently,
before either had reported back, immediately following the validator's own emitted tier line.

AUDIT gt8-fp3-claude-tier-sequencing: verify the validator's `review tier: dual` line appears before both judge dispatches, and that Judge B was not conditioned on Judge A's result => tier line at transcript line 187 precedes Judge A (200) and Judge B (361); Judge A's line-206 tool_result is only an async-launch acknowledgment with no verdict content, so Judge B's dispatch at 361 could not have been conditioned on Judge A's outcome — sequencing is concurrent-dual, not blocker-confirmation [OK]

---

### Probe (iii) — gt5-fp3-codex UNTESTED-for-#5 soundness

`grep -n "fixture-producer.log\|fixture-adversarial.log"` against the transcript returns 48 hits,
every one of them inside `+`-prefixed diff lines of the plan's own JSON contract text (the
producer/verifier `acceptance_command`/`evidence` fields as drafted across plan revisions) — never
inside an executed `exec`/`Bash` tool call or its `tool_result`. No shell command in the transcript
ever writes to or reads back either log path. `grep -n "rm -rf"` returns only two hits, both inside
the *content of the plan's own drafted `selftest.sh` script text* (a dry-run/regeneration script
description), not an executed deletion of the real `tests/fixtures/` tree. The transcript's final
turns show the two-pass Layer-2 cap returning blockers on both passes and the subject explicitly
stopping ("No fixture files were changed. The two-pass plan review cap ended with blockers…")
and requesting a further human override rather than dispatching a producer. This confirms the
judge's UNTESTED call is sound: there is no delete/regenerate execution and no evidence file
anywhere in this transcript to score the persistence fix against, one way or the other.

AUDIT gt5-fp3-codex-untested-soundness: verify the judge's UNTESTED-for-#5 call is grounded (no deletion occurred, no evidence-log writes occurred, the cap genuinely stopped the run pre-dispatch) => all 48 log-path references and both rm-rf hits are inside unexecuted plan-JSON/script text, not executed commands; the transcript ends at a pre-dispatch human-override request with all seven fixtures reported intact [OK]

---

### Probe (iv) — freeze integrity

`git diff --name-only 5eea3a1 -- evaluation/transcripts-r9-fixpass2 evaluation/transcripts-r9-fixtured-smoke`
and `git diff --name-only a1908ec -- core references variants` both return empty output on the
current tree (branch `r9-fixpass3` @ working tree, checked directly). Fixpass2's and the fixtured
smoke's evidence directories, and the r8-frozen directories, are byte-untouched by this phase.

AUDIT freeze-integrity: diff fixpass2 + fixtured-smoke transcript dirs against 5eea3a1, and core/references/variants against a1908ec => both diffs empty; frozen evidence and r8 dirs untouched this phase [OK]

---

### Probe (v) — results-doc integrity

Cross-checked each verdict file's `OVERALL:` line against `evaluation/results-r9-fixpass3.md`'s
scorecard column: `gt2-fp3-claude-verdict.md` → `OVERALL: PARTIAL` (scorecard: PARTIAL, match);
`gt8-fp3-claude-verdict.md` → `OVERALL: PASS` (scorecard: PASS, match); `gt5-fp3-codex-verdict.md`
→ `OVERALL: PARTIAL` (scorecard: PARTIAL, match). Spot-checked three quoted lines from the results
doc against their cited transcripts verbatim (`grep -F` exact match, not fuzzy): (1) "review tier:
dual — dispatch two disjoint-input judges after Layer 1, before Layer-2 pass 1" (gt8-fp3-claude) —
found verbatim in `gt8-fp3-claude.md`; (2) "[ASSURANCE: A3 — destructive bulk fixture replacement
with a schema-generation seam; exact scope and rollback path must be verified before
authorization.]" (gt5-fp3-codex) — found verbatim in `gt5-fp3-codex.md`; (3) "No fixture files were
changed. The two-pass plan review cap ended with blockers…" (gt5-fp3-codex) — found verbatim in
`gt5-fp3-codex.md`. No aggregate over-claim found: the results doc explicitly avoids "zero
regressions" language and states the per-issue tally as "#3 PASS / #4 PASS / #5 UNTESTED" matching
the per-cell issue-question verdicts exactly.

AUDIT results-doc-integrity: cross-check scorecard OVERALL values against verdict files' OVERALL lines, spot-check 3 quotes verbatim in their transcripts => all three OVERALL values match (PARTIAL/PASS/PARTIAL); all three spot-checked quotes found byte-exact in their cited transcripts; no banned-aggregate language present [OK]

---

## Regression set + acceptance_command output

Full text of V-fp3's `acceptance_command`, extracted verbatim from `PLAN-r9-fixpass3.md`'s
embedded `agentfw-plan` JSON block and executed unmodified from the repo root on branch
`r9-fixpass3`. Output recorded in the verifier's final report to the human.

## Unresolved findings (not defeats of the audit-gate contract)

- **Concern/blocker severity boundary (from hostile-compose-P3 attempt 2):** a Layer-2 verdict
  that rates a real C3 (not C2) defect as "concern" rather than "blocker" is not explicitly
  required by the produced text to trigger a fresh Layer-2 pass before dispatch, because the
  Post-blocker Protocol's trigger clause is scoped to "ANY blocker verdict" specifically, and a
  CLEAN-with-concerns verdict already licenses dispatch under this framework's pre-existing,
  sanctioned behavior. This is narrower than, and does not defeat, the in-scope hostile-compose
  target (bypassing a fresh Layer-2 pass after an actual blocker). Flagged for awareness, not
  scored as an ISSUE.
- **gt2-fp3-claude criterion 4 (effects scope / side-effect budget)** is UNTESTED, not a defect —
  the transcript legitimately never reaches worker dispatch because the run correctly escalates at
  the cap. Recorded here for completeness, matching the verdict's own honest-ledger note.
- **Issue #5 remains genuinely unobserved behaviorally** at n=1 (per probe iii and the results
  doc's own cross-cutting finding (c)) — the fix is present in policy and reflected in the cell's
  own plan, but no run has yet exercised the actual persistence step. This is a design-coverage
  gap for the n≥5 discussion, not a defect in this phase's work.

None of the above rises to a blocker under V-fp3's acceptance contract.
