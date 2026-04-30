# r7.11 — Hermes variant of AgentFW (internal RC)

This directory contains the **r7.11 milestone of the Hermes variant of AgentFW**. AgentFW is the parent product (architecture and roadmap live elsewhere); the Hermes variant is one implementation of AgentFW concepts against [Nous Research's Hermes](https://nousresearch.com/) substrate. r7.11 is a variant milestone, not a parent-product milestone.

**Status**: internal RC (release candidate). 3/5 strict completion at item 9 (n=5 confirmation on the T6 capability-curve workload). Reliability rate cleared the pre-committed RC threshold.

**Tag**: `hermes-r7.11-rc1`. **Branch**: `hermes-r7.11-internal-rc`. Not merged to `main`; sits as a stable variant milestone.

---

## What this is

r7.11 is the verified-state multi-session resumable architecture for Hermes-driven, parent-decomposed long-horizon coding tasks. It addresses the **synthesis-trust gap** surfaced in r7.5–r7.10: parents could produce code that passed static checks (presence, syntax, imports, wiring) while the actual acceptance criterion silently failed. The architecture closes that gap by:

- Splitting work into phases with a machine-authoritative state file (`verified-state.json`) as the exclusive cross-session channel
- Driving each phase as its own Hermes session via a thin Python wrapper (`hermes_multi.py`)
- Verifying phase deliverables in tiers (presence, syntax+imports, wiring, opt-in runtime smoke, **execution-tier acceptance-runner**)
- Teaching the parent to declare verifiable acceptance commands per phase via tool-description teaching

The campaign question — *does r7.11 close the synthesis-trust gap on T6-class workloads?* — is empirically answered **yes**: 0/5 trials reproduced the failure mode; every successful trial had perfect verifier-acceptance alignment.

---

## What's in this commit

### Source modules (the firmware)

- `verified_state.py` — schema + read/write helpers for `verified-state.json` (machine-authoritative phase state)
- `verify_phase.py` — verification engine; tiers 1 (presence), 2 (syntax+imports), 3 (wiring), opt-in 3.5 (importlib runtime smoke), **3.7 (acceptance-runner)**
- `verify_phase_tool.py` — orchestrator; PLAN.md parser; Hermes tool definition constants
- `handoff_tools.py` — `end_session_for_handoff` + `escalate_to_operator` Hermes tool definitions
- `hermes_multi.py` — wrapper substrate; state machine; transport abstraction (LocalProcess + Ssh)
- `content_verify.py` — strict/charitable scoring rubric used for trial scoring (separate evaluator from `verify_phase`)
- `probe-r7.11-stage.sh` / `probe-r7.11-unstage.sh` / `smoke-r7.11.sh` — stage/unstage/smoke scripts using the `.probe-r7.11-orig` backup convention
- `r7_11_lib/__init__.py` — package init for the staged-on-VM library

### Tests (227 total)

- `test_verified_state.py` (21), `test_verify_phase.py` (103), `test_verify_phase_tool.py` (26), `test_handoff_tools.py` (14), `test_hermes_multi.py` (26), `test_content_verify.py` (21), `test_probe_r7_11.py` (16)

### Design + reference docs

- `DESIGN-r7.11-architecture.md` — original architecture sign-off doc (six sections + appendix)
- `HANDOFF-r7.11-current.md` — campaign-close runbook with full trial-by-trial evidence trail
- `SCHEMA-verified-state.md`, `VERIFY-CONFIG-SCHEMA.md`, `SENTINEL-SCHEMAS.md` — schema references
- `PHASE-AWARENESS-NOTE.md`, `TIER3-NOTES.md`, `TIER35-NOTES.md` — implementation notes
- `HOWTO-r7.11-stage.md`, `HOWTO-r7.11-multi.md` — operator how-to docs
- `r7.x-followups.md` — followup ledger (F-1 through F-12 with closure status — 6 closed in r7.11, 6+2 deferred to r7.12)

### Cross-r7.10 dependencies

- `../r7.10/write_plan_md.py.r7.10-min` — minimum-mechanism PLAN.md authoring tool from r7.10; r7.11 carries it forward via the stage script. Tool description is the load-bearing teaching surface (parents internalize the format from the description text without needing the tool call to succeed — same r7.10 finding that motivated r7.11 design).
- `../r7.10/scaffold-baseline/` — the baseline scaffold a trial reset restores from. Includes the F-9 part C convention (docstring-only stubs) + `CONVENTION.md` documenting the convention.

### NOT in this commit (deferred to a separate session)

- Trial archives (`item8-trial-{1..4d,5.1..5.5}-archive/`) — 12 archives, full session evidence (PLAN.md, verified-state.json, .session-archive/ with manifest + per-session JSONs + stdout/stderr)
- Trial reports (`REPORT-r7.11-item8-trial-{1,2,4b}.md`, `REPORT-r7.11-item8-trial-4cd-reproducibility.md`, `REPORT-r7.11-item9-n5.md`)
- Smoke reports

These are research-methodology artifacts. Whether they get committed depends on whether r7.11 is positioned as personal infrastructure (private) or research artifact (public with evidence). Deferred decision.

---

## Architectural patterns vs Hermes-specific implementation

### AgentFW-portable findings (these inform AgentFW core)

These are the architectural patterns that should generalize beyond Hermes; future variants of AgentFW would re-implement them against their target substrate:

- **Verified-state-between-phases as the synthesis-trust mechanism.** The parent's narrative is non-authoritative; a machine-readable state file (here `verified-state.json`) is the exclusive cross-session source of truth. Wrapper routing decisions read from the state file; parent updates to it are validated through the verifier tool, not accepted on narrative claim.
- **Execution-tier verification (the tier 3.7 pattern) closes static-only verification gaps.** Static checks (presence, syntax, imports, wiring) are necessary but not sufficient. An execution-tier that runs the phase's stated acceptance criterion in a controlled subprocess catches synthesis-fabrication that static analysis cannot.
- **Wrapper-as-dumb-substrate / parent-as-orchestrator architecture.** The wrapper does not interpret the work; it polls sentinels, archives sessions, and routes based on the state file. The parent is the planner. This separation keeps the wrapper small (a few hundred LOC of state-machine + transport) and the parent's autonomy intact.
- **Tool-description teaching as the working doctrine-delivery mechanism.** Loud HERMES.md doctrine reaches the parent at 0% in pre-r7.11 measurements; teaching embedded in tool descriptions reaches the parent at 60-100% (r7.10 finding, validated again across n=5 in r7.11). Variants should embed teaching in tool descriptions, not in system prompts or external doctrine docs.
- **Sentinel-file-driven session boundaries with file-authoritative state.** Sessions don't need IPC; a sentinel file written by the agent + polled by the wrapper is sufficient. This gives the architecture cross-platform portability and degrades gracefully when more sophisticated session-management primitives aren't available.
- **Tiered verifier with structured exit-code interpretation.** Tier 3.7's `[ACCEPTANCE_PASSED]` / `[ACCEPTANCE_FAILED:N]` / `[ENVIRONMENT:reason]` / `[INCONCLUSIVE:reason]` distinction was load-bearing in trial 4b — without the ENVIRONMENT/ACCEPTANCE_FAILED split, a failed environment-side issue would have been mistaken for a real test failure and consumed parent-recovery budget on the wrong axis.

### Hermes-variant-specific implementation (do NOT generalize without substrate knowledge)

These are mechanics that are specific to Hermes' implementation choices. Other AgentFW variants would solve the same problems differently against their own substrate:

- The `_session_messages_live` patch on `run_agent.py` (Hermes-internal session JSON shape; not a public API)
- The parser-bug workaround (`json.dumps` in shim returns) — Hermes' tool dispatch path expects `str` returns; non-string returns trigger a slice error in the OpenAI-compatible API call
- The Hermes tool registration mechanics in `toolsets.py` + `model_tools.py` (Hermes registers tools via two cooperating files; r7.11 patches both during stage)
- SessionDB regression workarounds (Hermes' SQLite session DB stopped accepting writes around 2026-04-25; r7.11 routes around it via the file-authoritative state model and JSON-only session archiving)
- The `.probe-r7.11-orig` backup convention — Hermes' canonical install lives at `~/.hermes/hermes-agent/`; the stage script backs up the four files it touches before mutating
- Stage/unstage script structure specific to Hermes' file layout (`tools/r7_11_lib/` library + 3 thin shims at `tools/r7_11_*.py` + carry-forward `tools/write_plan_md.py`)

---

## How to read the tree (cold-start)

1. **Start with `HANDOFF-r7.11-current.md`** — the campaign-close runbook. Has the TL;DR, full chronological campaign arc (every trial outcome), build state, final canonical VM state with baseline md5s, followup closure status, hard constraints, and cold-start checklist.
2. **For the architecture: `DESIGN-r7.11-architecture.md`** — the original sign-off design doc. Six sections: preamble (synthesis-trust framing), lifecycle, tool surface, state artifacts, wrapper substrate, failure modes.
3. **For followups: `r7.x-followups.md`** — F-1 through F-12 with closure status. CLOSED in r7.11: B1 (F-5 resolution), F-4, F-7, F-8, F-9 part B + part C, F-11. DEFERRED to r7.12: F-1 (Hermes SessionDB regression), F-2 (registry.dispatch upstream), F-10 (tier-3.5 path-walker), F-12 (content_verify rubric noise), plus 2 new from n=5 (parent-recovery quality, bootstrap-handoff ceremony).
4. **For the empirical baseline (in deferred-commit material): `REPORT-r7.11-item9-n5.md`** — the full n=5 report. Pre-committed interpretation thresholds, distribution of revision counts / wall-clock / phases-chosen / failure modes, architecture validation summary across all 5 trials.

---

## Reproduction prerequisites (if running trials)

- Hermes installed at canonical path (`~/.hermes/hermes-agent/`) — see Hermes documentation for setup
- Python 3.11 (Hermes' base Python version; scaffold venvs must match for ABI compatibility — F-6)
- Local-dev oMLX or equivalent OpenAI-compatible inference endpoint. Auth via `~/.hermes/config.yaml` (`api_key:`) on the VM by default; `OMLX_API_KEY` env var only needed to override
- Read access to a scaffold dir (e.g. `/tmp/scaffold/`); scaffold must contain `USER-PROMPT.md`, `verify-config.json`, and a `.venv/` matching Hermes' Python version
- ssh access to the Hermes-running host (or LocalProcessTransport for VM-local execution)

Stage with `bash probe-r7.11-stage.sh stage` (uses `.probe-r7.11-orig` backup convention). Unstage with `bash probe-r7.11-unstage.sh`. Smoke-test with `bash smoke-r7.11.sh`.

---

## License + provenance

Internal research artifact. Tag `hermes-r7.11-rc1` marks this milestone. r7.12 architecture review is the next planning milestone (not started yet).

The campaign that produced r7.11 ran 2026-04-26 → 2026-04-30: design (1 day), build (3 days, items 0-7 + extensions), item 8 (T6 trials 1-4d, 4 days surfacing 6 closed and 6 deferred followups), item 9 (n=5 confirmation, 1 day), cleanup (HANDOFF + unstage + memory + this commit). Total ~5 days from design sign-off to internal RC.
