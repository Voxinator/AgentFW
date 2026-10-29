# DECISION — keep the kernel, cut the skill

**Date:** 2026-10-28 · **Author:** Brian + Claude (session evidence below)
**Status:** proposed, pending the 3-task validation at the end of this document.

AgentFW's job is to beat what the model and harness produce alone. Measured against that bar,
it is two products with opposite value. This document keeps one and cuts the other.

---

## Decision

| | Component | Size | Verdict |
|---|---|---|---|
| **KEEP** | `~/.claude/CLAUDE.md` (r9 assurance kernel) | 6 KB · ~1.7k tokens · always loaded | **Keep as-is** |
| **CUT** | `~/.claude/skills/agentfw/` (SKILL.md + policy/) | 166 KB · ~41k tokens on invocation | **Quarantine behind a code-only gate** |

Not deprecation. Deleting the ~96% that spawns subagents, keeping the ~4% that is a checklist.

---

## Evidence (2026-10-28 session)

### Earned its keep — all checklist-shaped, all ~free

| Control | What it did | Cost |
|---|---|---|
| Destructive-effect classification + authorization gate | Forced enumeration of 4 processes before termination. They were **not** orphans — they were children of live Claude sessions. Prevented a real cross-session mistake. | ~0 |
| §0 capability preflight | Produced **every** useful finding of the day: `model_selection` never probed, 85-day stale snapshot, `agentfw-install` unreachable from a live install | ~5 greps |
| Layer 1 deterministic validator | Caught a real schema error (`failure_surfaces` prose vs enum) in seconds | ~0 |
| "Do not self-verify" / independent read | Caught 3 planner overclaims: the "runs Uniform" posture label, degradation 4's "nowhere in the repo", and the confounded per-dispatch-model evidence | 1 read each |

### Destroyed value

| Control | Result |
|---|---|
| Acceptance Contract v2 (+ schema 1.1→1.7) | Forced invention of a 451-line test instrument nobody needed |
| Dual Layer-2 judge gate | **298,729 subagent tokens** over 4 passes → **0 workers dispatched, 0 requirements examined** |
| Red witnesses / IMPOSSIBLE-COMMAND | Bookkeeping on a prose deliverable |
| Ledger / scoreboard / tripwire / liveness | 13 gate events recording that nothing happened |

### The decisive fact

The judge gate's largest catch was **a defect the framework itself caused.** It demanded an
acceptance command; a document has none; one was invented; four judges proved it worthless.
That is ~299k tokens spent detecting self-inflicted damage — circular, and net negative.

The destructive gate's catch was **not** circular. That is the whole distinction:
**controls that constrain behaviour pay for themselves; controls that manufacture artifacts
to inspect do not.**

---

## KEEP — stays in the always-loaded kernel

1. **Classify effects before acting.** Destructive by operation type ⇒ disclose exact scope,
   expected post-state, and the restoration path (or its absence) ⇒ authorization on a
   genuine human turn. Worked 5/5 today.
2. **The three assurance questions as a thinking prompt, not a gate.** Blast radius /
   defect escape / autonomy. Emit the marker. No machinery behind it.
3. **Capability preflight as a checklist.** Read the capability files; declare degradations;
   never claim a capability the runtime does not expose.
4. **Do not self-verify.** One independent read of code changes by a context that did not
   produce them. Input-curated.
5. **Layer 1 validator** (`tools/validate-plan`) — deterministic, instant, free. Keep for
   plans that exist; never require a plan to exist.
6. **Side effects through native controls**, not prose promises. Plus the operator-relaxation
   lever (`[FLOOR-RELAXED]`) as-is.

## CUT — quarantine behind "code with a test that would exist anyway"

- Acceptance Contract v2 and the whole schema line (1.1 → 1.7)
- Dual Layer-2 judge passes (C0–C6 ceremony)
- Red witnesses, witness pairs, IMPOSSIBLE-COMMAND, mutation probes
- Delivery ledger, scoreboard markers, zero-dispatch tripwire, liveness budget
- Enforcement locality (`enforced_in` / `touches` matching)

**Gate rule, mechanical, enforceable at Layer 1:**

```
task touches executable code  ->  harness available; acceptance_command meaningful
task touches prose/data only  ->  harness FORBIDDEN; read-and-report is the shape
```

Analysis, docs, research, audits and design work never invoke the skill. That is the single
change that would have saved ~299k tokens today.

---

## Validation — settle it with 3 tasks, not another cycle

Run the next **three real tasks kernel-only** (no `agentfw` skill invocation). For each record:

| Metric | Why |
|---|---|
| Outcome correct on first delivery? | The quality bar |
| Operator go-arounds | The complaint D-32 names |
| Total tokens incl. subagents | The compute bar |
| Defects the kernel's independent read caught | Whether the cheap control is load-bearing |

**Reversal criteria — reinstate the skill for code work if, and only if:** kernel-only runs
show defects escaping to delivery that an independent judge would plausibly have caught, on
code paths, more than once in three.

**Deprecate entirely if:** kernel-only matches or beats the harnessed runs on all four metrics.

---

## Caveat on this document's authorship

Half of it was written by the agent that burned the 299k tokens, which is not a neutral
witness about its own harness. The session is n=1. Operator history across many runs is the
stronger dataset and should override anything here it contradicts.

## Related

- `D-ITEM-v9.8-scaffolding-inflation.md` (D-32) — the mechanism behind the waste
- `PLAN-v9.8-sweep.md` + `.ledger.json` — the halted objective, 13 gate events, 0 workers
- Open question still unanswered: **did the go-arounds also happen on code tasks?** If yes,
  the code-only gate above is aimed at the wrong boundary.
