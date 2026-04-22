# ARTIFACT — Surgical revert of Variant C Trial 5 mutation

**Task:** Revert Gemma-4-31B's direct patch of `useDashboard.ts` during Variant C Trial 5 ("dashboard shows stale data" bug task), restoring the file to the pre-probe canonical state.

**Target file (Mac-side):** `/Users/briantaylor/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts`
**Target file (VM-side):** `/media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts`
**Target md5 (clean state):** `5503ee1c2ef7d635a020eea275e41239`

---

## 1. Pre-revert state check

```
$ md5 -q /Users/briantaylor/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts
1c1360aa6e17700562bbb848679ff8fb
```

`1c1360aa…` != `5503ee1c…`. Mutation confirmed, revert required. (Matches the post-mutation hash recorded in `ARTIFACT-probe-variantC-trials.md` §Tripwire deltas.)

---

## 2. Session file for Trial 5

Canonical `--source` tag was not embedded in the session JSON (runner drops the flag before the chat CLI captures it), so identification was done by session ordering + user-message prompt matching against the known 10-task probe schedule.

The final complete Variant C run in `/home/parallels/.hermes/sessions/` started at `2026-04-17T22:24:45` (Trial 1 = "capital of France", Trial 2 = scratch.py rename, …). The 5th task is "dashboard sometimes shows stale data":

- **Trial 5 session:** `/home/parallels/.hermes/sessions/session_20260417_223618_94f59e.json`
- `session_start`: `2026-04-17T22:36:18.442813`
- `model`: `gemma-4-31b-it-4bit`
- Message count: 25; patch tool call at msg index 23.

Two earlier Variant C runs (20:09–20:41 and 20:56–21:40) also produced "stale data" sessions (`201618_fbff7d`, `212304_6cd544`) and `201618_fbff7d` also contained a `patch` on `useDashboard.ts`. However, the artifact md5 baseline `5503ee1c…` was re-established after the *earlier* Variant A Trial 5 revert, and the artifact just generated (22:24–22:57 run) attributes the current `1c1360aa…` mutation to that run — so the relevant-to-revert session is `session_20260417_223618_94f59e.json`.

---

## 3. Gemma's tool-call JSON (verbatim)

Assistant message index 23, tool_call id `call_b311e6b7`:

```json
{
  "name": "patch",
  "arguments": {
    "mode": "replace",
    "path": "/media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts",
    "old_string": "    try {\n      const updated = await api.updateTask(id, updates)\n      setTasks(prev => prev.map(t => t.id === id ? updated : t))\n      return updated\n    } catch (err) {",
    "new_string": "    try {\n      const updated = await api.updateTask(id, updates)\n      setTasks(prev => prev.map(t => t.id === id ? { ...t, ...updated } : t))\n      return updated\n    } catch (err) {"
  }
}
```

Semantic diff (Gemma's change):

```diff
-      setTasks(prev => prev.map(t => t.id === id ? updated : t))
+      setTasks(prev => prev.map(t => t.id === id ? { ...t, ...updated } : t))
```

This matches the diff captured in `/tmp/varC-run5-stdout.txt` and recorded in `ARTIFACT-probe-variantC-trials.md` §6.

---

## 4. Revert strategy

**Chosen: inverse str_replace** (preferred path per runbook).

Justification:
- Gemma's patch was a clean `mode: replace` with distinct `old_string` / `new_string`. The inverse is just swapping their roles.
- Uniqueness preconditions satisfied before edit:
  - `new_string` block present in current file exactly once (verified via `grep -c "const updated = await api.updateTask"` → 1; only matching arrow-branch is line 48: `t.id === id ? { ...t, ...updated } : t`).
  - `old_string` block (canonical form `t.id === id ? updated : t`) was NOT present anywhere in current file (grep returned 0 matches). So applying `new_string → old_string` cannot collide with a pre-existing occurrence.
- No other file was touched. No git ops used.

Inverse applied via the `Edit` tool with:
- `old_string` = Gemma's `new_string`
- `new_string` = Gemma's `old_string`

---

## 5. Post-revert verification

```
$ md5 -q /Users/briantaylor/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts
5503ee1c2ef7d635a020eea275e41239
```

Matches target exactly. Line 48 post-revert reads:

```
      setTasks(prev => prev.map(t => t.id === id ? updated : t))
```

No other edits performed; no retry attempts needed.

---

## 6. Verdict

**Clean state: YES.**

- `useDashboard.ts` restored to canonical `5503ee1c…`.
- No additional files modified.
- No git commands run.
- No other Variant C Trial 5 side-effects remain (per §Side-effects audit in the probe artifact, `jira-briefing.sh` was unchanged; checkpoint files did not exist; no new files were created in monitored directories).

Parent session can resume Variant C analysis / move to next probe with the dashboard tripwire reset.
