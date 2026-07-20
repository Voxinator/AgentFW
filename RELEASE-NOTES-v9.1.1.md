# AgentFW v9.1.1 — Release Notes

**Released 2026-07-20.** Documentation-correctness patch over
[v9.1.0](RELEASE-NOTES-v9.1.0.md). No policy, schema, validator, or adapter payload changed — the
governance surface is byte-identical to v9.1.0. Upgrade only if you install or upgrade the **Codex**
adapter.

## Why this release exists

v9.1.0 shipped a Codex upgrade procedure that quietly disarmed the thing AgentFW exists to enforce.

`adapters/codex/UPGRADE.md` Case A step 3 removed the installed skill directory and copied back two
items — `SKILL.md` and `policy/`. `adapters/codex/INSTALL.md` Step 2 installs **four**: those two
plus `tools/validate-plan` (the Layer-1 plan validator) and `capability.yaml` (which the skill's §0
capability preflight reads). Anyone upgrading Codex by the book therefore ended up with an install
that could no longer run Layer-1 plan validation and could no longer see its own capability
contract.

Both losses are silent. The skill still loads. The bootloader still lives in `AGENTS.md`, untouched.
The model still derives assurance levels and emits `[ASSURANCE: …]` markers correctly. Nothing
announces that the deterministic gate underneath has stopped firing.

## The second half of the defect

The procedure's own verification could not have caught it.

Step 5 deferred entirely to INSTALL.md Step 4, which is behavioral: start a fresh session, run
`/skills`, ask the model to state its operating framework, confirm an `[ASSURANCE: A0 — …]` line
appears. Every one of those checks passes with the validator missing, because none of them touch the
skill directory's file inventory.

That is the more interesting failure. A check that cannot go red on the defect it is meant to catch
is not a check — which is the C-1 principle this very release line introduced, applied here to
AgentFW's own installation docs.

## What changed

**Step 3 — restore the complete inventory.** All four Step 2 items, with the old directory *moved
aside* rather than deleted, so a failed copy leaves a rollback:

```sh
mv ~/.agents/skills/agentfw ~/.agents/skills/agentfw.bak-$(date +%Y%m%d-%H%M%S)
mkdir -p ~/.agents/skills/agentfw/tools
cp adapters/codex/skills/agentfw/SKILL.md ~/.agents/skills/agentfw/SKILL.md
cp -R policy ~/.agents/skills/agentfw/policy
cp tools/validate-plan ~/.agents/skills/agentfw/tools/validate-plan
chmod +x ~/.agents/skills/agentfw/tools/validate-plan
cp adapters/codex/capability.yaml ~/.agents/skills/agentfw/capability.yaml
```

**Step 5a — a mechanical inventory check.** Exit-code gated, `INVENTORY_OK` emitted last so every
clause gates the signal. Verified red against a skill directory built exactly the way the old
procedure built it, and green against a correct install.

**Step 5b — the behavioral check** (former INSTALL.md Step 4) is retained, not replaced. It answers
a different question: whether the bootloader is loaded at all.

## Who is affected

| Adapter | Affected | Why |
|---|---|---|
| Codex | **Yes** | Has no installer; inventory correctness rode entirely on the prose being right. |
| Claude Code | No | `tools/agentfw-install` is manifest-based, and `agentfw-install status` already verifies the file inventory mechanically. |

**If you upgraded Codex using the v9.1.0 procedure,** run the Step 5a check. If it does not print
`INVENTORY_OK`, re-run Step 3 from this release.

## Published field evidence

`evaluation/field-report-2026-07-20-noita-planning-livelock.md` ships with this release. It reports
a real incident under an active r9 install: AgentFW **correctly stopped a destructive-data
mistake**, then **prevented all implementation** through a planning livelock — repeated plan/critique
cycles in which each fresh Layer-2 pass surfaced new, increasingly specific objections, with no
global budget and no implementation worker ever dispatched.

Its central structural claim is that AgentFW's safety invariant is currently stronger than its
delivery/liveness invariant, and that a per-cycle pass cap provides local bounding without global
liveness. It also independently identifies **stale-install drift** as a contributing cause: the
active installed policy lacked the v9.1 cap-recovery menu that the repository contained. That is the
same class of distribution failure this patch fixes, arrived at from the opposite direction.

Three of the report's four evidence hashes were reproduced during this release and matched. The
fourth was a 66-character string where a SHA-256 is 64; it was corrected to the verified value of
the file it described. The report is otherwise published as written.

**Its recommendations are not implemented in v9.1.1.** A global liveness budget, separating safety
blockers from reversible implementation assumptions, surfacing cap recovery in the adapter skill
itself, and failing visibly on policy drift are all candidates for a later release, not claims about
this one.

**Evidence boundary:** one field incident, not a statistical result. It does not show that every
governed A2 task livelocks, and it does not weaken the case for the destructive-action stop — which
worked.

## Verification

`tools/tests/release-v9.1.sh`, re-pinned to the 9.1.1 identity: release-document and metadata
consistency, the schema validator fixture harness, installer roundtrip **28/28**, relative-link
resolution, and capability validation through **both** parser paths (PyYAML and the stdlib
fallback).

**No behavioral-evaluation round was run for v9.1.1.** The bounded n=1 evidence published with
v9.0.0 remains the behavioral record and is not re-presented as fresh evidence.
