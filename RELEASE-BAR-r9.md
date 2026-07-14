# r9 Release-Bar Redefinition — proposal for maintainer approval (one page)

**Problem.** The implicit r9 bar — every golden-task criterion PASS, n≥5, two platforms — demands
that probabilistic behavior act like a function. Three eval phases show the cost curve: every
prose-mediated rule reads differently across models and runs, each fix pass buys one margin and
exposes the next, and a model update would void the result anyway (eval-protocol already requires
re-running on model change). Meanwhile every deterministic mechanism shipped to date has worked on
first contact and never regressed. The bar should match that split.

**Proposed definition — r9 ships as v9.0 when BOTH tiers hold:**

**Tier 1 — Deterministic layer: MACHINE-VERIFIED (binary, blocking).**
Everything enforced by code must prove itself green in one command run: installer roundtrip
(25/25), validate-plan full fixture suite (schema 1.2 floors, fail-safe versioning, review-tier
emission), capability contracts under both parsers, link integrity, r8-dir freeze, publication-
hygiene sweep over all committed transcripts. Any red = no release. (Status: green today.)

**Tier 2 — Behavioral layer: MEASURED AND PUBLISHED (propensities, not pass/fail).**
For each golden-task mechanism × platform, publish the observed rate from the fixtured suite at
n≥5 with the model pinned per cell — e.g. "destructive stop-before-delete: claude 5/5, codex
5/5; dual-review from tier line: claude 4/5; …" — with verbatim-quote evidence discipline as
now. Release requires: (a) every SAFETY-CRITICAL mechanism (destructive stop, never-auto-dispatch
past blockers, no self-clearance) at 100% observed in the run, with any miss triaged as
framework-vs-harness before proceeding; (b) every other mechanism simply REPORTED honestly, with
divergences named (e.g. the claude/codex simulated-authorization split). No aggregate claim,
no "validated" adjective — the ledger IS the claim.

**What changes in practice.**
- "Validated release" language is retired; v9.0's release notes say: deterministic layer
  machine-verified; behavioral layer measured at n=5 per cell on the named models, numbers
  attached. Model updates invalidate Tier 2 numbers only — re-measure, don't re-gate Tier 1.
- The n≥5 matrix becomes ONE bounded run (≈ 9 GTs × 2 platforms × 5 = 90 cells + judging) whose
  job is to produce the Tier-2 table — not to chase all-PASS. Fixes after it only for safety-
  critical misses or harness defects; behavioral shortfalls below 100% on non-critical mechanisms
  ship as published numbers with open issues.
- Standing cost controls: sonnet judges with mechanical quote-verification (proven adequate —
  they caught every real defect this phase), exec-verification over prose re-review for command
  strength, Fable/Opus reserved for dispatch and final semantic reviews.

**Why this is not a lowered bar.** The old bar was unfalsifiable-by-affordability and silent
about variance; this bar makes the deterministic guarantees hard (unchanged), makes the
behavioral claims honest (new — today they're anecdotes at n=1), and pins safety-critical
behavior at 100%-observed-or-halt (stricter than today, where those mechanisms have never been
sampled more than once). It converts eval spend from "prove perfection" to "publish calibration."

**Decision requested:** approve this bar (or amend), after which the n≥5 run is scoped as the
Tier-2 measurement run — still requiring your explicit go per the standing no-go.

*Open items feeding the n≥5 design, carried from fixpass3: issue #5's evidence-persistence needs
a cell shape that reliably reaches producer dispatch (the GT-5 gate-cap path structurally
shadows it); issue #6 (authorization provenance) remains deferred and its claude/codex divergence
will appear in the Tier-2 table until fixed.*
