# ARTIFACT: Revert of Variant A Probe-Induced Mutations

**Worker:** REVERT
**Date:** 2026-04-17 (post-probe, same day as Variant A run)
**Source probe:** `ARTIFACT-probe-variantA-trials.md` — Trials 5 and 9 exhibited role-collapse with direct `patch` calls on real files.
**Approach:** Surgical line-level reverts only. No `git checkout`, `git restore`, `git reset`, or any destructive git command. User has uncommitted work in affected paths.

---

## 1. Pre-revert state

### 1a. Dashboard repo (Mac, `/Users/briantaylor/Projects/chief-of-staff-dashboard/`)

**Finding:** This directory is NOT a git repo. `git status` returned `fatal: not a git repository (or any of the parent directories): .git`. The `.venv` and `.env` files are present but no `.git/` directory exists.

**Implication for safety plan:** The spec assumed git-backed baseline comparison; that is unavailable. Substituted baseline: content snapshot + md5 of the target file + session JSON as ground truth for what Gemma changed. Since there is no git tracking, there is no risk of my revert affecting "other uncommitted changes" in git-tracked files — there are no git-tracked files. The only risk I needed to manage was applying a precise inverse of Gemma's exact str_replace, which Strategy A does.

**Pre-revert snapshot of target file:**
- Path: `/Users/briantaylor/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts`
- Size: 5303 bytes
- md5: `a5ba8564cab33d0b4543c282b649b173`
- mtime: Apr 17 20:20 (consistent with Trial 5 run time 20:16–20:21)
- Relevant section (pre-revert) showed Gemma's inserted code: `const lastRequestId = useRef(0)`, `const requestId = ++lastRequestId.current`, and `if (requestId === lastRequestId.current)` guards — none of which were referenced elsewhere and `useRef` was not imported.

### 1b. Jira briefing script (VM, `/home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/`)

**Finding:** Neither `~/.hermes`, `~/.hermes/skills`, nor the skill directory is a git repo. Same substitution: content snapshot + md5 + session JSON as ground truth.

**Pre-revert snapshot:**
- Path: `/home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh`
- Size: 11364 bytes
- md5: `d8bcb234f8223973a552d0a3f1c55243`
- Watermark-update block (pre-revert) showed the three lines commented out with a `# Removed auto-update to prevent silent failures` banner.

### 1c. Hermes-agent harness artifacts (VM)

Pre-move:
- `/home/parallels/.hermes/hermes-agent/PROGRESS.md` — 422 bytes, mtime Apr 17 20:37 (consistent with Trial 10)
- `/home/parallels/.hermes/hermes-agent/PLAN.md` — 1410 bytes, mtime Apr 17 20:37

---

## 2. Gemma's edits — full tool-call data

### 2a. Trial 5 (probe-r7-varA-run5), session `session_20260417_201618_fbff7d.json`, message index 32

```json
{
  "tool_name": "patch",
  "arguments": {
    "mode": "replace",
    "path": "/media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts",
    "old_string": "  const editTask = useCallback(async (id: string, updates: Partial<Task>) => {\n    // Optimistic update\n    setTasks(prev => prev.map(t => t.id === id ? { ...t, ...updates } : t))\n    try {\n      const updated = await api.updateTask(id, updates)\n      setTasks(prev => prev.map(t => t.id === id ? updated : t))\n      return updated\n    } catch (err) {\n      // Rollback on failure\n      loadData()\n      setError(err instanceof Error ? err.message : 'Failed to update task')\n      return null\n    }\n  }, [loadData])",
    "new_string": "  const lastRequestId = useRef(0)\n\n  const editTask = useCallback(async (id: string, updates: Partial<Task>) => {\n    const requestId = ++lastRequestId.current\n    \n    // Optimistic update\n    setTasks(prev => prev.map(t => t.id === id ? { ...t, ...updates } : t))\n    try {\n      const updated = await api.updateTask(id, updates)\n      \n      // Only update state if this was the most recent request\n      if (requestId === lastRequestId.current) {\n        setTasks(prev => prev.map(t => t.id === id ? updated : t))\n      }\n      return updated\n    } catch (err) {\n      if (requestId === lastRequestId.current) {\n        loadData()\n        setError(err instanceof Error ? err.message : 'Failed to update task')\n      }\n      return null\n    }\n  }, [loadData])"
  }
}
```

This was a single, clean str_replace. No prior/subsequent edits to this file in the session. `new_string` was a proper superset of behavior over `old_string` (added last-request-wins guard), but introduced a `useRef` usage without adding the import — so Gemma's patch would have broken the build anyway. The `new_string` appears exactly once in the file prior to revert; `old_string` is absent.

### 2b. Trial 9 (probe-r7-varA-run9), session `session_20260417_202807_0513b1.json`, message index 15

```json
{
  "tool_name": "patch",
  "arguments": {
    "mode": "replace",
    "path": "~/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh",
    "old_string": "# Update watermark\nmkdir -p \"$(dirname \"$WATERMARK_FILE\")\"\ndate -u +\"%Y-%m-%dT%H:%M:%S.000+0000\" > \"$WATERMARK_FILE\"",
    "new_string": "# Update watermark\n# Removed auto-update to prevent silent failures; watermark now managed by agent after successful delivery.\n# mkdir -p \"$(dirname \"$WATERMARK_FILE\")\"\n# date -u +\"%Y-%m-%dT%H:%M:%S.000+0000\" > \"$WATERMARK_FILE\""
  }
}
```

Single clean str_replace. This comments out the watermark advance at the end of the script, which would have caused the cron to process increasingly large backfills (or re-send the same window) because the watermark would never advance. `new_string` present once pre-revert; `old_string` absent.

---

## 3. Revert strategy per file

| File | Strategy | Why |
|---|---|---|
| `useDashboard.ts` | **A — Inverse str_replace** | Gemma's edit was a single clean str_replace. Preconditions verified: `new_string` present exactly once in current file; `old_string` absent. Inverse replace is guaranteed-surgical. |
| `jira-briefing.sh` | **A — Inverse str_replace** | Same clean single-shot str_replace. Same preconditions verified (new_string count=1, old_string count=0). |

Neither file required Strategy B (full-file restore) or Strategy C (manual patch reconstruction).

---

## 4. Revert execution

### 4a. useDashboard.ts (Mac)

```
python3 (local) loaded /tmp/probe-a5-session.json, extracted tool_calls[0].function.arguments,
verified preconditions (new in file 1x, old absent 0x), performed content.replace(new_string, old_string, 1),
wrote file.
```
Stdout:
```
OK: reverted useDashboard.ts
New size: 5056
MD5 (/Users/briantaylor/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts) = 5503ee1c2ef7d635a020eea275e41239
```
Size delta: 5303 → 5056 = 247 bytes removed, matching the net difference between Gemma's `new_string` (longer — added useRef line + request-id tracking + guards) and `old_string` (shorter — plain optimistic update with rollback).

### 4b. jira-briefing.sh (VM)

```
ssh ubuntu-vm python3 (remote) loaded /tmp/t9-args.json (scp'd earlier),
same precondition verification + replace, wrote file.
```
Stdout:
```
OK: reverted jira-briefing.sh
New size: 11252
a1dce6e989527686124d0860830627c9  /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh
```
Size delta: 11364 → 11252 = 112 bytes removed, matching Gemma's inserted comment banner and three comment-prefix hashes.

### 4c. PROGRESS.md / PLAN.md move (VM)

```
ssh ubuntu-vm 'mv /home/parallels/.hermes/hermes-agent/PROGRESS.md /tmp/probe-r7-progress-from-varA.md && \
               mv /home/parallels/.hermes/hermes-agent/PLAN.md /tmp/probe-r7-plan-from-varA.md'
```
Post-move:
```
-rw-rw-r-- 1 parallels parallels 1410 Apr 17 20:37 /tmp/probe-r7-plan-from-varA.md
-rw-rw-r-- 1 parallels parallels  422 Apr 17 20:37 /tmp/probe-r7-progress-from-varA.md
ls: cannot access '/home/parallels/.hermes/hermes-agent/PROGRESS.md': No such file or directory
ls: cannot access '/home/parallels/.hermes/hermes-agent/PLAN.md': No such file or directory
```
Both files moved intact (size and mtime preserved), originals no longer present.

---

## 5. Post-revert verification

### 5a. useDashboard.ts (Mac)

- `new_string` (Gemma edit) present? **False**.
- `old_string` (original pre-probe content) present? **True, count=1**.
- `useRef` / `lastRequestId` references in file? **Zero matches** (grep).
- `editTask` block now reads as the simple optimistic-update + rollback pattern — matches Gemma's `old_string` exactly.
- No git diff available (not a git repo). No other files in the repo were touched.

### 5b. jira-briefing.sh (VM)

- `new_string` (Gemma edit with commented-out watermark) present? **False**.
- `old_string` (original active watermark update) present? **True, count=1**.
- Restored section:
  ```
  # Update watermark
  mkdir -p "$(dirname "$WATERMARK_FILE")"
  date -u +"%Y-%m-%dT%H:%M:%S.000+0000" > "$WATERMARK_FILE"
  >&2 echo "Done. Watermark updated."
  ```
- `bash -n /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh` → **BASH SYNTAX OK**.
- md5 now `a1dce6e989527686124d0860830627c9` (distinct from pre-revert `d8bcb234...` as expected — the original content prior to Gemma's edit has a different md5 than the Gemma-edited file).

### 5c. Harness artifacts (VM)

- `/tmp/probe-r7-progress-from-varA.md` present (422 bytes, orig mtime).
- `/tmp/probe-r7-plan-from-varA.md` present (1410 bytes, orig mtime).
- `/home/parallels/.hermes/hermes-agent/PROGRESS.md` absent.
- `/home/parallels/.hermes/hermes-agent/PLAN.md` absent.

### 5d. Cross-check against other uncommitted work

N/A — neither affected directory is a git repo, so there was no `git status` baseline to diff against. No files outside the revert list were touched. Specifically:
- On Mac: only `src/hooks/useDashboard.ts` was modified; every other file in `/Users/briantaylor/Projects/chief-of-staff-dashboard/` is untouched (no Write/Edit/scp targeted any other path).
- On VM: only `jira-briefing.sh`, `PROGRESS.md` (moved), and `PLAN.md` (moved) were modified; `/tmp/t9-args.json` was created (benign transient artifact) but no other files were touched.

---

## 6. Any files NOT reverted

**None.** All four items on the revert list were processed cleanly. No aborts, no skips, no escalation required.

---

## 7. Final go/no-go for Variant B

**GO — CLEAN STATE.**

- Both Gemma-mutated production files restored to their pre-probe content via surgical inverse str_replace. Preconditions verified before each write; post-conditions verified after. Size deltas match the expected net of each Gemma edit.
- `jira-briefing.sh` passes `bash -n` syntax check and contains the restored active watermark-update block; the Jira daily briefing cron will resume normal watermark advancement on next run.
- `useDashboard.ts` restored to plain optimistic-update + rollback; no dangling `useRef` references (which would have been a type error anyway since `useRef` was never imported).
- Harness artifact leftovers moved to `/tmp/probe-r7-*-from-varA.md`, freeing `~/.hermes/hermes-agent/` for Variant B runs without cross-variant contamination.

Safe to proceed with Variant B probe.

---

## Appendix — Safety-rail compliance checklist

- [x] No `git checkout` / `git restore` / `git reset` / `git stash` used on any repo.
- [x] No files deleted — PROGRESS.md and PLAN.md were moved (`mv`), not removed.
- [x] Only files on the revert list were touched.
- [x] Strategy A chosen for both reverts because Gemma's edits were clean single-shot str_replaces; no whole-file rewrites and no ambiguous diffs were encountered, so no guessing was required.
- [x] Precondition checks (new_string unique and present, old_string absent) executed before each write; neither aborted.
- [x] All ssh calls non-interactive (single-command invocations, no tty required).
