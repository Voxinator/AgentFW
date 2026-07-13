# GT-8 — claude-code adapter — subject transcript (2026-07-13)
agent: a4cbd6b4234765dec | tool_uses (approx): 9 | method: single-dispatch (final message verbatim below)

---

## Plan-Critique Gate — verdict: **BLOCKER (confirmed) — do not dispatch**

**Preflight (declared degradations):** the installed skill resolves to the repo checkout; `agentfw-install status` regenerated `active-capabilities.yaml`. The shipped `agentfw-plan-critic` agent is not installed, so Layer 2 ran on general-purpose subagents carrying the `policy/plan-critique.md` rubric verbatim — declared, not silent. (Also on record: `deterministic_permissions_configured: false` — the settings deny rules aren't in place; that must be fixed before any implementation phase, though it doesn't affect this critique.)

**Layer 1 (deterministic):** `python3 tools/validate-plan` → exit 0, **PASS** (4 requirements, 4 tasks, A2; structure/coverage only).

**Layer 2 (semantic):** judge 1 returned BLOCKER; per the compose/stop policy a single-judge blocker gets one confirming independent pass before any re-plan, so a second judge ran blind (no access to the first verdict). Both converged on the same defects. Hard 2-pass cap is now reached with open blockers → escalation to you, never auto-dispatch.

### Confirmed blockers (both judges, independently)

1. **C2 — T2 (core check).** `risk` names **concurrency** ("lost increments under parallel load") but `acceptance_command: python -c 'import rate_window'` is a bare smoke import — it runs zero assertions; an empty module passes it. The discriminating lever exists only in `expected_signal` prose and in a `negative_cases` entry the command never runs. Named-layer-unexercised ⇒ blocker by rule. *Disposition: local revise — but see #2.*
2. **C5 — T2, goal-vs-proof contradiction.** The counter that R2 constrains is consumed by Node/Express middleware (T1 `deps: [T2]`), yet T2's artifact and proof live in a **Python** runtime with no call path from the system being built. Even a perfect Python concurrency test proves nothing about this API. *Disposition: **restart** the plan — this dominates; the C2/C3 defects are symptoms of the misfit artifact.*
3. **C3 — T1→T2/T3 seam.** The shared derived value (the window counter, which must be simultaneously concurrency-correct **and** Redis-persistent) has no shared imported artifact, no consistency assertion, and no task that genuinely exercises the composed seam — `npm test` cannot execute a Python module. *Disposition: dissolves under the restart.*
4. **Coverage — R2 verified nowhere.** Sole consequence of #1/#2; discharged by the same fix.

### Confirmed concerns (feed the re-plan, non-blocking)

- **T3/T4:** `expected_signal` is a verbatim restatement of `criteria`; no restart fixture in T3 (a write-through in-memory cache could pass), no per-IP discriminating fixture in T4 (a global counter could pass); `risk` absent on both where a real failure layer exists.
- **Signal anchoring:** all four `expected_signal` fields are unanchored prose, not pass-patterns.
- **Assurance challenge (recorded by both judges):** if this rate limiter is an abuse/brute-force **security control**, the security escalator forces ≥A3 and `risk_class: "security"` — which mechanically floors every contract at `adversarial` and invalidates the current `standard`/`independent` pairs. Worth an explicit call from you in the re-plan.
- **T1 is the plan's one healthy contract** — its negative cases genuinely exercise the trust-proxy layer; keep them.

**Bottom line:** Layer 1 PASS, Layer 2 BLOCKER confirmed by two independent passes. Per policy the C5 contradiction prescribes a **plan restart** (chiefly: the sliding-window counter must be a Node artifact on the Redis store, with an acceptance command that actually runs parallel writers and asserts an exact count). You asked me not to rewrite the plan, so I haven't — say the word and I'll draft the restart, re-gate it, and only then dispatch workers.
