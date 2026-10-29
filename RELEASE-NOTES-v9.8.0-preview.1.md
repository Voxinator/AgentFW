# AgentFW v9.8.0-preview.1 — harness gate preview

**Pre-release. Not Latest. Do not treat as v9.8.0.**

One behavioural change: **the `agentfw` skill no longer loads for prose work.** Everything
else is v9.7.0 unchanged.

---

## What's in it

```
task touches executable code  ->  harness available
task touches prose/data only  ->  harness FORBIDDEN, read-and-report
```

Two edits per runtime:

| File | Change |
|---|---|
| kernel (`CLAUDE.md` / `AGENTS.md`) | new **Harness gate (D-32)** section; the routing line, the A2 table row and the "load it before planning" line all now carry the code-only condition. +701 B / +707 B, ~175 est. tokens |
| `skills/agentfw/SKILL.md` | `description` narrowed to *"ONLY for work that modifies EXECUTABLE CODE"*, with an explicit do-not-use list for prose/docs/research/analysis/audits/design/planning |

The skill `description` is the real routing lever — narrowing it is what stops the skill
being matched against an analysis request in the first place. The kernel section is what
makes the rule legible to a session that has already loaded.

## What is NOT in it

This is the **gate**, not the **fix**. D-32's proposed mechanism — splitting the judge
verdict into "is the work right" (gates dispatch) versus "is the machinery strong" (sets
evidence tier only), plus a first-class `reasoned-independent` verification tier and a
Layer-1 `touches` discriminator — is **designed but unimplemented**. See
`D-ITEM-v9.8-scaffolding-inflation.md`.

Nothing else from v9.7.0 changed: schema 1.7, red witnesses, IMPOSSIBLE-COMMAND, the
ledger/scoreboard, model dispatch and the sleep posture are all as shipped.

## Why

Operator-reported: agents invent test scaffolding above the requirement, then judges fail on
the scaffolding rather than the requirement. Go-arounds and token spend inflate, and the
harness goes unused on judgment-heavy work.

Reproduced end to end before shipping this (objective `v98-sweep`, ledger in the repo):

| Metric | Value |
|---|---|
| Acceptance instrument written | 451 lines, unrequested |
| Layer-2 passes | 4 / 4 |
| Cycles | 2 / 2 |
| Subagent tokens | 298,729 |
| Workers dispatched | **0** |
| Requirements examined by any judge | **0** |

Every useful finding came from the §0 preflight, before any scaffolding existed.

## Install

```bash
git fetch --tags
git checkout v9.8.0-preview.1
tools/agentfw-install install
tools/agentfw-install status      # verify
```

Covers both runtimes. Claude Code reads its skill from `~/.claude/skills/`; Codex reads
from `~/.agents/skills/`.

## Rollback

```bash
git checkout v9.7.0
tools/agentfw-install install     # re-installs 9.7.0 over the preview
```

Or remove entirely with `tools/agentfw-install uninstall`.

## Known issues in this preview

- **The gate is blunt.** It forbids the harness for all non-code work rather than offering a
  lighter verification tier for it. A task that genuinely needs independent review of a
  document gets review (the kernel still mandates it at A2+) but no contract machinery.
- **The discriminator is prose, not enforced.** "Touches executable code" is a judgement the
  model makes, not something `validate-plan` checks. Mechanical enforcement is part of the
  unimplemented fix.
- **Open question that could invalidate the whole approach:** did the original go-arounds
  also happen on *code* tasks? If yes, the code/prose boundary is the wrong place to cut.
  Feedback on this specifically is the most useful thing a preview tester can give.
- `AGENTFW:END` still sits above two lines of kernel content, so those two lines do not
  update across installs. Unfixed here; tracked separately.

## Feedback

PR [#21](https://github.com/Voxinator/AgentFW/pull/21) carries the full analysis and the
reviewer caveats, including the honest evidence tier: the findings behind this change are
**judge-corroborated, not machine-verified**.
