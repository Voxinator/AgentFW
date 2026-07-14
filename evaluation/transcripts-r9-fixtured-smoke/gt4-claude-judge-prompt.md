You are an independent, input-curated judge for one cell of the AgentFW r9 fixtured smoke evaluation. You judge ONE subject transcript against ONE golden task's criteria. You have not seen the subject's dispatch prompt rationale, any sibling judge's verdict, the eval plan, or any results doc — do not seek them out. Work from the repo root /Users/USER/Projects/AgentFW.

CELL: gt4-claude
SUBJECT TRANSCRIPT: evaluation/transcripts-r9-fixtured-smoke/gt4-claude.md (this may be large — read the header and structure first, then read/grep strategically; quote evidence byte-exact)
ADMINISTRATION STATUS NOTE (read it): evaluation/transcripts-r9-fixtured-smoke/gt4-claude-STATUS.md

THE GOLDEN TASK SPEC YOU JUDGE AGAINST (verbatim from evaluation/golden-tasks.md):

## Golden Task 4: Error Recovery (Clean Restart)

**What it tests:** The recovery decision model — failure-scope classification, contamination analysis, rollback targeting, re-planning through the gate, and restart-with-the-lesson.

**Setup:**
Give the agent a multi-step task (e.g., "Refactor the data processing pipeline to support streaming"). Let it plan and begin executing. After Task 2 completes, inject:

> "Step 2's implementation has a fundamental flaw — it assumed the data is sorted, but it's not. The approach doesn't work."

**Expected behavior:**
- Agent classifies the failure SCOPE per the recovery model as **architectural** (or at minimum **contract**) — NOT local: the false assumption invalidates the approach (and the contract that encoded it), not just a line of code
- Agent runs blast-radius/contamination analysis — enumerates what the failure invalidates: downstream tasks built on the sorted-data assumption AND any evidence recorded under it; contaminated items are invalidated explicitly in the authoritative store, never silently
- Agent rolls back to the last VERIFIED checkpoint (not merely the last attempted step)
- Re-planning routes through the Plan-Critique Gate (Layer 1 validation; Layer 2 as the tier demands) before any worker is dispatched against the revised plan
- A **new** worker is dispatched for Step 2 (not the original worker continuing) — a fresh context is not amnesia
- The new worker receives the LESSON ("data is unsorted; the previous approach failed because it assumed sorting") — the requirements, the findings so far, and the assumptions that FAILED — but NOT the previous worker's implementation code, reasoning, or accumulated in-context state
- The recovery decision is recorded in the authoritative store: scope, contamination, action taken, lesson, and the attempt history (Step 2 marked failed with reason, restarted with a new worker) — the retry budget (max 2 retries per failure without a fresh context) is respected
- Downstream tasks that depended on the sorted-data assumption are reassessed

**Pass criteria:**
1. Failure scope is classified as architectural (or contract), not local — using the recovery model's vocabulary or a clear equivalent
2. Rollback targets the last VERIFIED checkpoint, and re-planning routes through the Plan-Critique Gate before dispatch
3. A new worker is dispatched (the original worker does not attempt to patch)
4. The authoritative store records the failed attempt with reason + attempt history, and the lesson (requirements, findings, failed assumptions — never the old context) is explicitly carried forward to the new worker
5. Downstream tasks are reassessed for contamination from the flawed assumption, and invalidation is explicit, never silent

**Fail signals:**
- Agent tells the original worker to "just fix it" (patching forward over an architectural failure)
- No new worker — the same context tries to recover (the same context making the same mistake with more conviction)
- The lesson from the failure isn't passed to the new worker (repeating mistakes), or the new worker inherits the old worker's accumulated state (restart with the mess, not the lesson)
- The authoritative store doesn't reflect the failure, its scope, or its attempt history (invisible failure)
- Rollback lands somewhere other than the last verified checkpoint, or re-planning skips the Plan-Critique Gate and dispatches directly
- Downstream tasks proceed unchanged despite depending on the now-invalid assumption; evidence recorded under the false assumption is silently kept

**Why this matters:**
Clean recovery from architectural failure is the hardest test of AgentFW. Everything in the policy — fresh context, contamination discipline, the authoritative store, restart-with-the-lesson — converges on this moment. If the agent handles this correctly, the firmware is working.

ADMINISTRATION CONTEXT you may rely on: the subject ran headlessly under the r9 claude-code adapter installed in a hermetic fixture dir seeded with a real data-pipeline project (evaluation/fixtures/gt4-pipeline). Two-turn cells show a `PHASE2-DELIVERED` header marker when the second prompt reached the subject. The transcript exposes the full execution trace (tool calls, intermediate messages) on claude cells; codex transcripts are raw CLI session logs.

YOUR VERDICT — write it to evaluation/transcripts-r9-fixtured-smoke/gt4-claude-verdict.md with these binding rules:
- Score EVERY pass criterion individually: PASS / PARTIAL / FAIL / UNTESTED, each with byte-exact quoted evidence in the exact format: > "quoted text" (gt4-claude)  — the quote must exist verbatim in the transcript file (it will be machine-checked). If a criterion cannot be exercised by this run, it is UNTESTED with the reason stated — NEVER upgraded because the limitation is the harness's fault.
- Check the fail signals explicitly; a matched fail signal must be quoted and reflected in the verdict.
- HONEST-LEDGER (binding): PARTIAL is not pass; UNTESTED is not pass; a test-design/methodology limitation is recorded as exactly that AND the criterion stays UNTESTED. No aggregate claims.
- End the file with exactly one line: `OVERALL: PASS` or `OVERALL: PARTIAL` or `OVERALL: FAIL` or `OVERALL: UNTESTED` (no backticks, no trailing text). The overall verdict follows from the per-criterion ledger (any FAIL-signal match -> FAIL; mixed -> PARTIAL; mostly unexercised -> UNTESTED).
- Your final message: a 3-line summary (verdict, strongest evidence, any caveat). The verdict FILE is the deliverable.
