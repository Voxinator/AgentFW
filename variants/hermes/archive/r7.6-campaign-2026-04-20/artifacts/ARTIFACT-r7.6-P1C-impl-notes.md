[TASK CLASS: long-horizon]
Justification: Scaffold implementation + A/B probe matrix for r7.6 ship gate; part of multi-session campaign.

# ARTIFACT — r7.6-P1C implementation notes (HERMES-WORKER.md scaffold)

## Summary

P1-C delivers the only behavioral intervention in r7.6: a teaching doc
(`HERMES-WORKER.md`) injected into child-agent system prompts to fix the four
worker-quality failure modes that r7.5's F.2 probe quantified (3/20 PASS under
mechanical baseline). The scaffold is env-var-gated so we can A/B probe with a
clean on/off switch.

## Artifacts delivered

| Artifact | Path | Role |
|----------|------|------|
| Teaching doc | `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-WORKER.md` | 5-part child doctrine (plan-then-execute, stop-after-3, honest-blocked, turn budget, anti-fabrication) |
| Stage script | `/Users/briantaylor/Projects/AgentFW/probe-variantI-stage.sh` | Stage/unstage/status for delegate_tool.py patch + HERMES-WORKER.md upload |
| VM patch | `~/.hermes/hermes-agent/tools/delegate_tool.py` | `_build_child_system_prompt` modified to prepend overlay when env var set |
| VM doc | `~/.hermes/hermes-agent/HERMES-WORKER.md` | scp'd from local variants/hermes/ |
| Arm B wrapper | `/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh` | Variant F wrapper + HERMES_WORKER_OVERLAY=1 env injection (ARM=B) or no injection (ARM=A) |

## Design decisions

**Why fork to probe-variantI-stage.sh vs. extending probe-variantH-stage.sh:**
variantH's scope is mechanical runtime fixes (gemma_parser prefix-tolerance +
channel-marker pollution routing). variantI's scope is a new teaching doc
injected into child prompts — a behavioral overlay. Keeping them separate lets
us A/B probe with the env var as the single binary knob. Arm A = variantH
staged (mechanical fixes only, no overlay); Arm B = variantH + variantI
staged (mechanical + scaffold). No mid-run stage-script changes required.

**Why env-var gating vs. always-on:**
The A/B comparison requires a way to disable the overlay cleanly without
re-staging. Env var `HERMES_WORKER_OVERLAY=1` is injected into the remote
`ssh ubuntu-vm` command for Arm B trials and left unset for Arm A. The
delegate_tool.py patch reads os.environ inside `_build_child_system_prompt`,
so the switch is per-invocation — no process restart needed.

**Why prepend (highest-attention slot):**
Per inv-1's recommendation, the scaffold goes at slot 1 of the prompt
assembly so the child reads it before encountering the goal/context text.
This matches how CRITICAL RULES work in the main CLAUDE.md — structural rules
first, task-specific content second. Format:

```
HERMES-WORKER.md contents
\n\n---\n\n
(existing child prompt: "You are a focused subagent ... YOUR TASK: ...")
```

**Why fork to probe-variantI-wrapper.sh vs. extending probe-variantF-wrapper.sh:**
The operator's brief forbids mid-run artifact edits (wrapper/check/stage).
Creating a sibling wrapper is a setup-time artifact, not a mid-run edit. The
sibling:
- Uses `probe-variantH-check.py` (has the fabrication detector) instead of
  variantF-check.py — matches P1-C's requirement for the new detector to be
  active during probing.
- Parameterized by `ARM` env var: ARM=A runs without overlay (baseline);
  ARM=B runs with overlay active via `HERMES_WORKER_OVERLAY=1` prefix on the
  remote hermes command.
- All other semantics (retry loop, correction messages, session-id recovery,
  OUTCOME line format) identical to probe-variantF-wrapper.sh.

## HERMES-WORKER.md structure

Five sections covering the four r7.5 failure modes plus one anti-regression:

1. **Plan-then-execute pattern** — before any tool call, emit PLAN block
   stating artifact, paths, stop condition. Fixes "dive straight into search
   without goal-shape awareness."
2. **Stop-after-3-unproductive-searches rule** — after 3 consecutive
   reads/searches with no write/meaningful terminal output, STOP and either
   summarize learning + decide OR emit §3 blocked template. Fixes r7.5
   failure mode 1 (search_files thrash, 7/20 trials).
3. **Honest-blocked template** — explicit BLOCKED template with "what I
   tried / what I found / what parent needs to decide." Fixes r7.5 failure
   mode 2 partially (mid-investigation truncation; at minimum reframes
   "I cannot complete" from fabrication to first-class valid output).
4. **Turn budget discipline** — per-range cadence (1-3 plan, 4-14 execute,
   15-18 verify+summarize, 19-20 emit final). If turn 15 arrives without
   progress toward summary, enter §3 immediately. Fixes budget exhaustion.
5. **Anti-fabrication rule** — explicit: NEVER claim file creation unless
   actual write_file/patch/terminal-write call succeeded. Cross-checked by
   the P1-B fabrication detector in check.py. Fixes r7.5 failure mode 4
   (fabricated completion claims on T10).

Approx 200 lines, markdown-formatted with tables and examples.

## Verification performed

### Unit test: delegate_tool.py patch in isolation

```
python3 -c "
from tools.delegate_tool import _build_child_system_prompt
# Test 1: env var unset → base prompt (679 chars, does not start with HERMES-WORKER)
# Test 2: env var 1/true/yes/TRUE/Yes → overlay prepended (8661 chars, starts with '# HERMES-WORKER')
# Test 3: env var 0/false/empty → base prompt (overlay inactive)
"
```

All tests PASS. Overlay injection is correctly gated.

### Smoke test: full end-to-end Arm B trial

Single T4 run under ARM=B:
- Parent session `20260419_201835_5d5a04` successfully dispatched `delegate_worker_v2`
- Child session `20260419_201844_84b781` spawned
- Child's first-turn content: `PLAN: I will explore the workspace to locate the target files ... Stop when I have identified the files and the new session store.`
- Child's final-turn content: `BLOCKED: The target files ... could not be found in the provided workspace ... - What I tried: ...`

Both §1 (PLAN-prefix) and §3 (BLOCKED template) of HERMES-WORKER.md were
observably followed by the child. Overlay is reaching the child at runtime.

### Smoke test: Arm A baseline

Single T4 run under ARM=A (no overlay):
- Parent `20260419_202012_595b58` dispatched successfully
- Child `20260419_202017_1c45a7` started with empty content → `todo` tool call (classic r7.5 failure pattern)
- No PLAN prefix, no §3 template; behavior matches pre-r7.6 canonical

Overlay is correctly OFF under ARM=A.

## Stage + VM preconditions for probe

Before probe start (2026-04-19 20:17 PT):
- `HERMES-canonical-backup.md`: md5 `0780c232a6cb52e13e432261f0d68ad9` (canonical)
- `HERMES.md` swapped to variantF: md5 `01c0e77bb2a6e753a8ea9063784a25e0`
- Tripwires (`SKILL.md` `fb1a5a52…`, `jira-briefing.sh` `a1dce6e9…`): unchanged
- oMLX health: CLEAN (95.9 GB free mem)
- Staged: variantF (delegate_worker_v2), variantG (turn-0 toolset restriction),
  variantH (inv-2 + inv-3 mechanical fixes), variantI (HERMES-WORKER.md overlay)
- Probe wrappers use `probe-variantH-check.py` (md5 `873935f65e1bb91942dde1139dd57f92`
  — the replay-verified build with fabrication detector).

## Hard invariants preserved

- Canonical HERMES.md backup present (single-file restore path).
- All `.probe-r7.*-orig` backups on VM preserved side-by-side.
- Env-var gate ensures Arm A runs are byte-identical to canonical child prompts.
- `_strip_blocked_tools` / `_build_child_agent` call path unchanged — overlay
  only affects the `ephemeral_system_prompt` argument, not tool binding.
