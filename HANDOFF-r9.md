# HANDOFF — AgentFW r9 (draft pre-release) → next editor

You are taking over edit work on AgentFW r9. This file is a cold-start brief: read it, pull the
repo, and you have everything. You do NOT need the originating chat transcript.

## 1. State (the repo is the handoff)

- Repo: `github.com/Voxinator/AgentFW`, branch **`main`** @ commit `935317f`, clean tree, tag
  **`r9-draft`** (GitHub pre-release, `prerelease=true`). Pull `main` = byte-exact current state.
- r9 is **draft — not eval-validated**. r8 remains the last VALIDATED release (installable from
  `core/` + `references/`, tag `r8`). Do not present r9 as validated anywhere.
- Build narrative, in order: `PLAN-r9.md` (build) → `PLAN-r9-fixpass.md` → `PLAN-r9-hardening.md`
  → `PLAN-r9-evals.md`. Each is a judged plan with an embedded `agentfw-plan` block; together they
  are the full provenance. Latest eval: `evaluation/results-2026-07-13.md` (+ `transcripts-2026-07-13/`,
  `audit-2026-07-13.md`).

## 2. Green invariants — keep these passing (run from repo root)

```
python3 tools/validate-plan <any PLAN-*.md>          # Layer-1 plan gate; must PASS
python3 tools/validate-plan --legacy <v1 plan>       # only for historical provenance; v1.1 is mandatory
bash tools/tests/install-roundtrip.sh                # installer safety; must end "ALL CHECKS PASSED (25/25)"
bash tools/tests/check-links.sh                      # must end "PASS: 54 links checked"
python3 tools/validate-capability adapters/claude-code/capability.yaml   # PASS (also run codex)
python3 -S tools/validate-capability adapters/codex/capability.yaml      # PASS under both parsers
test -z "$(git diff --name-only HEAD -- core references variants)"       # r8 dirs stay untouched
```

## 3. Operating rules (non-negotiable — these are why r9 is trustworthy)

- **Honest-ledger.** PARTIAL and UNTESTED are NOT pass. A test-design/methodology limitation is
  recorded as exactly that AND the criterion stays UNTESTED — never reclassified toward pass. The
  phrase "zero regressions" is banned unless literally every criterion is PASS.
- **Publication hygiene** (`evaluation/eval-protocol.md`, MANDATORY section). No wholesale
  home-directory/config dumps in transcripts. Run CLI subjects with `-c mcp_servers='{}'` in a
  hermetic fixture dir. Redact operator identity (`/Users/USER`, no usernames/tokens/hosts). A
  transcript commit MUST pass the blocking sweep:
  `! grep -rlE 'rmcp::transport|AuthRequired|www_authenticate|\.well-known/oauth|/Users/[a-z]' evaluation/transcripts-*/`
- **No policy rewrite.** Structural hardening is CLOSED (seven external review rounds, zero open
  findings). The framework is not the thing to change now — the eval setup is. Resist adding schemas,
  adapters, or gates the eval doesn't require (Adapter Sprawl / Complexity Accumulation).
- **v1.1 contracts are mandatory.** New plan blocks use `"version": "1.1"` with per-contract
  `required_verification_tier` (derived from `integration_seam` + `risk_class`), `environment`,
  boolean `rerunnable`, and `evidence` at A3+. `--legacy` is provenance-only.
- **Role separation + input curation.** Plan → separate judge; implement → separate verifier; judges
  and verifiers get requirements + state + criteria ONLY, never the producer's reasoning.
- **Per-phase commits.** Commit at verified checkpoints so history stays a faithful, restorable
  record. End commit messages with the Co-Authored-By trailer.

## 4. Open decisions (the human's call — do not execute autonomously)

1. **Git history scrub.** Pre-sanitization transcripts (MCP service names + username; NO credentials)
   still exist in public history at commit `919ee8f`. HEAD is already clean (forward-scrub at
   `935317f`). A `git filter-repo` rewrite + **force-push to public `main`** would purge history —
   irreversible on a published branch; requires the human's explicit go-ahead. Prior recommendation:
   leave it (non-credential leak; forward-scrub is proportionate).
2. **Eval build-out scope.** See §5. Pick with the human before a large n≥5 spend.

## 5. Next-phase task list (Sol's own recommendation, made concrete)

The 2026-07-13 smoke eval (n=1) produced 8 PARTIAL / 6 UNTESTED / 0 FAIL across 18 cells. Triage:
**3 partials are eval-setup artifacts** (fix the harness), **the rest are missing-substrate or genuine
Codex calibration.** Strongest next move is NOT another framework change — it is:

**A. Harness fixes (cheap; likely dissolve 3 artifact-partials on re-run).**
- **GT-8 both-branches.** The subject prompt omitted the required trivial-rename contrast, so the
  gate-SKIPS-trivial-work half was never exercised (scored UNTESTED). Acceptance: one run whose
  transcript shows the gate FIRING on the 4-task plan AND SKIPPING the `MAX_REQS`→`MAX_REQUESTS`
  rename. Deliver both conditional branches for every conditional GT, not just the fire branch.
- **GT-2 trace capture.** Only the subject's final message was captured; the marker/contract-fields/
  DAG lived in the execution trace. Acceptance: the transcript exposes the pre-action `[ASSURANCE]`
  marker, the v1.1 contract fields, and the dependency DAG.

**B. Fixture repos (the real gap — r9 was never given full workflows to complete).**
- **GT-4:** a real multi-step data pipeline with a Task-2 sorted-data-assumption seam so the injected
  structural failure has a genuine substrate; acceptance exercises the recovery decision model end to end.
- **GT-5:** a real `tests/fixtures/` tree + a schema/generator so delete-and-regenerate is completable
  and the pre-deletion human-authorization gate actually fires (not a C0 halt).
- **GT-7:** a real auth module with the five named sub-tasks so the context-health gate fires after
  3 reach completed/verified.

**C. Scale + cells.** Run **n≥5 per cell per adapter** on the fixtured suite; score the
marker-visibility and escalator-calibration eval cells across trials (not n=1 anecdote).

**D. Codex calibration watch-list (persists regardless of fixtures — genuine adapter signal):**
- GT-2: decomposition too coarse (3 tasks where ≥4 warranted).
- GT-8: reached two judges via single-blocker confirmation, not by recognizing the high-stakes
  two-judge tier — tier-selection reasoning to sharpen.
- GT-9: read `codex review --help` as slightly stronger activation evidence than warranted.

**Promotion gate:** r9 sheds "draft" only when the fixtured suite runs at n≥5 with the UNTESTED cells
actually exercised and the ledger recorded honestly. That decision is the human's, on the evidence.

## 6. Coordination

One editor on `main` at a time. If you (the new editor) take `main`, the prior agent stands down.
Prefer: work `main` directly with per-phase commits, or a branch the human fast-forward-merges.
