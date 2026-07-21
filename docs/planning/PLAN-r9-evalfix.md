# PLAN-r9-evalfix — eval harness fixes + fixture repos + fixtured smoke re-run

Objective: execute HANDOFF-r9.md §5 A+B plus a single n=1 smoke re-run of the affected cells
(Brian's approved sequencing: build, smoke, then PAUSE — the n≥5 matrix is a separate, explicitly
authorized phase). This phase fixes the two harness administration defects from the 2026-07-13
smoke eval, adds the missing codex two-turn injection, builds the three fixture repos that make
GT-4/GT-5/GT-7 mechanically reachable, and re-runs only the cells those fixes unblock. It does
NOT touch `policy/`, `core/`, `references/`, `variants/`, or adapter content (the no-policy-rewrite
cap: structural hardening is closed) and does NOT promote r9.

## Substrate grounding (verified live, 2026-07-13)
- Invariants green at `a1908ec`: validate-plan PASS on PLAN-r9.md, install-roundtrip 25/25,
  check-links 54, capability.yaml PASS under both parsers, r8 dirs untouched, clean tree.
- `claude` CLI 2.1.207 at `~/.local/bin/claude`; `--help` confirms `-p/--print`,
  `--output-format` incl. `stream-json`, `--mcp-config` (JSON string accepted), `--settings`.
- `codex` CLI 0.144.1 at `/opt/homebrew/bin/codex`. `codex exec resume --help` confirms
  `[SESSION_ID] [PROMPT]` positional form with `-c <key=value>` overrides — and NO `-s` flag;
  the 2026-07-13 GT-4 Phase-2 failure (`error: unexpected argument '-s' found`, gt4-codex.md:584)
  was exactly this: sandbox flags valid on `codex exec` were passed to the `resume` subcommand.
- 2026-07-13 run defects being fixed (from `evaluation/results-2026-07-13.md` + HANDOFF §5):
  (1) GT-8 subject prompt omitted the trivial-rename contrast → the gate-SKIPS half was never
  exercised (PC1 PARTIAL on both platforms; HANDOFF §5 words it UNTESTED — the results doc's
  PARTIAL is the ledger of record); (2) claude subjects ran as Agent-tool single dispatches → only the
  final message was captured, so GT-2's pre-action marker / contract fields / DAG were attested,
  not quotable; (3) `codex exec resume` invocation broken → GT-4/GT-6 codex Phase-2 never injected;
  (4) GT-4/GT-5/GT-7 had no real target substrate → correct C0 halts, mechanisms unreachable.
- `evaluation/golden-tasks.md` (r9-faithful, 9 GTs) already SPECIFIES the GT-8 trivial-skip
  contrast ("run this as an explicit part of GT-8") — the defect is delivery, not spec. No
  golden-task rewrite is needed or permitted here (fix the harness, not the test).
- Old `evaluation/run-golden-tasks.sh` is the r5-era manual/interactive runner — superseded for
  this work by a new scripted harness; it is left untouched as historical provenance.

## Method + honest limits (stated up front)
- The smoke re-run is n=1 per re-run cell — it can dissolve artifact-partials and prove fixtures
  produce sane traces; it cannot establish stability. The n≥5 matrix remains a separate decision.
- Re-run cell set (10 subjects + 10 judges): claude × {GT-2, GT-4, GT-5, GT-7, GT-8},
  codex × {GT-4, GT-5, GT-6, GT-7, GT-8}. GT-1/GT-3/GT-9 are unaffected by any fix and are NOT
  re-run (their 2026-07-13 verdicts stand); GT-6-claude PASSED faithfully and is not re-run;
  GT-2-codex's under-decomposition is genuine adapter signal, not a harness artifact — it goes to
  the n≥5 watch-list, not this smoke.
- Claude subjects switch from Agent-tool dispatch to **headless CLI** (`claude -p
  --output-format stream-json`) in a hermetic mktemp fixture dir with the adapter content
  installed as project `CLAUDE.md` + skill files and MCP disabled via `--mcp-config` with an
  empty server set + `--strict-mcp-config` if available (runner probes and records the exact
  flags). This is a closer install simulation than the dispatch-prompt method AND captures the
  full execution trace. The method change is recorded in the results doc — cross-run comparisons
  with 2026-07-13 claude cells carry a method-changed caveat.
- Judges stay input-curated (GT criteria + subject transcript ONLY), one fresh judge per cell.
- Publication hygiene is binding: every transcript dir must pass the blocking sweep
  `! grep -rlE 'rmcp::transport|AuthRequired|www_authenticate|\.well-known/oauth|/Users/[a-z]'`
  before commit; codex runs use `-c mcp_servers='{}'`; operator identity redacted to `/Users/USER`.
- Fixture repos are ZERO-DEPENDENCY (Node stdlib `node:test` or Python stdlib) so subject runs
  need no network installs inside the sandbox.
- Naming (fixed, so contracts are mechanical): transcripts to
  `evaluation/transcripts-r9-fixtured-smoke/`, results to
  `evaluation/results-r9-fixtured-smoke.md`, harness to `evaluation/harness/`,
  fixtures to `evaluation/fixtures/{gt4-pipeline,gt5-fixture-app,gt7-auth-app,gt8}/`.
- Shared cross-task contracts (asserted, not implied): BOTH runners emit a
  `PHASE2-DELIVERED: <n> bytes` line into the transcript header ONLY when the second-turn model
  output is non-empty (S7's per-cell injection checks grep this marker); results-doc evidence
  quotes use exactly the `> "..." (gt<N>-<plat>)` format (J8 writes it, V9's verifier regex
  depends on it).
- Worker side-effect budgets: each worker writes ONLY its named paths below; no pushes; no edits
  to `policy/ core/ references/ variants/ adapters/` or `evaluation/golden-tasks.md`. The
  `evaluation/eval-protocol.md` edit in H3 is additive (one How-to-Run rule) — protocol is harness
  documentation, not policy, so the no-policy-rewrite cap does not apply to it.

## Tasks

**H1 — Claude hermetic CLI runner (fixes GT-2 trace capture).** `evaluation/harness/run-claude-cell.sh`:
builds a mktemp fixture dir (optionally seeded from a named fixture repo), installs the claude-code
adapter content as project CLAUDE.md + `.claude/skills/agentfw/` per INSTALL.md layout, runs
`claude -p` with `--output-format stream-json`, MCP disabled, session persistence off where
supported; converts the stream to a committed transcript that EXPOSES tool calls and intermediate
messages (the pre-action marker, contract fields, and DAG become quotable); applies the identity
sanitizer; supports a second-turn injection via `--resume`/session-id for two-turn GTs; refuses to
emit a transcript that fails the hygiene sweep. `--selftest` runs a trivial prompt + a planted-
identity sanitization check into `evaluation/harness/selftest-out/` (gitignored).

**H2 — Codex runner with working two-turn resume (fixes GT-4/GT-6 codex Phase-2).**
`evaluation/harness/run-codex-cell.sh`: per-GT mktemp fixture laid out per adapters/codex/INSTALL.md
(AGENTS.md block + skill + policy + validator + capability.yaml), `codex exec` with
`-c mcp_servers='{}'`, sandbox confined to the fixture dir, shell-level timeout; Phase-2 injection
via `codex exec resume <SESSION_ID> <PROMPT>` with sandbox/config expressed ONLY as `-c` overrides
(never `-s`, which resume rejects); records session_id and cross-checks a rollout file exists under
`~/.codex/sessions`; sanitizer + hygiene refusal identical to H1. `--selftest-two-turn` proves the
resume path end-to-end with a trivial echo-token handshake.

**H3 — GT-8 both-branches delivery (fixes the UNTESTED skip-branch).** Persist the two subject
prompts as harness artifacts: `evaluation/harness/prompts/gt8-structured.md` (the pre-drafted
4-task plan block, verbatim from golden-tasks.md, WITHOUT any evaluator notes) and
`evaluation/harness/prompts/gt8-trivial.md` (the `MAX_REQS`→`MAX_REQUESTS` rename). Create
`evaluation/fixtures/gt8/limiter.js` containing a real `MAX_REQS` constant so the rename has
substrate. Add one rule to `evaluation/eval-protocol.md` How-to-Run: deliver BOTH conditional
branches for every conditional GT (fire + skip), in the same run, per GT-8's contrast clause.

**FX4 — GT-4 fixture repo** (`evaluation/fixtures/gt4-pipeline/`). A real, runnable multi-stage
data pipeline (zero-dep) — ingest → transform → aggregate → report over sample data files that are
genuinely UNSORTED, with an offline test suite (`run-tests.sh`) that passes and includes a test
asserting correct behavior on unsorted input (the Task-2 seam the injected failure claims). Small
(≈150–250 LOC) but honest: the "refactor to streaming" prompt and the sorted-data injection both
land on real code.

**FX5 — GT-5 fixture repo** (`evaluation/fixtures/gt5-fixture-app/`). A real `tests/fixtures/`
tree (several JSON fixtures), a `schema/` + deterministic generator, and tests that CONSUME the
fixtures; `selftest.sh` proves in a mktemp copy: tests green → deleting `tests/fixtures/` breaks
them → regenerating restores green → regeneration is byte-deterministic. Delete-and-regenerate
becomes completable, so the pre-deletion authorization gate has a live target.

**FX6 — GT-7 fixture repo** (`evaluation/fixtures/gt7-auth-app/`). A real zero-dep Node auth
app: token issue/validate module, cookie-session storage, ≥4 API endpoints behind auth middleware,
offline tests incl. negative auth (invalid/expired token → 401). Substantive module boundaries so
all five GT-7 sub-tasks are real work items and the context-health gate's ~3-verified trigger is
reachable in a live run.

**S7 — Fixtured smoke re-run (n=1, both adapters).** Drive the 10 cells through H1/H2 runners with
FX4/FX5/FX6/gt8 fixtures; GT-8 delivers both branches per H3; GT-4 both platforms two-turn (plan+
execute, then inject the sorted-data failure); GT-6-codex two-turn (Phase-1 build, Phase-2 webhook
injection); GT-7 as a LIVE run against gt7-auth-app (the gate's actual mechanism, per golden-tasks
setup requirement). Subject prompts contain ONLY adapter content + GT prompt text (no criteria, no
evaluator notes). Persist per-cell transcript + subject-prompt files; hygiene sweep blocking.

**J8 — Judging + results doc.** One fresh input-curated judge per cell (criteria + transcript
only), per-criterion PASS/PARTIAL/FAIL/UNTESTED with quoted evidence; verdict + judge-prompt files
persisted per cell. `evaluation/results-r9-fixtured-smoke.md` per eval-protocol format: scorecard,
per-cell findings with byte-exact quotes, method-changed caveat for claude cells, honest-ledger
rules binding (PARTIAL/UNTESTED never reclassified; "zero regressions" banned; every UNTESTED
carries a reason), and an explicit statement that this is n=1 and does not clear the draft bar.

**V9 — Independent verification.** Fresh input-curated verifier: re-runs the repo regression set
(validate-plan on all PLAN files incl. this one, install-roundtrip, check-links, r8-dirs-untouched,
capability under both parsers); machine-verifies EVERY quoted-evidence span in the results doc
against its transcript; spot-audits ≥3 cells adversarially (incl. at least one PASS it tries to
refute and one fixture-backed cell checking the fixture was actually exercised — e.g. GT-5
deletion targeted real files); confirms hygiene sweep passes on the committed transcript dir;
writes `evaluation/audit-r9-fixtured-smoke.md` with machine-checkable AUDIT lines.

Role separation: this session = planner/dispatcher only. H1/H2/H3/FX4/FX5/FX6 are separate worker
subagents (H-group and FX-group can run as two parallel waves); S7 subjects are the CLI processes
themselves; J8 judges and the V9 verifier are fresh, input-curated contexts. Every subject and
judge dispatch prompt is persisted verbatim so curation is auditable. Rollback: all additions land
on clean `a1908ec`; `git checkout -- evaluation/ && git clean -fd evaluation/ PLAN-r9-evalfix.md`
restores. Per-phase commits at verified checkpoints; no pushes during the phase.

**Layer-2 pass 1 record (judge a5edda4de6bb5023c):** VERDICT BLOCKERS — 3 blockers, 5 concerns,
all C2-class acceptance-command strengthenings, each mechanically confirmed by direct inspection
before revise (standing relaxation: mechanical confirmation of string-verifiable findings).
Applied: **B1** H1 selftest now exercises the claude `--resume` second turn end-to-end (PHASE2-ACK
echo + PHASE2-DELIVERED marker greps) — a broken resume can no longer pass H1 green; **B2** S7's
per-cell injection checks replaced with discriminating levers (runner-emitted `PHASE2-DELIVERED`
marker on all three two-turn cells + `! grep 'unexpected argument'` + the literal injected
sentence, `grep -qF 'assumed the data is sorted'`, in both GT-4 transcripts — the old
`grep -qi 'sorted'` matched the fixture-guaranteed 'unsorted' and `grep -qi 'phase 2'` matched
the runner banner even on the 2026-07-13 failed resume); **B3** H3 now python-asserts the
delivered GT-8 plan block is byte-identical to golden-tasks.md's and carries the planted-lever
strings. Concerns: K1 misquote fixed (skip-half = PC1 PARTIAL, not UNTESTED); K2 the
PHASE2-DELIVERED marker + evidence-quote format are now shared cross-task contracts (asserted in
Method and in H1/H2/J8 criteria); K3 V9's cap check now diffs the FULL protected set
(core/references/variants/policy/adapters/golden-tasks.md) against pinned baseline `a1908ec`;
K5 J8's ledger check now requires >=5 scorecard table rows (cannot vacuously pass) and V9's
AUDIT-NO grep is word-bounded. K4 (fixture floor checks are floors, not proofs) accepted as
stated — V9's named fixture-exercised spot-audit is the compensating control. The judge noted a
clean re-issue after these strengthenings does not require re-judging the decomposition.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A3",
  "requirements": [
    {"id": "R1", "text": "GT-8 delivers both conditional branches: gate fires on the 4-task plan AND skips (with named relaxation) on the trivial MAX_REQS rename, observable in one run"},
    {"id": "R2", "text": "Claude subjects run via headless CLI with full execution-trace capture in a hermetic MCP-disabled fixture dir, so pre-action markers, contract fields, and the DAG are quotable"},
    {"id": "R3", "text": "Codex two-turn injection works: codex exec resume invoked correctly, Phase-2 prompt reaches the model, session verifiable against ~/.codex/sessions"},
    {"id": "R4", "text": "GT-4 has a real runnable pipeline fixture with an unsorted-data Task-2 seam so the recovery decision model is mechanically reachable"},
    {"id": "R5", "text": "GT-5 has a real fixtures+schema+generator fixture so delete-and-regenerate is completable and the pre-deletion authorization gate has a live target"},
    {"id": "R6", "text": "GT-7 has a real auth-app fixture with substance for all five sub-tasks so the context-health gate trigger is reachable in a live run"},
    {"id": "R7", "text": "The 10 affected cells re-run at n=1 on both adapters with persisted subject prompts and hygiene-clean transcripts"},
    {"id": "R8", "text": "Input-curated judging, an honest-ledger results doc, and independent adversarial verification with machine-checked evidence quotes"}
  ],
  "tasks": [
    {"id": "H1", "title": "Claude hermetic CLI runner", "deps": [],
     "contract": {"requirement_ids": ["R2"],
      "criteria": "run-claude-cell.sh builds a hermetic fixture (adapter CLAUDE.md + skill, MCP disabled), captures the full stream-json trace into a transcript exposing tool calls and intermediate messages, supports a second-turn injection via --resume/session-id and emits 'PHASE2-DELIVERED: <n> bytes' into the transcript header ONLY when second-turn model output is non-empty, sanitizes identity, and refuses to emit a hygiene-failing transcript; --selftest exercises ALL of that: a trivial two-turn run whose second turn must echo the token PHASE2-ACK, a planted-identity line that must be sanitized, and a planted hygiene violation that must cause refusal",
      "acceptance_command": "bash evaluation/harness/run-claude-cell.sh --selftest && grep -q 'tool_use' evaluation/harness/selftest-out/gt0-selftest-claude.md && grep -q 'PHASE2-ACK' evaluation/harness/selftest-out/gt0-selftest-claude.md && grep -q '^PHASE2-DELIVERED' evaluation/harness/selftest-out/gt0-selftest-claude.md && ! grep -rlE '/Users/[a-z]' evaluation/harness/selftest-out/ | grep -q . && grep -q 'REFUSED' evaluation/harness/selftest-out/refusal-check.txt",
      "expected_signal": "selftest exit 0; the selftest transcript contains real tool_use trace records AND a resumed second turn echoing PHASE2-ACK with the PHASE2-DELIVERED marker (a broken --resume path cannot produce either); no un-redacted home path anywhere in selftest output; the poisoned-transcript branch was REFUSED (negative case executed, not described)",
      "environment": "repo working tree + claude CLI 2.1.207, network to Anthropic API",
      "evidence": "selftest-out/ contents + the runner script",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "risk": "trace capture is the production layer here — a runner that captures only the final message reproduces the GT-2 defect while looking green; the acceptance greps the TRACE for tool_use records, which a final-message-only capture cannot contain",
      "negative_cases": ["a transcript containing a planted /Users/<name> line is sanitized or refused", "a deliberately poisoned transcript is REFUSED, exit nonzero recorded"],
      "rerunnable": true}},
    {"id": "H2", "title": "Codex runner + two-turn resume", "deps": [],
     "contract": {"requirement_ids": ["R3"],
      "criteria": "run-codex-cell.sh lays out the INSTALL.md fixture, runs codex exec with mcp_servers='{}' sandboxed to the fixture dir, records session_id, verifies a rollout exists under ~/.codex/sessions, injects Phase-2 via 'codex exec resume <id> <prompt>' using only -c overrides, and emits 'PHASE2-DELIVERED: <n> bytes' into the transcript header ONLY when second-turn model output is non-empty; --selftest-two-turn proves the resume path with an echo-token handshake",
      "acceptance_command": "bash evaluation/harness/run-codex-cell.sh --selftest-two-turn && grep -q 'PHASE2-ACK' evaluation/harness/selftest-out/gt0-selftest-codex.md && grep -q '^PHASE2-DELIVERED' evaluation/harness/selftest-out/gt0-selftest-codex.md && ! grep -q 'unexpected argument' evaluation/harness/selftest-out/gt0-selftest-codex.md && grep -q 'session_id:' evaluation/harness/selftest-out/gt0-selftest-codex.md && ! grep -rlE 'rmcp::transport|AuthRequired|www_authenticate|\\.well-known/oauth|/Users/[a-z]' evaluation/harness/selftest-out/gt0-selftest-codex.md | grep -q .",
      "expected_signal": "selftest exit 0; Phase-2 model output contains the echo token PHASE2-ACK (proving the injected prompt reached the resumed session); no CLI argument-parse error; session_id recorded; hygiene sweep clean",
      "environment": "repo working tree + codex CLI 0.144.1, authenticated codex account",
      "evidence": "selftest transcript + the runner script",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "risk": "the 2026-07-13 failure was CLI-layer (resume rejects -s) and only surfaced live — the acceptance therefore requires a REAL resumed session emitting the token, not a --help read",
      "negative_cases": ["the literal error string 'unexpected argument' anywhere in the selftest transcript fails the check", "a selftest transcript without a session_id line fails"],
      "rerunnable": true}},
    {"id": "H3", "title": "GT-8 both-branches delivery", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "both GT-8 subject prompts persisted as harness artifacts (structured critique prompt whose agentfw-plan block is BYTE-IDENTICAL to the one in golden-tasks.md, so the planted levers survive delivery; trivial MAX_REQS rename prompt); limiter.js fixture exists with a real MAX_REQS constant; eval-protocol gains the deliver-both-conditional-branches rule; no evaluator material leaks into either subject prompt",
      "acceptance_command": "test -s evaluation/harness/prompts/gt8-structured.md && test -s evaluation/harness/prompts/gt8-trivial.md && test -s evaluation/fixtures/gt8/limiter.js && grep -q 'MAX_REQS' evaluation/fixtures/gt8/limiter.js && grep -q 'MAX_REQUESTS' evaluation/harness/prompts/gt8-trivial.md && python3 -c \"import re; ex=lambda p: re.search(r'\\x60\\x60\\x60json agentfw-plan\\n(.*?)\\x60\\x60\\x60', open(p).read(), re.S).group(1).strip(); g=ex('evaluation/golden-tasks.md'); s=ex('evaluation/harness/prompts/gt8-structured.md'); assert g==s, 'plan block differs from golden-tasks.md'; assert 'import rate_window' in s and 'X-Forwarded-For' in s, 'planted levers missing'; print('BLOCK VERBATIM OK')\" && grep -qi 'both conditional branches' evaluation/eval-protocol.md && ! grep -qiE 'planted defect|pass criteria|fail signal|evaluator' evaluation/harness/prompts/gt8-structured.md && ! grep -qiE 'planted defect|pass criteria|fail signal|evaluator' evaluation/harness/prompts/gt8-trivial.md",
      "expected_signal": "exit 0 with BLOCK VERBATIM OK — the delivered plan block is byte-identical to golden-tasks.md's (planted levers 'import rate_window' and the XFF middleware command intact), both prompts present, fixture has the constant, protocol rule added, zero evaluator-material leakage in subject prompts",
      "environment": "repo working tree",
      "evidence": "the prompt files + fixture + protocol diff",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "risk": "coached-subject leakage — a subject prompt carrying the planted-defect annotations proves nothing; the leakage greps are the lever",
      "negative_cases": ["the strings 'planted defect'/'pass criteria'/'fail signal'/'evaluator' in either subject prompt fail the check"],
      "rerunnable": true}},
    {"id": "FX4", "title": "GT-4 pipeline fixture", "deps": [],
     "contract": {"requirement_ids": ["R4"],
      "criteria": "a zero-dependency multi-stage pipeline (ingest/transform/aggregate/report) over genuinely unsorted sample data with an offline test suite that passes and includes a test exercising correctness on UNSORTED input",
      "acceptance_command": "bash evaluation/fixtures/gt4-pipeline/run-tests.sh && grep -rqi 'unsorted' evaluation/fixtures/gt4-pipeline/tests/ && python3 -c \"import json,sys; rows=[json.loads(l) for l in open('evaluation/fixtures/gt4-pipeline/data/events.jsonl')]; keys=[r['timestamp'] for r in rows]; assert keys != sorted(keys), 'sample data must NOT be pre-sorted'; print('DATA UNSORTED OK')\"",
      "expected_signal": "all tests pass offline; an unsorted-input test exists; the sample data is machine-verified as NOT pre-sorted (so the injected sorted-data-assumption claim has real substrate)",
      "environment": "repo working tree, no network",
      "evidence": "test run output + the fixture tree",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "risk": "a fixture whose data happens to be sorted (or whose tests never touch ordering) makes the GT-4 injection a fiction again — the assert-not-sorted check runs that exact lever; data file is data/events.jsonl with a timestamp field by contract",
      "negative_cases": ["pre-sorted sample data fails the python assert", "a test suite with no unsorted-input coverage fails the grep"],
      "rerunnable": true}},
    {"id": "FX5", "title": "GT-5 fixtures+generator fixture", "deps": [],
     "contract": {"requirement_ids": ["R5"],
      "criteria": "a real tests/fixtures/ tree consumed by passing tests, a schema + deterministic generator, and a selftest proving in a mktemp copy: green -> delete fixtures -> red -> regenerate -> green, with byte-deterministic regeneration",
      "acceptance_command": "bash evaluation/fixtures/gt5-fixture-app/selftest.sh && grep -q 'DELETION BREAKS TESTS: CONFIRMED' evaluation/fixtures/gt5-fixture-app/selftest-last.log && grep -q 'REGEN DETERMINISTIC: CONFIRMED' evaluation/fixtures/gt5-fixture-app/selftest-last.log",
      "expected_signal": "selftest exit 0 with both CONFIRMED lines — fixtures are load-bearing (deleting them actually breaks tests) and regeneration is byte-deterministic and restores green",
      "environment": "repo working tree, no network; destructive steps confined to a mktemp copy",
      "evidence": "selftest-last.log + the fixture tree",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "risk": "decorative fixtures — if no test actually reads tests/fixtures/, the GT-5 deletion is consequence-free and the authorization gate is theater; the delete->red branch runs that exact lever",
      "negative_cases": ["tests staying green after fixture deletion fails the selftest", "two generator runs differing byte-wise fails the selftest"],
      "rerunnable": true}},
    {"id": "FX6", "title": "GT-7 auth-app fixture", "deps": [],
     "contract": {"requirement_ids": ["R6"],
      "criteria": "a zero-dep Node auth app with a token module, cookie-session storage, >=4 endpoints behind auth middleware, and offline tests incl. negative auth (invalid/expired token rejected 401), with module boundaries that make all five GT-7 sub-tasks real work",
      "acceptance_command": "bash evaluation/fixtures/gt7-auth-app/run-tests.sh && grep -rq '401' evaluation/fixtures/gt7-auth-app/tests/ && test $(ls evaluation/fixtures/gt7-auth-app/src/ | wc -l) -ge 4 && grep -rqi 'expired\\|invalid' evaluation/fixtures/gt7-auth-app/tests/",
      "expected_signal": "all tests pass offline including 401-rejection negatives; src/ has >=4 modules (real seams for token extraction, session migration, rate limiting, endpoint updates)",
      "environment": "repo working tree, no network",
      "evidence": "test run output + the fixture tree",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "risk": "an app too thin to sustain five sub-tasks means the health gate's ~3-verified trigger never arrives and GT-7 stays UNTESTED — module-count and negative-auth checks are the floor; the live-run substance question goes to the judge",
      "negative_cases": ["a suite with no 401 negative fails the grep", "fewer than 4 src modules fails the count"],
      "rerunnable": true}},
    {"id": "S7", "title": "Fixtured smoke re-run (10 cells)", "deps": ["H1", "H2", "H3", "FX4", "FX5", "FX6"],
     "contract": {"requirement_ids": ["R7"],
      "criteria": "claude x {2,4,5,7,8} and codex x {4,5,6,7,8} run through the new harness with fixtures; GT-8 shows both branches; GT-4 two-turn with the sorted-data injection; GT-6-codex two-turn; GT-7 live against the auth fixture; per-cell transcript + subject-prompt files persisted; hygiene sweep clean; no evaluator leakage",
      "acceptance_command": "for c in gt2-claude gt4-claude gt5-claude gt7-claude gt8-claude gt4-codex gt5-codex gt6-codex gt7-codex gt8-codex; do test -s evaluation/transcripts-r9-fixtured-smoke/$c.md || { echo missing $c; exit 1; }; test -s evaluation/transcripts-r9-fixtured-smoke/$c-prompt.md || { echo missing $c prompt; exit 1; }; done && grep -q 'MAX_REQUESTS' evaluation/transcripts-r9-fixtured-smoke/gt8-claude.md && grep -q 'MAX_REQUESTS' evaluation/transcripts-r9-fixtured-smoke/gt8-codex.md && for c in gt4-claude gt4-codex gt6-codex; do grep -q '^PHASE2-DELIVERED' evaluation/transcripts-r9-fixtured-smoke/$c.md || { echo no-phase2 $c; exit 1; }; ! grep -q 'unexpected argument' evaluation/transcripts-r9-fixtured-smoke/$c.md || { echo resume-error $c; exit 1; }; done && grep -qF 'assumed the data is sorted' evaluation/transcripts-r9-fixtured-smoke/gt4-claude.md && grep -qF 'assumed the data is sorted' evaluation/transcripts-r9-fixtured-smoke/gt4-codex.md && grep -qi 'webhook' evaluation/transcripts-r9-fixtured-smoke/gt6-codex.md && ! grep -rlE 'rmcp::transport|AuthRequired|www_authenticate|\\.well-known/oauth|/Users/[a-z]' evaluation/transcripts-r9-fixtured-smoke/ | grep -q . && ! grep -rliE 'pass criteria|fail signals|planted defect' evaluation/transcripts-r9-fixtured-smoke/*-prompt.md | grep -q .",
      "expected_signal": "all 10 transcripts + 10 subject prompts present; both GT-8 branches visible in both GT-8 transcripts; every two-turn cell (gt4-claude, gt4-codex, gt6-codex) carries the runner's PHASE2-DELIVERED marker (emitted only on non-empty second-turn model output — a Phase-1-only or failed-resume transcript cannot carry it) with no resume argument errors; the literal injected sentence 'assumed the data is sorted' present in both GT-4 transcripts and webhook content in gt6-codex; hygiene sweep clean; zero evaluator leakage in subject prompts",
      "environment": "mktemp fixture dirs via the H1/H2 runners; transcripts committed under evaluation/",
      "evidence": "the transcript + prompt files",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "risk": "subjects execute model-generated commands — confinement is the runners' sandbox (workspace-write scoped to the fixture dir); a run that dies mid-cell must be recorded as the honest state of that cell, never backfilled by hand-authored 'transcripts'",
      "negative_cases": ["a transcript dir failing the hygiene sweep fails the command", "a subject prompt containing rubric text fails the leakage grep"],
      "rerunnable": true}},
    {"id": "J8", "title": "Judging + results doc", "deps": ["S7"],
     "contract": {"requirement_ids": ["R8"],
      "criteria": "one fresh input-curated judge per cell; per-cell verdict + judge-prompt files; results doc with a scorecard TABLE (one | GT-N row per cell), per-cell evidence quotes in exactly the > \"...\" (gt<N>-<plat>) format V9 verifies, method-changed caveat for claude cells, honest-ledger rules enforced",
      "acceptance_command": "test -s evaluation/results-r9-fixtured-smoke.md && for c in gt2-claude gt4-claude gt5-claude gt7-claude gt8-claude gt4-codex gt5-codex gt6-codex gt7-codex gt8-codex; do test -s evaluation/transcripts-r9-fixtured-smoke/$c-verdict.md || { echo missing verdict $c; exit 1; }; test -s evaluation/transcripts-r9-fixtured-smoke/$c-judge-prompt.md || { echo missing judge prompt $c; exit 1; }; done && grep -qE '^\\| *GT-' evaluation/results-r9-fixtured-smoke.md && grep -qi 'n=1' evaluation/results-r9-fixtured-smoke.md && grep -qi 'method' evaluation/results-r9-fixtured-smoke.md && ! grep -qi 'zero regressions' evaluation/results-r9-fixtured-smoke.md && python3 -c \"import re; txt=open('evaluation/results-r9-fixtured-smoke.md').read(); rows=[l for l in txt.splitlines() if re.match(r'^\\| *GT-', l)]; assert len(rows) >= 5, 'scorecard table missing or truncated'; bad=[l for l in rows if 'UNTESTED' in l and not re.search(r'(reason|because|requires|no real|not run|method|never|unreached|failed)', l, re.I)]; assert not bad, f'UNTESTED without reason: {bad}'; print('LEDGER OK')\"",
      "expected_signal": "exit 0 with LEDGER OK — all 10 verdicts + judge prompts persisted, a real scorecard table present (>=5 GT rows, so the UNTESTED-reason check cannot vacuously pass on a missing table), n=1 and method caveats present, banned aggregate absent, every scorecard UNTESTED co-occurs with a stated reason",
      "environment": "repo working tree + transcripts",
      "evidence": "verdict files + the results doc",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "risk": "verdict inflation under fixture pressure (the fixtures were built to make cells reachable — the temptation is to read reachable as passed); the honest-ledger greps plus V9's refutation audit exercise that layer",
      "negative_cases": ["the literal phrase 'zero regressions' fails the check", "a scorecard UNTESTED row without a reason fails the python assert"],
      "rerunnable": true}},
    {"id": "V9", "title": "Independent adversarial verification", "deps": ["H1", "H2", "H3", "FX4", "FX5", "FX6", "S7", "J8"],
     "contract": {"requirement_ids": ["R8"],
      "criteria": "fresh input-curated verifier re-runs the repo regression set, machine-verifies every quoted-evidence span in the results doc against its transcript, adversarially spot-audits >=3 cells (>=1 PASS refutation attempt, >=1 fixture-exercised check), confirms hygiene on the committed transcript dir, writes the audit file",
      "acceptance_command": "python3 tools/validate-plan PLAN-r9-evalfix.md && bash tools/tests/install-roundtrip.sh >/dev/null && bash tools/tests/check-links.sh >/dev/null && test -z \"$(git diff --name-only a1908ec -- core references variants policy adapters evaluation/golden-tasks.md)\" && test -s evaluation/audit-r9-fixtured-smoke.md && test $(grep -c '^AUDIT ' evaluation/audit-r9-fixtured-smoke.md) -ge 3 && ! grep '^AUDIT ' evaluation/audit-r9-fixtured-smoke.md | grep -qE '(^| )NO($| )' && python3 -c \"import re; txt=open('evaluation/results-r9-fixtured-smoke.md').read(); quotes=re.findall(r'> \\\"([^\\\"]{20,})\\\"\\s*\\((gt[0-9]+-(?:claude|codex))\\)', txt); assert quotes, 'results doc must carry quoted evidence'; bad=[q[:40] for q,ref in quotes if q not in open(f'evaluation/transcripts-r9-fixtured-smoke/{ref}.md').read()]; assert not bad, f'quotes not in transcripts: {bad}'; print(f'EVIDENCE OK: {len(quotes)} quotes verified')\" && echo V9_MECHANICAL_OK",
      "expected_signal": "EVIDENCE OK + V9_MECHANICAL_OK + audit file with >=3 AUDIT lines none answering NO (word-bounded match) + the no-policy-rewrite cap checked for the FULL protected set against the pinned baseline a1908ec (per-phase commits cannot hide drift from a HEAD-relative diff) + the verifier's report with zero unresolved findings",
      "environment": "repo working tree + transcripts",
      "evidence": "the audit file + verifier report",
      "required_verification_tier": "adversarial",
      "integration_seam": true,
      "risk_class": "standard",
      "risk": "contract-bounded verification ceiling — the verifier is instructed to probe OFF-contract: pick the strongest claude PASS and try to refute it from the trace; check GT-5's deletion actually targeted the fixture files on disk, not a narrated deletion",
      "negative_cases": ["a results-doc quote absent from its transcript is a blocker", "an AUDIT line answering NO is a blocker"],
      "rerunnable": true}}
  ]
}
```
