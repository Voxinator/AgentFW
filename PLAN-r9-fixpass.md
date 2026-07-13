# PLAN-r9-fixpass — post-review hardening of the r9 draft

Status: fix pass over the r9 draft built per PLAN-r9.md. Source of requirements: GPT 5.6 Sol's
adversarial review (2026-07-11), each finding independently re-reproduced against this tree before
acceptance (empty-A2 plan PASSed, unknown R99 PASSed, `agentfw-*.md` uninstall glob confirmed at
tools/agentfw-install:316, `Bash(cat:*)` allow confirmed in settings.example.json, metadata bootstrap →
r8 bootstrap.md confirmed, universal-judge clause confirmed at policy/acceptance-contract.md:33-34,
overbroad ChatGPT claim confirmed at profiles/chatgpt.md:5).

## Requirements (accepted findings; Sol's numbering in parens)

- **FR1** (Sol 1) The installed skill must be able to run the validator without a repo checkout: installer copies `tools/validate-plan` into the installed skill (`$CLAUDE_DIR/skills/agentfw/tools/validate-plan`, executable); both SKILL.md files resolve it skill-relative with repo-checkout fallback; Codex INSTALL.md adds the copy step. Single source stays `tools/validate-plan` — no forked copies in the repo.
- **FR2** (Sol 2) Validator hardening, all mechanical: reject (a) empty `requirements` or empty `tasks` when assurance ≥ A2; (b) `requirement_ids` referencing undeclared requirements; (c) duplicate requirement ids; (d) malformed requirement records (missing/empty id or text); (e) missing `rerunnable` on any contract when assurance ≥ A2. Defect-class keyword set extends to: contract, cover, cycl, negative, assurance, empty, duplicate (documented in policy/plan-critique.md, which is the schema of record — PLAN-r9.md's S5 is historical and must not be edited). PLAN-r9.md, PLAN-r9-fixpass.md, and plan-good.md must still PASS (update plan-good.md if it lacks newly required fields).
- **FR3** (Sol 3) Uninstall removes ONLY files it installed: installer writes a manifest at install time (`$CLAUDE_DIR/skills/agentfw/.install-manifest`, one installed path per line); uninstall removes exactly manifest entries (fallback for manifest-less legacy installs: the three known shipped agent filenames, never a glob). Hostile roundtrip fixture: seeded `agentfw-custom.md` survives uninstall.
- **FR4** (Sol 4) settings.example.json models effect classification, not executable-name allowlisting: remove global `Bash(cat:*)`, `Bash(find:*)`, `Bash(grep:*)`, `Bash(rg:*)`, `Bash(ls:*)`, `Bash(wc:*)` allows (Read/Glob/Grep tool rules already cover read effects and honor Read denies); move test runners (`npm test`, `pytest`, etc.) from allow to ask with a comment that they execute repository-controlled code; keep git read-only allows and all denies; add a comment block naming the limitation honestly: command-name allowlists cannot express the effects taxonomy — secrets isolation and egress control require Read-deny rules plus hooks/sandboxing, and any `Bash(<dumper>:*)` allow reopens what Read denies close.
- **FR5** (Sol 5) metadata.json must not route to the r8 installer as r9's bootstrap: `bootstrap` points at the r8 file explicitly labeled (`bootstrap_r8`) and a new `install` field points at `adapters/<platform>/INSTALL.md`; bootstrap.md itself gains a one-line r9 notice at top pointing draft users to adapters/ (no other r8 content edited).
- **FR6** (Sol 6) Resolve the producer/independent contradiction: acceptance-contract.md defines terminal states `verified_producer` / `verified_independent` / `verified_adversarial` and `required_verification_tier` derived from assurance + risk (A0/A1 → producer evidence suffices; A2 seams and A3+ → independent; A4/security/destructive → adversarial); the universal independent-judge clause is scoped to the independent/adversarial tiers.
- **FR7** (Sol 11) Evidence classes replace the single mechanical floor for non-code work: behavioral-machine, structural-artifact, source-grounded, expert-judgment, human-authorization — with an assurance-tier combination table (e.g., research at A2 = structural + source-grounded + independent expert judgment; grep never validates substance).
- **FR8** (Sol 7a, scoped) profiles/chatgpt.md → profiles/chatgpt-projects.md, claims scoped to standard ChatGPT/Projects; explicit note that **ChatGPT Work** is a different surface with hosted subagents/skills (cite the learn.chatgpt.com subagents doc) and is the designated r9.1 adapter candidate AFTER the two shipped adapters pass evals (Adapter Sprawl rule). All references (README, metadata profiles array, any policy/adapter index) updated — no dangling links.
- **FR9** (Sol 8) Capability schema splits platform availability from installation activation: spec adds `available` / `configured` / optional `activation_probe` (+ `required_for` tiers); both instances migrate (`value` → `available`; `configured` set honestly — claude-code deterministic_permissions `configured: unknown` with probe = agentfw-install status settings check; persistent_state downgraded to partial per the no-atomic-task-store point); `agentfw-install status` runs the cheap probes it can and reports configured state; assurance gating language consults ACTIVE state.
- **FR10** (Sol 9, narrowed by us) A3 escalator recalibrated: "autonomous multi-file change" alone no longer escalates; escalation requires autonomy PLUS material side effects, unclear integration seams, elevated defect-escape probability, or absence of rapid human review. A routine reversible multi-file refactor with strong tests is A2. Applied in assurance-model.md, core.md, and both bootloaders if they carry the escalator list (byte caps still hold).
- **FR11** (Sol 10, surgical; + our verification lesson) (a) Guided profiles may compress the A0 marker to a single short clause — never silent; adapters keep full markers; recorded as a policy line in core.md's marker section. (b) Verifier hardening: agentfw-verifier.md and agentfw-plan-critic.md gain a standing off-contract instruction — after re-executing the contracts, attempt at least 2 hostile probes the contracts did not anticipate (empty/duplicate/hostile inputs, seeded user content, bypass paths) and report them; policy/plan-critique.md notes contract-bounded verification has a ceiling.

## Substrate grounding
All findings re-reproduced live (header). Current tree: r9 draft complete, T1–T6 green as of last
verification; `tools/validate-plan` PASSes PLAN-r9.md (16 req / 6 tasks / A3). Roundtrip 5/5.
check-links 47 PASS. Bootloaders: CLAUDE-block.md 2,230 B; codex AGENTS.md 2,401 B (cap 2,500).

## Tasks — file ownership is disjoint

**FA** — tools/agentfw-install, tools/tests/install-roundtrip.sh, adapters/claude-code/{settings.example.json,
CLAUDE-block.md, SKILL (skills/agentfw/SKILL.md), INSTALL.md, UPGRADE.md, UNINSTALL.md,
agents/agentfw-verifier.md, agents/agentfw-plan-critic.md}. Covers FR1(claude side), FR3, FR4, FR9(status
probes), FR10(bootloader), FR11b(agents).
**FB** — tools/validate-plan, tools/fixtures/* (new: plan-bad-empty.md, plan-bad-unknown-ref.md,
plan-bad-duplicate-id.md; update plan-good.md if needed), policy/plan-critique.md. Covers FR2, FR11b(policy note).
**FC** — policy/{core.md, assurance-model.md, acceptance-contract.md, capability-contract.md}. Covers FR6,
FR7, FR9(spec), FR10(policy), FR11a.
**FD** — profiles/* (rename + rescope), adapters/codex/{INSTALL.md, skills/agentfw/SKILL.md, capability.yaml,
AGENTS.md if escalator listed}, adapters/claude-code/capability.yaml, metadata.json, bootstrap.md (one-line
notice only), CHANGELOG.md, README.md. Covers FR1(codex side), FR5, FR8, FR9(instances), FR10(codex bootloader).
**FV** — fresh input-curated adversarial verifier: re-runs every FA–FD acceptance command, Sol's four original
probes (all must now fail-safe), the full PLAN-r9.md T1–T6 regression commands, and ≥2 off-contract probes of
its own devising.

Role separation: planner (this session) dispatches; FB/FC/FD run in parallel on disjoint files; FA runs after
FB (FA's roundtrip executes FB-owned validator/fixtures — serialized to avoid mid-edit flakes); FV is a fresh
verifier. **Rollback (corrected by Layer-2 pass 1):** the r9 draft is UNCOMMITTED atop 90f3e7e, so git-based
rollback would destroy the draft, not the fix pass. Before first dispatch the planner snapshots the baseline:
`tar -czf <scratchpad>/r9-prefixpass-baseline.tgz PLAN-r9.md PLAN-r9-fixpass.md policy adapters profiles
tools README.md CHANGELOG.md metadata.json bootstrap.md` — restore = extract over the tree. No history
rewriting, no pushes, no deletions of r8 content (bootstrap.md gets a bounded ≤2-line-added notice, asserted
by numstat in FD).

**Layer-2 pass 1 record (judge ae99b6f45f3b4ad9d):** VERDICT BLOCKERS — 5 blockers, 6 concerns, all quoting
string-verifiable plan/tree text, confirmed by direct inspection (relaxation: mechanical confirmation in lieu
of a second judge; C2/C3/C4 ⇒ local revise). Applied: (1) baseline snapshot + corrected rollback above;
(2) FV runs PLAN-r9.md T4's regression greps with the path substituted to profiles/chatgpt-projects.md —
the rename makes the original T4 path an expected-fail, stated in FV's contract; (3) order-robust escalator
negative greps added at the sites where the escalator actually lives (assurance-model.md via FC, both
bootloaders via FA/FD) — the core.md grep alone was vacuous; (4) FC pins the old universal-judge sentence
with a negative grep so FR6's contradiction cannot survive rewording; (5) FR2 sub-classes (d)/(e) get their
own hostile fixtures (malformed-req, no-rerunnable) in FB's loop. Concerns folded: FA greps the roundtrip
output for the specific new PASS lines; FD's metadata assert requires install→adapters/ + bootstrap_r8
labeling + bootstrap.md numstat bound; per-key available/configured conformance loops on both capability
instances; FC greps all five evidence-class names; FV's command chains the rerunnable FA/FB positives and
its criteria gain a substance-review line.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A3",
  "requirements": [
    {"id": "FR1", "text": "Validator ships with the installed skill on both platforms; skill-relative resolution"},
    {"id": "FR2", "text": "Validator rejects empty A2+ plans, unknown requirement refs, duplicate/malformed records, missing rerunnable at A2+"},
    {"id": "FR3", "text": "Manifest-based uninstall removes only installed files; user agentfw-* files survive"},
    {"id": "FR4", "text": "Settings example models effect classification; no global file-dumper or test-runner allows; honest limitation note"},
    {"id": "FR5", "text": "metadata/bootstrap routing no longer sends r9 users to the r8 installer"},
    {"id": "FR6", "text": "Tiered verified terminal states resolve the producer/independent contradiction"},
    {"id": "FR7", "text": "Five evidence classes with assurance-tier combinations for non-code work"},
    {"id": "FR8", "text": "ChatGPT profile rescoped to Projects; Work surface acknowledged as r9.1 adapter candidate; no dangling refs"},
    {"id": "FR9", "text": "Capability schema and instances split available from configured with activation probes"},
    {"id": "FR10", "text": "A3 escalator narrowed: autonomy alone no longer escalates multi-file work"},
    {"id": "FR11", "text": "A0 marker compression for guided profiles; verifiers gain standing off-contract hostile-probe instruction"}
  ],
  "tasks": [
    {"id": "FA", "title": "Installer, settings, hostile roundtrip", "deps": ["FB"],
     "contract": {"requirement_ids": ["FR1","FR3","FR4","FR9","FR10","FR11"],
      "criteria": "manifest-based uninstall; validator packaged into sandbox installs and EXECUTED there by the roundtrip; settings example rewritten with honest limitation note; status reports configured state; verifier agents carry off-contract instruction; bootloader escalator narrowed (order-robust) within byte cap",
      "acceptance_command": "out=$(bash tools/tests/install-roundtrip.sh) && echo \"$out\" | grep -qi 'agentfw-custom' && echo \"$out\" | grep -qi 'validator' && python3 - <<'PY'\nimport json;d=json.load(open('adapters/claude-code/settings.example.json'));a=' '.join(d['permissions']['allow'])\nassert 'cat:' not in a and 'find:' not in a and 'Bash(ls' not in a and 'Bash(grep' not in a and 'Bash(rg' not in a and 'Bash(wc' not in a, 'file-dumper allow remains'\nassert 'pytest' not in a and 'npm test' not in a, 'test-runner allow remains'\nask=' '.join(d['permissions']['ask']);assert 'pytest' in ask or 'npm test' in ask, 'test runners missing from ask'\ndeny=' '.join(d['permissions']['deny']);assert '.ssh' in deny and '.env' in deny, 'secret denies lost'\nprint('SETTINGS OK')\nPY\ntest $? -eq 0 && test $(wc -c < adapters/claude-code/CLAUDE-block.md) -le 2500 && ! grep -qiE 'autonomous multi-file|multi-file autonomous' adapters/claude-code/CLAUDE-block.md && grep -q 'off-contract' adapters/claude-code/agents/agentfw-verifier.md && grep -q 'off-contract' adapters/claude-code/agents/agentfw-plan-critic.md && grep -qi 'manifest' tools/agentfw-install && grep -qi 'configured' tools/agentfw-install",
      "expected_signal": "roundtrip output contains the new PASS lines (agentfw-custom survival; sandbox validator executed against a fixture); manifest written and consumed; SETTINGS OK; escalator negative grep clean; all exits 0",
      "risk": "uninstall still reachable for user-owned files, or validator packaging only asserted by inventory rather than executed in the sandbox",
      "negative_cases": ["roundtrip seeds agentfw-custom.md before uninstall and fails unless it survives", "roundtrip executes the sandbox-installed validator against a fixture and fails on non-zero exit", "settings assertion fails if any file-dumper or test-runner string returns to the allow list"],
      "environment": "repo working tree, python3 + bash, CLAUDE_DIR mktemp sandboxes for install probes; no network",
      "evidence": "acceptance_command output and exit codes recorded in the worker report, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}},
    {"id": "FB", "title": "Validator hardening + hostile fixtures", "deps": [],
     "contract": {"requirement_ids": ["FR2","FR11"],
      "criteria": "hardened validator rejects the five new defect classes with stable keywords; all prior positives still pass; schema of record updated in plan-critique.md incl. contract-ceiling note",
      "acceptance_command": "python3 tools/validate-plan tools/fixtures/plan-good.md && python3 tools/validate-plan PLAN-r9.md && python3 tools/validate-plan PLAN-r9-fixpass.md && d=$(mktemp -d) && ok=1 && for pair in missing-contract:contract cyclic:cycl uncovered-req:cover risk-without-negative:negative empty:empty unknown-ref:cover duplicate-id:duplicate malformed-req:empty no-rerunnable:contract; do f=${pair%%:*}; k=${pair##*:}; cp tools/fixtures/plan-bad-$f.md $d/x.md; if python3 tools/validate-plan $d/x.md >$d/out 2>&1; then ok=0; echo \"NOT REJECTED: $f\"; fi; grep -qi $k $d/out || { ok=0; echo \"KEYWORD MISS: $f ($k)\"; }; done && test $ok = 1 && grep -qi 'ceiling' policy/plan-critique.md && grep -q 'duplicate' policy/plan-critique.md",
      "expected_signal": "three positives PASS; all nine bad fixtures rejected under neutral filenames with matching defect-class keywords",
      "risk": "hardening breaks existing positives (PLAN-r9.md regression) or new checks live in prose but not code",
      "negative_cases": ["each of the three new hostile fixtures is rejected with its keyword", "an A2 plan with zero tasks can no longer PASS (plan-bad-empty.md proves it)", "unknown requirement_ids can no longer PASS (plan-bad-unknown-ref.md proves it)"],
      "environment": "repo working tree, python3 + bash, mktemp scratch dirs for neutral-filename fixture copies; no network",
      "evidence": "acceptance_command output and exit codes recorded in the worker report, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}},
    {"id": "FC", "title": "Policy revisions", "deps": [],
     "contract": {"requirement_ids": ["FR6","FR7","FR9","FR10","FR11"],
      "criteria": "tiered verified states + derivation; five evidence classes with tier combinations; capability spec gains available/configured/activation_probe with unverified-and-unconfigured gating; escalator narrowed; A0 compression clause; vendor-neutrality preserved",
      "acceptance_command": "grep -q 'verified_producer' policy/acceptance-contract.md && grep -q 'verified_independent' policy/acceptance-contract.md && grep -q 'verified_adversarial' policy/acceptance-contract.md && grep -q 'required_verification_tier' policy/acceptance-contract.md && ! grep -qF 'fresh per `produced_after_change`, re-executed by the independent judge' policy/acceptance-contract.md && grep -qi 'behavioral' policy/acceptance-contract.md && grep -qi 'structural' policy/acceptance-contract.md && grep -qi 'source-grounded' policy/acceptance-contract.md && grep -qi 'expert' policy/acceptance-contract.md && grep -qi 'human-authorization\\|human authorization' policy/acceptance-contract.md && grep -qi 'combination' policy/acceptance-contract.md && grep -qi 'available' policy/capability-contract.md && grep -qi 'configured' policy/capability-contract.md && grep -qi 'activation_probe' policy/capability-contract.md && grep -qi 'rapid human review' policy/assurance-model.md && ! grep -qiE 'autonomous multi-file|multi-file autonomous' policy/assurance-model.md && ! grep -qiE 'autonomous multi-file|multi-file autonomous' policy/core.md && grep -qi 'compress' policy/core.md && ! grep -riE 'claude|codex|chatgpt|openai|anthropic' policy/core.md policy/assurance-model.md policy/acceptance-contract.md policy/capability-contract.md | grep -vE 'adapters/|profiles/' | grep -q .",
      "expected_signal": "exit 0 — including the pinned-sentence negative grep (old universal-judge clause gone) and order-robust escalator negatives at the sites where the escalator lives",
      "risk": "the contradiction is reworded but survives (independent re-execution still stated as universal for reaching any verified state), or vendor tokens leak in during the edit",
      "negative_cases": ["acceptance-contract.md no longer contains an unscoped universal independent-judge requirement (the A0/A1 producer path is explicit)", "vendor-token sweep stays empty"],
      "environment": "repo working tree, python3 + bash; no network",
      "evidence": "acceptance_command output and exit codes recorded in the worker report, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}},
    {"id": "FD", "title": "Profiles, instances, codex install, repo metadata", "deps": [],
     "contract": {"requirement_ids": ["FR1","FR5","FR8","FR9","FR10"],
      "criteria": "chatgpt profile rescoped+renamed with Work note and doc citation; both capability instances migrated to available/configured; codex INSTALL carries the validator copy step; metadata/bootstrap routing fixed; changelog/readme consistent; no dangling refs",
      "acceptance_command": "test -s profiles/chatgpt-projects.md && test ! -e profiles/chatgpt.md && grep -q 'not an adapter' profiles/chatgpt-projects.md && grep -q 'no deterministic enforcement' profiles/chatgpt-projects.md && grep -qi 'ChatGPT Work' profiles/chatgpt-projects.md && grep -qi 'learn.chatgpt.com' profiles/chatgpt-projects.md && grep -qi 'validate-plan' adapters/codex/INSTALL.md && for y in adapters/codex/capability.yaml adapters/claude-code/capability.yaml; do for k in filesystem shell isolated_agents parallel_agents persistent_state deterministic_permissions worktree_isolation scheduled_resume independent_review structured_output; do grep -A6 \"^$k:\" $y | grep -q 'available:' || { echo \"$y $k missing available\"; exit 1; }; grep -A6 \"^$k:\" $y | grep -q 'configured:' || { echo \"$y $k missing configured\"; exit 1; }; done; done && ! grep -qiE 'autonomous multi-file|multi-file autonomous' adapters/codex/AGENTS.md && test $(wc -c < adapters/codex/AGENTS.md) -le 2500 && python3 -c \"import json;m=json.load(open('metadata.json'));assert 'adapters/' in m.get('install',''), 'install must point into adapters/';assert m.get('bootstrap_r8')=='bootstrap.md', 'r8 bootstrap must be relabeled';assert m.get('bootstrap')!='bootstrap.md', 'r9 still routes to r8 bootstrap';assert 'chatgpt-projects' in m['profiles']\" && head -3 bootstrap.md | grep -qi 'r9' && n=$(git diff --numstat HEAD -- bootstrap.md | awk '{print $1+$2}') && test \"${n:-0}\" -le 3 && bash tools/tests/check-links.sh",
      "expected_signal": "exit 0 with check-links PASS (no dangling refs after the rename); per-key available/configured conformance on BOTH capability instances; bootstrap.md numstat-bounded",
      "risk": "rename leaves dangling references, or capability migration loses keys/annotations",
      "negative_cases": ["check-links fails on any reference still pointing at profiles/chatgpt.md", "10-key and verified-annotation greps re-run on both migrated capability files"],
      "environment": "repo working tree, python3 + bash; no network",
      "evidence": "acceptance_command output and exit codes recorded in the worker report, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}},
    {"id": "FV", "title": "Adversarial verification", "deps": ["FA","FB","FC","FD"],
     "contract": {"requirement_ids": ["FR1","FR2","FR3","FR4","FR5","FR6","FR7","FR8","FR9","FR10","FR11"],
      "criteria": "fresh verifier re-executes FA-FD acceptance_commands verbatim, replays Sol's four probes expecting fail-safe outcomes, re-runs PLAN-r9.md T1-T6 regression commands (T4 with profiles/chatgpt.md substituted to profiles/chatgpt-projects.md — the rename makes the original path an expected-fail), performs at least two off-contract hostile probes of its own, and substance-reviews the token-grepped requirements (FR7 tier-combination table, FR8 Work note, FR9 per-entry honesty) rather than trusting greps",
      "acceptance_command": "python3 tools/validate-plan PLAN-r9-fixpass.md && bash tools/tests/install-roundtrip.sh >/dev/null && python3 tools/validate-plan tools/fixtures/plan-good.md >/dev/null && bash tools/tests/check-links.sh && ! grep -riE 'claude|codex|chatgpt|openai|anthropic' policy/ | grep -vE 'adapters/|profiles/' | grep -q . && test -z \"$(git diff --name-only HEAD -- core references variants)\"",
      "expected_signal": "verifier report with recorded outputs: all four Sol probes now fail-safe; all FA-FD contracts re-executed green; T1-T6 regressions green (T4 path-substituted); off-contract probes and substance review reported",
      "risk": "fixes verified only against the fix contracts, repeating the contract-bounded-verification ceiling this pass exists to correct",
      "negative_cases": ["Sol probe replay: empty A2 plan must be REJECTED", "Sol probe replay: seeded agentfw-custom.md must SURVIVE uninstall", "Sol probe replay: sandbox install must CONTAIN a runnable validator", "Sol probe replay: settings allow list must not permit a cat/find secrets bypass"],
      "environment": "repo working tree, python3 + bash, CLAUDE_DIR mktemp sandboxes for install probes; no network",
      "evidence": "verifier report with re-executed acceptance_command outputs and exit codes, produced_after_change",
      "required_verification_tier": "adversarial",
      "integration_seam": true,
      "risk_class": "standard",
      "rerunnable": true}}
  ]
}
```
