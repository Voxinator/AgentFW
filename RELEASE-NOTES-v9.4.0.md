# AgentFW v9.4.0 — the operator release

**Released 2026-07-31.** Five candidates shipped in one field-driven day: the framework now
answers to the operator instead of to itself. An operator's deliberate permission-mode choice is
respected instead of blocked (D-16); a plan objective gets a hard review budget instead of an
endless treadmill (D-2); scope discovered after the gate is deferred by default instead of
folded in (D-18); every requirement must justify its own existence and a judge is paid to cut,
not just to add (D-19); and every gate outcome must be explained in plain language a
policy-non-reader can act on (D-20). The six-item safety floor is untouched throughout. Design
of record: [CANDIDATES.md](CANDIDATES.md) § D-16, § D-2, § D-18, § D-19, § D-20; field
evidence:
[evaluation/field-report-2026-07-31-drydock-scope-accretion.md](evaluation/field-report-2026-07-31-drydock-scope-accretion.md).

## D-16 — operator-relaxed enforcement (full access / bypass is a lever, not a blocker)

A Codex install running `sandbox_mode = "danger-full-access"` could not get any A2+ plan past
the gate: the adapter probes classified the mode as missing substrate, gating routed that to
safety-floor item 5 (never waivable), and the operator's deliberate choice became an unwaivable
blocker. The Claude Code adapter escaped only by accident — its probe never read the permission
mode at all.

- **New core rule** (`policy/capability-contract.md` § *Operator relaxation is a lever, not
  missing substrate*): an explicit relaxed mode in live config (Claude Code
  `bypassPermissions`; Codex `danger-full-access` / `approval_policy = "never"`) is
  **operator-relaxed**, not unconfigured. Handling is fixed at four steps: **recommend the
  floor once** at plan time; **declare** `[FLOOR-RELAXED: operator — <mode>]` citing documented
  residuals only; **compensate behaviorally** (destructive/irreversible/outward effects gate on
  a genuine human turn — already A3/A4 policy); **proceed**. Never a Layer-2 blocker, never
  safety-floor item 5, never re-raised per task.
- **Honesty bound:** Claude Code's documented bypass residuals are explicit `ask` rules,
  connector `ask` settings, `requiresUserInteraction` MCP tools, and the root/home `rm` circuit
  breaker. Whether deny rules and PreToolUse hooks still evaluate under bypass is **not stated
  in official docs** — the adapter now says so and claims nothing more.
- **Unchanged:** genuinely unconfigured installs still gate as absent; sleep/headless still
  halts at floor blockers — relaxation removes interruptions while a human is reachable, never
  the human.

## D-2 — global liveness budget (the cap treadmill ends)

The 2-pass cap bounded each cycle; a fresh cycle reset it. Field-demonstrated result: the cap
hit "over and over," with progress only when the maintainer hand-carried blockers between
runtimes.

- Review expenditure accrues **per objective** — `cycles` and `layer2_passes`, budget **2
  cycles / 4 Layer-2 passes** for reversible A2 (A3/A4 may extend by exactly one named
  human-authorized cycle, once). Markers: `[LIVENESS: objective <slug> — cycle n/2, layer2
  passes m/4]`, `[LIVENESS-EXCEEDED: …]`.
- **No reset:** a renamed, renarrowed, or restructured plan chasing the same goal inherits the
  counters.
- **At exhaustion** planning stops; the only moves are **halt** (open floor blocker, or the
  human declines) / **rescope proposal** (C5 contradiction or unavailable substrate) /
  **proactive delivery-override offer** — the model brings the D-1 offer to the human instead
  of waiting to be asked.
- Machine-checked as a decision table: `tools/check-liveness-invariants.py` over
  `evaluation/fixtures/liveness-budget.json` (exhausted ⇒ never another cycle; floor blocker ⇒
  halt; same-objective ⇒ never reset; hardened against fixture flag-laundering).

## D-18 — post-gate scope freeze (the accretion valve)

Field-demonstrated: four requirements born in ~35 minutes of post-gate conversation, every one
defaulting *into* the gated plan — a critique gate functioning as a scope generator.
Requirements discovered after a plan's Layer-1 PASS now default to a recorded
**next-increment ledger** beside the plan; folding one in is an explicit human choice that
spends a D-2 cycle. Ship the gated increment; plan the discoveries against the next one.

## D-19 — necessity tiers + C6 demote-duty (requirement-inflation defense)

Every gate check asked "what's missing?"; nothing ever asked "would this fail without it?" —
so adding read as diligence and cutting was nobody's job.

- **Plan schema 1.5** (new schema of record, additive over 1.4): every requirement carries
  `necessity` ∈ `must` | `nice-to-have` | `fluff`, and a `must` carries a plain-language
  `because` naming the concrete failure without it. `tools/validate-plan` enforces it (new
  stable defect keyword `necessity`): unlabeled scope, unjustified musts, and any task
  building fluff are defects. Coverage is **tier-aware**: an uncovered nice-to-have is valid
  deferred scope — the plan block doubles as the D-18 next-increment ledger — and a task
  serving only nice-to-haves gets a non-fatal `scope note:`.
- **C6, the anti-coverage check:** the Layer-2 judge independently attempts to name the failure
  behind every must-claim; a claim that fails the attempt is **demoted to nice-to-have, not
  debated** — a scope correction, never a blocker, never a re-plan trigger. Coverage stops
  under-building the musts; C6 stops over-claiming them.
- Backward compatible: 1.1–1.4 plans validate exactly as before.

## D-20 — the operator digest (plain language or it isn't governance)

Markers, rubric letters, and candidate numbers are audit-speak addressed to a future grep — and
they were the only rendering the operator ever got, making requirement inflation invisible even
to a diligent human reader.

- Every gate event — Layer-1 result, Layer-2 verdict, escalation menu, override offer — now
  carries a fixed-shape **operator digest** written for someone who has never read the policy:
  what the plan builds; scope counts by necessity (musts / nice-to-haves built-vs-deferred /
  dropped); an **ADDED/REMOVED delta** since the last version, one plain line per change with
  its tier and "because" — the operator's inflation detector, with a new post-gate must-have
  called out explicitly; review cost in plain numbers; and a one-line ask.
- **The counts cannot be fiction:** on schema 1.5 they must match `validate-plan --digest`,
  the machine-derived count oracle; a mismatch is a defect, and prose never overrides the block.
- **Speak-twice rule:** any marker the operator is expected to act on carries one plain
  sentence beside it. Governance the operator cannot parse is governance that does not govern —
  the economy calibration applied to language.

## Also in this release

- **D-17 (cross-substrate consult)** proposed on the ledger with field evidence — same-family
  verifiers missed the same blind spot twice; a different model family resolved it. Not built;
  awaiting maintainer acceptance.
- **D-7 (plan-mass alarm)** evidence updated with the drydock accretion transcript; still
  proposed.
- Layer 2 is now the **C0–C6 rubric** across policy, both adapter SKILLs, the packaged
  plan-critic agent, and both kernel bootloaders.

## Release evidence

Deterministic gate: `tools/tests/release-v9.4.sh` — release identity, D-16/D-2/D-18/D-19/D-20
policy and surfacing facts, the full validator fixture harness (schema 1.5 positives, hostile
fixtures, `--digest` count oracle), installer roundtrip, link check, 11-key capability schema on
both parser paths, adapter SKILL sync, sleep-posture and liveness decision-table invariants, and
ledger completeness for D-2 and D-14 through D-20. Independent verification: three input-curated
`agentfw-verifier` passes ran during the build (D-16, D-2, D-19/D-20), each re-executing
acceptance commands and mutation probes on scratch copies; all PASS.

**Behavioral evidence boundary:** no behavioral-evaluation round was run for v9.4.0. The
machine-checked invariants (liveness decision table, schema 1.5 fixtures, digest count oracle)
are the deterministic proof; whether models honor the liveness markers, C6 demote-duty, and
digest duty in the field is behavioral and remains to be measured — the D-6 treadmill eval and
the drydock follow-up are the designated instruments.
