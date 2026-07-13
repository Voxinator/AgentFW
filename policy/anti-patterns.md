# Anti-Patterns — the Judgment Layer

Platforms are biased toward MORE machinery — a feature never tells you to stop using it, and neither
does a framework. This catalog is the counterweight. Each entry: what it is, the tell, the fix.

### One-Shot Hero Mode
Solving complex work in one massive response — the single-turn failure mode. **The tell:** your response
balloons past a screen while you hold six sub-problems in your head simultaneously; errors compound in
the thin-attention middle third, producing a plausible-looking answer with defects buried where
attention was thinnest. **The fix:** the pull to push through IS the decomposition signal. Classify,
decompose, fan out.

### Flat Coordination
Parallel efforts sharing one context/state with no hierarchy — no one owns priority, conflict
resolution, or final integration. **The tell:** parallel workers producing contradictory changes to the
same files; merge chaos; duplicated effort. **The fix:** planner–producer–judge structure with disjoint
scopes; exactly one context owns integration.

### Complexity Accumulation (load-bearing)
Adding coordination machinery when things aren't working. On capable platforms another isolated context
or verification step is nearly free, so over-orchestration is the DEFAULT failure, not the exotic one.
**The tell:** a third layer of orchestration managing failures in the first two; harness scaffolding
outweighing the work product. **The fix:** cleaner isolation, clearer roles, less coupling — never
another layer. The right amount of machinery is the minimum that still decomposes and verifies.
**This applies to this framework's own machinery.** The temptation to add schemas, adapters, and event
taxonomies beyond what a real validator consumes is Complexity Accumulation wearing the framework's own
badge. A schema no validator reads is decoration (see Prose-API); a binding no evaluation has run is a
liability (see Adapter Sprawl).

### Context Window Stuffing
Holding everything in one context instead of summarizing to the authoritative store and restarting.
**The tell:** pasting whole files "for reference" instead of reading the section you need; carrying
every prior turn when only the last decision matters; early instructions quietly deprioritized as the
window fills — drift you won't notice until verification catches it. **The fix:** summarize to the
authoritative store, restart with fresh context, continue from the record.

### Invisible Assumptions
Working from assumptions the human can't see or challenge. **The tell:** a library or approach chosen
because it's "standard," never stated, with three layers built on top before anyone reviews it — by
review time the assumption is load-bearing and expensive to reverse. **The fix:** state assumptions at
the top of every plan and every worker output. Caught early, a wrong assumption is a restart; caught
late, a rewrite.

### Patching Over Structural Problems
Patching individual symptoms of a wrong foundation compounds errors. **The tell:** each fix introduces a
new failure elsewhere; special-case handling added for the third time in the same area; the sunk-cost
voice saying "one more patch and I'm there." **The fix:** that voice is wrong. Restart the sub-problem
cleanly with the lesson carried forward (`policy/recovery.md`) — almost always faster than a fourth
patch on a broken foundation.

### Role Collapse ("I'll just do it myself")
The planning/judging context drops into producer mode because it "already has the context" and it seems
faster. The most common and most damaging entry here. The context that planned a fix is the worst
context to verify it — it carries its own assumptions into the review, like a developer merging their
own PR. **The tell:** you're about to write implementation inside the planning context at A2+. **The
fix:** if you planned it, you don't produce it; if you produced it, you don't judge it.

### Self-Review
The producing context runs the verification of record on its own output. It checks for what it
*intended*, not what *happened*, and misses the same edge cases in both passes. **The tell:** the
"independent" verdict was written by the context whose work it blesses — including conversational
role-play ("now I'll review as the QA engineer"), which is the producer wearing a hat, not an
independent context. **The fix:** verdicts of record come from a fresh, input-curated context that
evaluates artifacts cold. A producer's in-context pre-flight re-read of its own diff before handing off
is fine — that's diligence, not judgment of record.

### Rubber-Stamp Compliance
Emitting protocol markers without performing the assessment behind them. **The tell:**
`[ASSURANCE: A1 — small change]` on a production migration; `[CONTEXT HEALTH: OK]` with no evidence
while the session has been producing directly for three items; the marker appears but the behavior it
gates never changes. **The fix:** markers record decisions. If the gated behavior wouldn't change either
way, no decision was made. A bare OK without evidence is this pattern by definition.

### Prose-API (new in r9)
Specifying behavior as function signatures, state APIs, or event schemas that no runtime implements —
creating the illusion of enforcement. Prose that LOOKS like code inherits code's authority while
executing nothing. **The tell:** a spec section that reads like an interface definition nothing calls —
"the system SHALL expose a state-fetch function" on a platform that has no such function. **The fix:**
restate as invariants plus the minimum evidence that proves them ("an authoritative store exists and the
adapter declares it"), and let each adapter compile the invariant into whatever its platform actually
enforces. Schemas exist only where a real validator consumes them.

### Adapter Sprawl (new in r9)
Shipping platform bindings no evaluation has executed. Every adapter file asserts "this platform
provides X and we drive it correctly"; untested, that assertion is fiction with a directory structure.
**The tell:** a capability file whose claims nobody verified on the live platform; install and upgrade
docs written from imagination. **The rule:** an adapter you haven't tested is a profile you're lying
about — demote it to a guided profile (honest, declared as unenforced) until an evaluation has actually
run against the platform, and annotate every capability claim with its verification source or
`unverified`.
