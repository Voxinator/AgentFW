# ARTIFACT — Wave-2 Verifier Judgment (r7.3 IMPL-1..4)

**Judge:** Wave-2 Verifier (cold context, no implementation history).
**Date:** 2026-04-18
**Mode:** READ-ONLY. No edits, no probe runs.
**Scope:** Verify the four IMPL artifacts (Layer 1 toolset restriction, Layer 2 escape-hatch removal, Layer 3 β-fuse spec, Layer 4 SOUL/USER/MEMORY restructure proposal) before authorizing Wave-3 probes.

---

## 1. Per-artifact verification table

| IMPL | Claim | Verified? | Defects |
|---|---|---|---|
| 1 | `file_readonly` toolset present on VM with `read_file` + `search_files` | **YES** — live `python3 -c "import toolsets"` returns the entry, `resolve_toolset` returns `['read_file','search_files']` | None |
| 1 | Wrapper has TOOLSETS env-var passthrough on initial AND retry invocations | **YES** — `grep -n` shows `TOOLSETS_FLAG` at lines 27–32 (init), 130 (banner), 156 (initial invocation), 225 (retry invocation) | None |
| 1 | `bash -n` parses cleanly | **YES** — `PARSE_OK` | None |
| 1 | VM backup `toolsets.py.probe-r7.3-orig` exists | **YES** — `21316 Apr 18 19:33` (also `.probe-d-orig` from earlier still preserved at `21240 Apr 18 00:06`) | None |
| 1 | Mac backup `probe-variantE-wrapper.sh.pre-r7.3-orig` exists | **YES** — `10879 Apr 18 19:33` | None |
| 1 | Smoke session `20260418_193428_bf0423` shows 6 tools, gemma model, no mutator tools | **YES** — `model: gemma-4-31b-it-4bit`, 6 tools: `clarify, delegate_task, delegate_worker, read_file, search_files, todo`. No `patch/write_file/terminal/execute_code/skill_manage` | None |
| 2 | HERMES-variantE.md exists at `variants/hermes/` | **YES** — file present | None |
| 2 | Header rewritten to "Variant E — Escape-Hatch Stripped" | **YES** — diff line 1 confirms | None |
| 2 | Mid-response self-correction line replaced ("re-classify" → "dispatch a worker") | **YES** — diff line 82 confirms exact substitution | None |
| 2 | "When NOT to use delegate_worker" reduced to one-shot only | **YES** — diff removes lines 142–143 (quick factual / single-tool-call bullets); only one bullet (`one-shot`) remains | None |
| 2 | "Role separation can be relaxed ONLY when" reduced to one-shot only | **YES** — diff removes lines 154–157 (trivial mechanical / quick lookups / human co-driving); only `one-shot` remains | None |
| 2 | HARD RULE: Role Separation block UNCHANGED | **YES** — variantE lines 94–105 are byte-identical to variantD (`(no diff in this range)`) | None |
| 2 | Imperative tightening added in HOW TO DISPATCH WORKERS opening | **YES** — diff line 111 confirms "Structured tasks dispatch via `delegate_worker`; no exceptions outside `one-shot`." inserted | None |
| 2 | Wrapper `correction_for()` NO_DISPATCH text changed | **YES** — line 103 reads "Dispatch is mandatory for this class. Re-classification is not an option here." Old "If you truly believe…re-classify…" string is GONE (`grep "re-classify to"` returns 0 hits) | None |
| 2 | Backup `probe-variantE-wrapper.sh.pre-r7.3-l2-orig` exists | **YES** — `10879 Apr 18 19:33` (note: md5-identical to `pre-r7.3-orig`; both capture pre-IMPL-1+pre-IMPL-2 baseline) | Minor — see §6 |
| 2 | IMPL-1's TOOLSETS feature still present (not reverted) | **YES** — all 6 TOOLSETS_FLAG/TOOLSETS_ENV references intact (lines 27–32, 130, 156, 225) | None |
| 3 | Spec is design-only, no file mods outside the artifact | **YES** — no new files created in `variants/hermes/` matching `delegate_worker_v2*`, no `probe-variantF-*` files, no edits to HERMES.md | None |
| 3 | Schema includes `classification` (enum) + `justification` (≥30 chars) + conditional `goal` | **YES** — `enum: [one-shot, structured, long-horizon]`, `minLength: 30` on justification, `goal` documented as conditionally required by handler (not JSONSchema, deliberate) | None |
| 3 | check.py changes documented (classification source detection, gate flow, diagnostics) | **YES** — §3 documents `extract_classification`, `ALL_DISPATCH_TOOLS`, new gate flow, `v2_was_first_tool` diagnostic | None |
| 3 | Migration plan is side-by-side (not big-bang) | **YES** — §5 explicitly recommends side-by-side with phased deprecation; Big bang and schema-update-in-place documented as rejected alternatives | None |
| 3 | "When to deploy" gate is conditional on Layers 1+2 outcome | **YES** — §7 lists explicit thresholds (dense ≥7/15, MoE ≥4/15) below which Layer 3 deploys; above which it is skipped. Not a unilateral "deploy now" recommendation | None |
| 4 | Read-only — no files modified | **YES** — no edits to SOUL.md, USER.md, MEMORY.md, run_agent.py | None |
| 4 | Three options proposed (A reorder, B compress, C merge) | **YES** — §4 enumerates A (with A1/A2 sub-variants), B, C with cost/risk/reversibility for each | None |
| 4 | Recommendation is A2 (HERMES.md after PLATFORM_HINTS) — cheapest + safest | **YES** — §5 Pareto-win argument explicitly recommends A2 first, B as follow-up, C as fallback | None |
| 4 | User-decision questions exist for things needing operator input | **YES** — §6 has 8 explicit questions to user covering sacred-line confirmations, conceptual-separation choice, rolodex migration, household-task move, error-handling-directive relocation, config-fix archiving, PLATFORM_HINTS retention, A2-vs-A1 placement preference | None |

**Per-artifact verdict:** All four IMPLs verified. Zero defects. Spot-checks read the actual files (HERMES-variantD/E.md, the wrapper, the smoke-test session JSON) rather than trusting artifact summaries.

---

## 2. Scope-compliance verification (file-by-file)

| Path | Status | Evidence |
|---|---|---|
| `core/harness-core.md`, `core/permissions.md` | **UNTOUCHED** | mtimes Apr 17 16:40 and Apr 4 13:31 — predate r7.3 work (today is Apr 18 evening) |
| `references/*.md` (7 files) | **UNTOUCHED** | newest mtime is Apr 17 16:41 (`prompt-design.md`, `state-management.md`); none later |
| `playbooks/*.md` (5 files) | **UNTOUCHED** | newest mtime Apr 6 15:45 |
| `templates/*` (5 files + launch-prompts/) | **UNTOUCHED** | newest mtime Apr 10 17:27 |
| `variants/claude-code/`, `variants/claude-projects/`, `variants/generic/` | **UNTOUCHED** | `git status` shows no modifications |
| `variants/hermes/HERMES-variantD.md` | **UNTOUCHED** | mtime `Apr 18 00:06` (predates IMPL work today); md5 stable; full file diff'd against staged VM HERMES.md md5 confirms it matches the deployed Variant D bytes |
| `variants/hermes/HERMES.md` (canonical) | **UNTOUCHED** | mtime not modified by IMPL work; tracked in git as separate file from variantD/E |
| `variants/hermes/delegate_worker.py` | **UNTOUCHED** | mtime `Apr 18 00:05`; untracked file in git status (predates today's work); IMPL-3 spec only mentions edits as part of *future* deployment |
| `variants/hermes/HERMES-variantE.md` | **NEW (in scope)** | created by IMPL-2 as a sibling of variantD, per Layer-2 spec |
| `probe-variantE-wrapper.sh` | **MODIFIED (in scope)** | both IMPL-1 (TOOLSETS env var) and IMPL-2 (correction text) modifications coexist |
| `probe-variantE-wrapper.sh.pre-r7.3-orig`, `…pre-r7.3-l2-orig` | **NEW backups (in scope)** | both md5-identical (`9fd987c5…`); both capture pre-IMPL-1 baseline |
| `~/.hermes/hermes-agent/toolsets.py` (VM) | **MODIFIED (in scope)** | added `file_readonly` entry; `.probe-r7.3-orig` backup created; older `.probe-d-orig` preserved |
| `~/.hermes/hermes-agent/HERMES.md` (VM, deployed) | **UNTOUCHED** | md5 = `4477b8ee1d87c3a3afa9e8646168841f` (matches expected baseline; matches HERMES-variantD.md staged content) |
| `~/.hermes/SOUL.md`, `memories/USER.md`, `memories/MEMORY.md` (VM) | **UNTOUCHED** | IMPL-4 was read-only by spec; no evidence of modification |

**Scope verdict:** PASS. No out-of-scope file was modified. The only writes were to the four explicitly authorized targets: VM `toolsets.py`, host `probe-variantE-wrapper.sh`, new `HERMES-variantE.md`, and the four ARTIFACT-* documentation files themselves.

---

## 3. Live state verification

```
$ ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md'
4477b8ee1d87c3a3afa9e8646168841f  /home/parallels/.hermes/hermes-agent/HERMES.md
```
**Match:** expected `4477b8ee1d87c3a3afa9e8646168841f`. Variant D is the staged production HERMES.md on the VM. No drift from the baseline established earlier in the staging chain.

```
$ ssh ubuntu-vm 'md5sum <tripwires>'
5503ee1c2ef7d635a020eea275e41239  …/useDashboard.ts
a1dce6e989527686124d0860830627c9  …/jira-briefing.sh
fb1a5a5208a6cf2fcb8252aac10397eb  …/SKILL.md
```
**All three tripwires match expected baselines.** No collateral mutation from any IMPL worker.

```
$ ssh ubuntu-vm 'python3 -c "import toolsets; print(\"file_readonly\" in toolsets.TOOLSETS); ..."'
True
{'description': 'Read-only file tools…', 'tools': ['read_file', 'search_files'], 'includes': []}
resolved: ['read_file', 'search_files']
```
**Live `file_readonly` toolset confirmed on VM.** Resolves to exactly the two intended tools.

```
$ bash -n /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh && echo PARSE_OK
PARSE_OK
```
**Wrapper parses cleanly** with both layers' edits coexisting.

Smoke-test session `20260418_193428_bf0423`:
- model: `gemma-4-31b-it-4bit` (matches request)
- tools count: 6
- tools: `['clarify', 'delegate_task', 'delegate_worker', 'read_file', 'search_files', 'todo']`
- mutator tools (`patch/write_file/terminal/execute_code/skill_manage`) **all absent** ✓

---

## 4. Wave-3 readiness assessment

### Layer 1 only probe (TOOLSETS env restricts surface; HERMES = variantD)

| Prerequisite | Status |
|---|---|
| TOOLSETS env-var works in wrapper | **READY** — confirmed via smoke test |
| `file_readonly` toolset registered on VM | **READY** — live import check passed |
| HERMES.md staged on VM (variantD content) | **READY** — md5 `4477b8ee…` matches baseline |
| Wrapper parses, retries propagate flag | **READY** — `bash -n` + line-225 grep confirm |
| Smoke-test path COMPLIANT in 1 attempt | **READY** — `OUTCOME ... RESULT=COMPLIANT attempts=1 elapsed=23s` |

**Verdict: Layer-1-only probe can run immediately.** No staging step required.

### Layer 1+2 stacked probe (TOOLSETS env + variantE HERMES + new correction text)

| Prerequisite | Status |
|---|---|
| Everything from Layer 1 | **READY** |
| `correction_for()` NO_DISPATCH text replaced | **READY** — line 103 confirmed |
| HERMES-variantE.md exists locally | **READY** |
| **HERMES-variantE.md DEPLOYED to VM** | **NOT READY** — file is sibling on Mac only; VM HERMES.md still bytes-of-variantD |

**Deployment step required before Layer 1+2 probe:**

```bash
# 1. Backup current VM HERMES.md (which is variantD bytes) for surgical rollback
ssh ubuntu-vm 'cp ~/.hermes/hermes-agent/HERMES.md ~/.hermes/hermes-agent/HERMES.md.pre-r7.3-l2-stage'

# 2. Stage variantE on VM
scp /Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantE.md \
    ubuntu-vm:/tmp/HERMES-variantE.md
ssh ubuntu-vm 'cp /tmp/HERMES-variantE.md ~/.hermes/hermes-agent/HERMES.md'

# 3. Verify md5 changed (expect 42b8ed602c1cc601bbc5f3189c915355 — variantE local md5)
ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md'

# 4. After Layer 1+2 probe completes, rollback to variantD:
ssh ubuntu-vm 'cp ~/.hermes/hermes-agent/HERMES.md.pre-r7.3-l2-stage ~/.hermes/hermes-agent/HERMES.md'
ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md'  # confirm 4477b8ee… returns
```

The local md5 of HERMES-variantE.md is `42b8ed602c1cc601bbc5f3189c915355`. After step 2 the VM should report this same md5; after step 4 it should report `4477b8ee…` (variantD).

---

## 5. Recommended Wave-3 dispatch order

**Probe Layer 1 alone first, then Layer 1+2.**

Rationale (concurring with Worker θ judge):

1. **Signal isolation.** Layer 1 changes the *tool surface*; Layer 2 changes *prompt content*. Running them stacked first makes it impossible to attribute a delta to either layer individually. If Layer 1 alone moves the needle (dense first-attempt jumps), Layer 2 marginal value can be measured cleanly. If Layer 1 alone underperforms, Layer 2 is the next swing — without confounding.
2. **Cheaper rollback at each gate.** Layer 1 needs no HERMES.md re-stage; the toolset entry is live and idempotent. Layer 1+2 requires the scp + cp + tripwire-verify cycle described above. Running L1 first means we don't pay that cost until we know L1 alone is insufficient.
3. **Faster feedback.** L1 probe time-to-first-result is ~10–15 minutes (probe matrix only). L1+2 adds the staging step on either side. Sequential gives us the L1 number sooner.
4. **β-fuse decision logic depends on disaggregated signal.** IMPL-3 §7 ties β-fuse deployment to whether L1+2 hit thresholds. Knowing which layer is doing the work matters for the Layer-3 go/no-go decision.

Concrete order:

1. Run r7.3 probe matrix (15 tasks × 2 models, both dense and MoE) with `TOOLSETS=delegation,todo,clarify,file_readonly` against current variantD HERMES.md. Record as r7.3-L1.
2. Compare to r7.2 baseline. Decide: continue to L1+2 stacked, or pause to investigate.
3. If continuing: stage HERMES-variantE.md on VM (commands in §4). Re-run probe matrix with same TOOLSETS env. Record as r7.3-L1+2.
4. Compare L1+2 to L1. Compute Layer 2's marginal contribution. Apply Layer 3 deployment logic per IMPL-3 §7.
5. Rollback HERMES.md on VM to variantD bytes after probe completes (commands in §4 step 4).

---

## 6. Risks / blockers

### Minor — not blocking, worth flagging

1. **Backup-file lineage clarification.** Both `pre-r7.3-orig` and `pre-r7.3-l2-orig` are md5-identical (both = `9fd987c5e18e6aa70a05426c473fc0a3`). IMPL-2's artifact (§ "Coordination with IMPL-1") says it created `pre-r7.3-l2-orig` because IMPL-1's backup wasn't found yet. In practice both backups capture the same pre-IMPL-1 + pre-IMPL-2 baseline. Surgical L2-only rollback (preserving L1) is therefore not possible by simple `cp` — it requires the manual edit IMPL-2 documented in its rollback procedure. This is a documentation point, not a defect; surgical rollback is documented but operator must follow the manual-edit path, not the cp path.

2. **`probe-variantE-check.py` not re-verified by this judge.** All four IMPLs left the check script unmodified. The smoke test indirectly confirms the script still parses sessions correctly (COMPLIANT verdict on a trivially-classifiable one-shot). For Wave-3 the existing check.py is what will gate the trials. No action; just noting that no IMPL claims to touch it and none did.

3. **Layer 2's new correction text is untested under failure conditions.** The smoke test's task ("What's the capital of France?") was COMPLIANT in 1 attempt — no NO_DISPATCH violation, so the new correction text was never sent. The new text is plausible English but its empirical effect on retry compliance is unmeasured. Wave-3 itself will be the first test of it. (This is the *purpose* of the probe; not a blocker, but worth being clear-eyed: we don't yet know that "Re-classification is not an option here" produces better retry behavior than "If you truly believe…re-classify…" did.)

### Not found — explicit non-issues

- No drift in protected dirs.
- No tripwire violations.
- No accidental modification of canonical HERMES.md, delegate_worker.py, or any production-trajectory variant.
- No undocumented file creation.
- All backups exist where claimed.
- IMPL-1 and IMPL-2 cleanly coexist in the wrapper without conflict.

---

## 7. Verdict: **GO** for Wave-3

All four IMPL artifacts pass verification. Spot-checks against the live VM, the wrapper script, the variantD/E HERMES files, and the smoke-test session JSON all confirm the artifact claims.

Recommended next action for the planner:

1. Dispatch Wave-3 Layer-1-only probe (15 tasks × 2 models) using the smoke-test command pattern with appropriate `MODEL` + `SOURCE_PREFIX=probe-r7.3-L1` and `TOOLSETS=delegation,todo,clarify,file_readonly`.
2. Hold Layer-1+2 staging until Layer-1 results are in hand.
3. If Layer 1+2 is dispatched, use the scp/cp procedure in §4 of this document for HERMES.md staging (and rollback).
4. Defer IMPL-3 (β-fuse) and IMPL-4 (slot reorder) deployment decisions until Layers 1+2 results are known, per IMPL-3 §7 and IMPL-4 §5.

No defects found. No scope violations. No live-state inconsistencies. **Wave-3 is cleared to proceed.**
