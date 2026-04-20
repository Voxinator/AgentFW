# ARTIFACT-impl-1-toolset-restriction

**Worker:** IMPL-1
**Layer:** 1 of r7.2 dispatch-remediation playbook
**Goal:** Make `hermes chat` invokable with a restricted toolset that mechanically prevents Gemma from role-collapsing into mutator tools (`patch`, `write_file`, `terminal`, `execute_code`, `skill_manage`) while preserving orientation capability (`read_file` + `search_files`).
**Status:** COMPLETE — smoke test passed.
**Date:** 2026-04-18

---

## Summary

Two changes:

1. **VM:** Added a new `file_readonly` toolset to `~/.hermes/hermes-agent/toolsets.py` that exposes only `read_file` and `search_files`. The existing `file` toolset (which bundles `read_file` + `write_file` + `patch` + `search_files`) was left unchanged.
2. **Mac (host):** Modified `probe-variantE-wrapper.sh` to accept an optional `TOOLSETS` env var. When set, the wrapper appends `-t "$TOOLSETS"` to both the initial `hermes chat` call and the `--resume` retry calls. When unset, behavior is identical to the previous wrapper (no `-t` flag, full default toolset).

Combined effect: a probe trial launched as `TOOLSETS=delegation,todo,clarify,file_readonly probe-variantE-wrapper.sh ...` exposes only 6 tools to Gemma (delegate_task, delegate_worker, todo, clarify, read_file, search_files) instead of the default 29. Mutator tools are physically absent from the model's tool registry, so role-collapse becomes mechanically impossible rather than just behaviorally discouraged.

Both backups exist via the new `.probe-r7.3-orig` / `.pre-r7.3-orig` suffixes (distinct from the existing `.probe-d-orig` generation, so they don't collide).

---

## 1. Diff: `~/.hermes/hermes-agent/toolsets.py` (on VM)

```diff
--- /home/parallels/.hermes/hermes-agent/toolsets.py.probe-r7.3-orig	2026-04-18 19:33:15.551041825 -0500
+++ /home/parallels/.hermes/hermes-agent/toolsets.py	2026-04-18 19:33:48.301262465 -0500
@@ -152,6 +152,12 @@
         "includes": []
     },
     
+    "file_readonly": {
+        "description": "Read-only file tools: read_file and search_files only (no write_file, no patch). Use to mechanically prevent role-collapse mutation in untrusted/orientation-only agents.",
+        "tools": ["read_file", "search_files"],
+        "includes": []
+    },
+    
     "tts": {
         "description": "Text-to-speech: convert text to audio with Edge TTS (free), ElevenLabs, or OpenAI",
         "tools": ["text_to_speech"],
```

Insertion point: between the existing `file` toolset and the `tts` toolset. Single new entry, no modifications to existing toolsets, no changes to `_HERMES_CORE_TOOLS`, no changes to any `hermes-*` platform toolset. Idempotent (the patch script bails with `ALREADY_PRESENT` if the entry already exists).

Verification:

```
$ ssh ubuntu-vm 'cd ~/.hermes/hermes-agent && python3 -c "import toolsets; print(\"file_readonly\" in toolsets.TOOLSETS); print(toolsets.TOOLSETS[\"file_readonly\"]); print(\"resolved:\", sorted(toolsets.resolve_toolset(\"file_readonly\")))"'
True
{'description': 'Read-only file tools: read_file and search_files only (no write_file, no patch). Use to mechanically prevent role-collapse mutation in untrusted/orientation-only agents.', 'tools': ['read_file', 'search_files'], 'includes': []}
resolved: ['read_file', 'search_files']
```

---

## 2. Diff: `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh` (on host)

```diff
--- /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh.pre-r7.3-orig	2026-04-18 19:33:56
+++ /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh	2026-04-18 19:34:20
@@ -21,6 +21,15 @@
 MAX_RETRIES=3
 TIMEOUT_PER_TURN=900
 SOURCE_TAG="${SOURCE_PREFIX}-run${RUN_NUM}"
+# Optional restricted-toolset selection (r7.3 Layer 1). If set, becomes
+# `-t "$TOOLSETS"` appended to every `hermes chat` invocation. If empty/unset,
+# wrapper behaves exactly as before (no -t flag, full default toolset).
+TOOLSETS_ENV="${TOOLSETS:-}"
+if [[ -n "$TOOLSETS_ENV" ]]; then
+  TOOLSETS_FLAG="-t \"$TOOLSETS_ENV\""
+else
+  TOOLSETS_FLAG=""
+fi
 CHECK_REMOTE="/tmp/probe-variantE-check.py"
@@ -118,7 +127,7 @@
-log "MODEL=${MODEL} SOURCE_PREFIX=${SOURCE_PREFIX} TIMEOUT=${TIMEOUT_PER_TURN}s"
+log "MODEL=${MODEL} SOURCE_PREFIX=${SOURCE_PREFIX} TOOLSETS=${TOOLSETS_ENV:-<default>} TIMEOUT=${TIMEOUT_PER_TURN}s"
@@ -144,7 +153,7 @@
-ssh_run "P=\$(cat); cd ~/.hermes/hermes-agent && timeout $TIMEOUT_PER_TURN ./venv/bin/hermes chat -m $MODEL -Q --max-turns 20 --checkpoints -q \"\$P\" --source $SOURCE_TAG" <<< "$TASK_TEXT" > "$TURN_OUT" 2>&1
+ssh_run "P=\$(cat); cd ~/.hermes/hermes-agent && timeout $TIMEOUT_PER_TURN ./venv/bin/hermes chat -m $MODEL -Q --max-turns 20 --checkpoints $TOOLSETS_FLAG -q \"\$P\" --source $SOURCE_TAG" <<< "$TASK_TEXT" > "$TURN_OUT" 2>&1
@@ -213,7 +222,7 @@
-  ssh_run "P=\$(cat); cd ~/.hermes/hermes-agent && timeout $TIMEOUT_PER_TURN ./venv/bin/hermes chat -m $MODEL --resume $SESSION_ID -Q --max-turns 20 -q \"\$P\" --source $SOURCE_TAG" <<< "$CORRECTION" > "$TURN_OUT" 2>&1
+  ssh_run "P=\$(cat); cd ~/.hermes/hermes-agent && timeout $TIMEOUT_PER_TURN ./venv/bin/hermes chat -m $MODEL --resume $SESSION_ID -Q --max-turns 20 $TOOLSETS_FLAG -q \"\$P\" --source $SOURCE_TAG" <<< "$CORRECTION" > "$TURN_OUT" 2>&1
```

Four logical edits:

1. **Header block (lines 24-32):** Read `TOOLSETS` env var into `TOOLSETS_ENV`. Build `TOOLSETS_FLAG` as `-t "$TOOLSETS_ENV"` when non-empty, empty string otherwise. The `-t` flag is embedded inside the value so it disappears entirely when `TOOLSETS` is unset (preserving exact prior behavior).
2. **Header log line (line 130):** Append `TOOLSETS=${TOOLSETS_ENV:-<default>}` to the per-trial banner so every trial's logs document which toolset the trial ran with.
3. **Initial invocation (line 156):** Inject `$TOOLSETS_FLAG` between `--checkpoints` and `-q` in the first `hermes chat` call.
4. **Retry invocation (line 225):** Inject `$TOOLSETS_FLAG` between `--max-turns 20` and `-q` in every `--resume` retry call.

`bash -n` syntax check: PASS.

Idempotency: re-running the wrapper with or without `TOOLSETS` set has no side effects on the wrapper file itself; the backup script (the `cp`) is gated on `[ -f ...pre-r7.3-orig ]` so it won't overwrite the pristine backup on subsequent runs.

---

## 3. Rollback procedure

If Layer 1 needs to be reverted (toolsets.py change is rejected, or the wrapper modification breaks an existing probe path), restore both files from their `.r7.3` backups:

```bash
# On Mac (wrapper):
cp /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh.pre-r7.3-orig \
   /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh

# On VM (toolsets.py):
ssh ubuntu-vm 'cp ~/.hermes/hermes-agent/toolsets.py.probe-r7.3-orig \
                  ~/.hermes/hermes-agent/toolsets.py'
```

After rollback, the existing `.probe-d-orig` backups remain untouched (they predate r7.3 and represent a different generation of the patch lineage). The `file_readonly` toolset entry disappears entirely; existing probes (which don't pass `TOOLSETS`) revert to the prior 29-tool default surface.

No process restart required: `hermes chat` reads `toolsets.py` fresh on every invocation, and the wrapper is read by bash on every `probe-variantE-wrapper.sh` exec.

---

## 4. Smoke test

Command:

```bash
MODEL=gemma-4-31b-it-4bit SOURCE_PREFIX=probe-r7.3-smoke TOOLSETS=delegation,todo,clarify,file_readonly \
  /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh 0 <<<"What's the capital of France?"
```

OUTCOME line (verbatim):

```
OUTCOME run=0 MODEL=gemma-4-31b-it-4bit RESULT=COMPLIANT attempts=1 elapsed=23s final_session=20260418_193428_bf0423 chain="A0:rc=0 | A0:COMPLIANT"
```

Wrapper log (banner verifies the `TOOLSETS=...` field is now emitted):

```
[probe-r7.3-smoke run0] MODEL=gemma-4-31b-it-4bit SOURCE_PREFIX=probe-r7.3-smoke TOOLSETS=delegation,todo,clarify,file_readonly TIMEOUT=900s
[probe-r7.3-smoke run0] task: What's the capital of France?...
[probe-r7.3-smoke run0] attempt 0: initial invocation
[probe-r7.3-smoke run0] session_id captured: 20260418_193428_bf0423
[probe-r7.3-smoke run0] attempt 0 verdict: COMPLIANT
```

Result interpretation:

- `RESULT=COMPLIANT` — passed the variant-E check on first attempt.
- `attempts=1` — no retries / no corrections needed.
- `elapsed=23s` — within normal range.
- No `MODEL_MISMATCH` / `MODEL_CHECK=` suffix on the OUTCOME line — session JSON `model` field matches the requested `gemma-4-31b-it-4bit`.
- No `NO_SESSION_ID` ERROR — session_id captured cleanly via primary regex (no fallback recovery needed).
- `chain="A0:rc=0 | A0:COMPLIANT"` — clean single-attempt success.

---

## 5. Tools visible to Gemma in smoke-test session JSON

```
$ ssh ubuntu-vm 'python3 -c "
import json
sp = \"/home/parallels/.hermes/sessions/session_20260418_193428_bf0423.json\"
d = json.load(open(sp))
print(\"model:\", d.get(\"model\"))
print(\"tools count:\", len(d.get(\"tools\") or []))
print(\"tool names:\", sorted(t[\"function\"][\"name\"] for t in d.get(\"tools\") or []))
"'
model: gemma-4-31b-it-4bit
tools count: 6
tool names: ['clarify', 'delegate_task', 'delegate_worker', 'read_file', 'search_files', 'todo']
```

**Tool count: 6 (down from 29 in the default surface).**

Surface composition by toolset:

- `delegation` -> `delegate_task`, `delegate_worker`  (2 tools)
- `todo` -> `todo`                                     (1 tool)
- `clarify` -> `clarify`                                (1 tool)
- `file_readonly` -> `read_file`, `search_files`      (2 tools)

**Mutator tools confirmed absent:** `patch`, `write_file`, `terminal`, `execute_code`, `skill_manage` — none present in the tool list. Role-collapse into mutator paths is now mechanically impossible at the tool-registry level for any trial that opts in via the `TOOLSETS` env var.

Model field matches request: `gemma-4-31b-it-4bit` == requested `gemma-4-31b-it-4bit`. No MM mismatch.

---

## Files touched

- `/home/parallels/.hermes/hermes-agent/toolsets.py` (VM, +6 lines, 1 new toolset entry)
- `/home/parallels/.hermes/hermes-agent/toolsets.py.probe-r7.3-orig` (VM, new backup)
- `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh` (host, +9 -3 net edits)
- `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh.pre-r7.3-orig` (host, new backup)
- `/tmp/patch_toolsets_r7.3.py` (host scratch, also `/tmp/patch_toolsets_r7.3.py` on VM) — idempotent patch script, can be safely deleted; kept for re-run if rollback needs to be re-applied

## Files NOT touched (per scope rules)

- `core/`, `references/`, `playbooks/`, `templates/` — none touched
- `HERMES.md`, `delegate_worker.py`, `model_tools.py`, `run_agent.py` — none touched
- The existing `.probe-d-orig` backup generation — preserved untouched (different suffix used)
- Existing `file` toolset and any other toolset — preserved untouched
- `_HERMES_CORE_TOOLS` shared list — preserved untouched, so all `hermes-*` platform toolsets remain unchanged
