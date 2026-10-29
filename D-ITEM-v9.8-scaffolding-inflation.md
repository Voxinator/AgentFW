# D-32 — Scaffolding inflation (headline D-item for v9.8)

**Reported by:** Brian, 2026-10-28, from repeated operational experience.
**Status:** proposed. Evidence: operator history (primary) + one worked reproduction (below).
**Consequence today:** AgentFW goes unused on judgment-heavy work. `policy/model-dispatch.md`
line 4 already states the cost: *"an unused framework governs nothing."*

---

## The defect

Workers invent test scaffolding beyond the requirement. Judges then fail the plan **on the
scaffolding**, not on the requirement. The operator pays in go-arounds and context.

## The loop

| Step | What happens |
|---|---|
| 1 | Every A2+ task needs an `acceptance_command`. |
| 2 | Analysis/docs/research work has no natural one, so the producer **invents** it. |
| 3 | C2 ("prose-vs-mechanical reachability — core check") makes attacking that command the judge's job. |
| 4 | The invented command is now the biggest unverified artifact in the plan. It absorbs all judge attention. |
| 5 | Fixing it adds guards. Guards add surface. More surface → more blockers. |
| 6 | Budget exhausts on scaffolding. The requirement is never examined. Operator does the go-around. |

**Requirements are bounded. Scaffolding is unbounded.** Nothing caps one against the other.

## Why existing controls don't catch it

| Control | Why it fails |
|---|---|
| D-19 necessity tiers | Apply to **requirements** only. No `necessity` on an acceptance command. |
| §7 Complexity Accumulation | Advisory prose, no mechanical teeth — the "prose promise" the kernel forbids elsewhere. |
| C4 anti-pattern check | Does fire, but **after** the spend. In the reproduction it fired at pass 4 of 4. |
| D-21 zero-dispatch tripwire | Latches at **two** completed cycles. By then the budget is gone. |

## Worked reproduction (this session, n=1)

Objective `v98-sweep`. Task: audit AgentFW against doctor findings and the current model set.

| Metric | Value |
|---|---|
| Acceptance instrument written | 451 lines, nobody asked for it |
| Layer-2 passes spent | 4 / 4 |
| Cycles spent | 2 / 2 |
| Workers dispatched | **0** |
| Requirements examined by any judge | **0** |
| Blockers about the scaffolding | **all of them** |
| Useful findings produced | several — **all from preflight, before scaffolding existed** |

Each repair opened a new hole: the H8 freeze fix introduced a forgeable
`_frozen-probes.json` that judge C exploited within one pass. Monotonic surface growth,
exactly as the loop predicts.

---

## Proposed fix: split the verdict axes

A judge returns **one** verdict today, so a scaffolding defect blocks the work. Split it:

| Axis | Question | Effect |
|---|---|---|
| **(a)** | Is the work right? | **Gates dispatch** |
| **(b)** | Is the acceptance machinery strong? | **Sets the evidence tier. Does not gate.** |

A scaffolding-only failure then downgrades the claim from `verified` to
`judge-corroborated` and lets work proceed, with the operator seeing what they got.
Today the only outcomes are "machine-verified" or "nothing happens" — and for analysis
work it is always the second.

### Guard against the obvious loophole

Axis (b) **must stay binding for code.** Where a real test can exist, a weak command is
still a blocker — there you are not inventing scaffolding, you are declining to write a
test that ought to exist. Without this, every producer relabels its work "analysis" to
dodge the gate.

### Make the boundary mechanical, not a judgment call

Discriminator, checkable in `validate-plan` at Layer 1 from the schema as it already stands:

```
task.touches contains executable code  ->  acceptance_command MANDATORY, axis (b) binds
task.touches is prose/data only        ->  reasoned-independent tier, NO command to invent
```

Layer 1 enforcement matters: a judge's discretion is what producers game.

### Supporting changes

1. **New first-class tier** `required_verification_tier: reasoned-independent` — no
   `acceptance_command` field at all. Nothing to invent for a document.
2. **Move the tripwire earlier.** Cycle 1 ending with zero workers *and* only
   scaffolding-class blockers is the signal. Do not wait for cycle 2.
3. **Scaffolding budget.** Declare acceptance-machinery size per task; growth across a
   revision is a Layer-1 scope note, not a silent cost.

---

## Open question (needs operator input)

The `touches`-based discriminator assumes the misdirection only happens on non-shell work.
**If the go-arounds Brian experienced also happened on code tasks, this fix is wrong** and
the defect is deeper than the non-shell boundary. One session is n=1; operator history is
the stronger dataset.

## Related, found in the same session

- `tools/agentfw-install` never probes `model_selection` → D-14's capability is permanently
  `unknown`, so adaptive dispatch silently degrades to Uniform, undeclared, on every install.
- `agentfw-install` is not copied into the installed skill → §0's mandated
  `agentfw-install status` refresh is unreachable without the repo checkout.
- `AGENTFW:END` sits above two lines of AgentFW content, which therefore never update
  across releases (the M365 note still reads "out of scope for v8").
- Tier ladder `[haiku, sonnet, opus, fable]`, `floor: sonnet`, `flagship: fable` — **correct**
  against Haiku 5.5 $0.10/$0.50 → Sonnet 5.5 $2/$10 → Opus 5.5 $4/$20 → Fable 5.1 $10/$50.
  Zero concrete model ids in policy text. The model-agnostic core held across two generations.
- `failure_surfaces` enum has no member that fits documentation or analysis work.
