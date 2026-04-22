# ARTIFACT — r7.2 SKILL.md surgical revert

**Worker:** Claude Opus 4.7 sub-agent (read-only-except-one-file scope).
**Target file:** `/home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md` (on `ubuntu-vm`).
**Pre-revert md5:** `7452db8be00403f32b0f1dca8415b691` (244 lines, 10521 bytes on-disk / 10489 decoded UTF-8 chars, mtime 2026-04-18 13:25:27).
**Post-revert md5:** `fb1a5a5208a6cf2fcb8252aac10397eb` (244 lines, 10489 bytes).
**Verdict:** **GO — revert executed and verified.**

---

## 1. Session identification

- Dense-leg Trial 9 per `ARTIFACT-probe-r7.2-dense.md` §4:
  - Parent: `session_20260418_131827_6d144e.json`
  - Child spawned via `delegate_worker` call #12: **`session_20260418_132446_9dc3b8.json`**
- Child session model: `gemma-4-31b-it-4bit` (matches SKILL.md mtime 13:25 within 60s).
- Child session structure: **6 messages total**
  - `[0]` user task: verbatim the "Patch the 'jira-daily-briefing' skill…" delegation goal
  - `[1]` assistant `tool_calls=['read_file']`
  - `[2]` tool result — entire pre-mutation SKILL.md content (244 lines, `file_size: 10489`)
  - `[3]` assistant `tool_calls=['patch']` ← the mutating call
  - `[4]` tool result — `{"success": true, "diff": …}` (no `is_error`; mutation committed)
  - `[5]` assistant final summary

The mutation came via the **`patch`** tool (not `skill_manage` as the worker-spec hypothesized). The session log is otherwise uncontaminated — exactly one tool call touched SKILL.md.

## 2. Tool-call evidence (verbatim)

Assistant message `[3]`, tool call `call_5cabaa1a`:

```json
{
  "function": {
    "name": "patch",
    "arguments": {
      "mode": "replace",
      "path": "/home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md",
      "old_string": "- If ALL sections are empty: `All clear — nothing needs your attention this morning.`",
      "new_string": "- If ALL sections are empty: `All clear — nothing needs your attention this morning. (Scanned since [last_run date])`"
    }
  }
}
```

Tool result `[4]` confirms success with a unified diff at lines 212-218 of the file — single hunk, single line changed:

```diff
-- If ALL sections are empty: `All clear — nothing needs your attention this morning.`
++ If ALL sections are empty: `All clear — nothing needs your attention this morning. (Scanned since [last_run date])`
```

`files_modified`: the target path (only). No other file touched by this session.

## 3. Revert strategy — Strategy A (inverse str_replace)

**Justification for A over B/C/D:**
- Single clean `old_string → new_string` substitution; `mode: "replace"` in the tool call.
- Inverting is literally `content.replace(new_string, old_string, 1)`.
- **Uniqueness verified pre-revert:** `new_string` occurs exactly 1 time in current file; `old_string` occurs 0 times in current file (because `old_string`'s trailing backtick is followed by `` (Scanned…)`` in the mutated state, so they do not overlap as substrings).
- **Cross-check available:** the session's `read_file` result at message `[2]` embeds the full pre-mutation file content with line-number prefixes. Reconstructing that (strip `   N|` prefix, re-join) gives 10489 bytes and md5 `fb1a5a5208a6cf2fcb8252aac10397eb`. This provides Strategy B as a verification oracle without needing to use it as the source.
- Strategy C (multi-hunk) N/A — single hunk. Strategy D (abort) unwarranted — evidence is unambiguous.

## 4. Execution

Preflight guard matched (`current_md5 == 7452db8be00403f32b0f1dca8415b691`), then:

```python
# Executed via: ssh ubuntu-vm 'python3 /tmp/do_revert.py'
path = "/home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md"
new_str = "- If ALL sections are empty: `All clear — nothing needs your attention this morning. (Scanned since [last_run date])`"
old_str = "- If ALL sections are empty: `All clear — nothing needs your attention this morning.`"
# Guarded: current md5 must be 7452db8… ; new_str count must be exactly 1; old_str must be absent
content = open(path, "rb").read().decode("utf-8")
reverted = content.replace(new_str, old_str, 1)
open(path, "wb").write(reverted.encode("utf-8"))
```

A pre-revert backup was written to `SKILL.md.pre-revert-20260418_1340` in the same directory (alongside the pre-existing `SKILL.md.bash-backup`). The backup preserves the exact mutated state for audit.

## 5. Post-revert verification

- **md5 (disk):** `fb1a5a5208a6cf2fcb8252aac10397eb` — matches the md5 of the session-reconstructed pre-patch content.
- **Byte size:** 10489 (matches session `file_size: 10489` from the pre-mutation `read_file` result).
- **Byte-level cross-check:** `diff -q <reverted-file> <session-reconstructed-prepatch>` → files identical. This is a stronger check than md5 and rules out collision pathology.
- **Structural smoke (head -40):** YAML frontmatter intact (`name: jira-daily-briefing`, `version: 3.0.0`, `prerequisites.env_vars: [ATLASSIAN_SITE, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN]`). `# Jira Daily Briefing — Chief of Staff` heading present. `## HOW TO CALL TOOLS — CRITICAL` section present with three worked `<tool_call>` examples (cat, curl POST, etc.).
- **Reverted hunk (lines 210-218):** the target line now reads `- If ALL sections are empty: \`All clear — nothing needs your attention this morning.\`` (pre-mutation wording).
- **Difference from mutated md5:** post-revert md5 differs from the mutated md5 as required.

## 6. Go/no-go verdict

**GO — revert complete and verified.** The production Jira cron (weekdays 08:00) will now run against the pre-r7.2-dense state of SKILL.md on Monday. No other files were touched. No git operations were performed. Backup preserved at `SKILL.md.pre-revert-20260418_1340` in case the parent session later decides the Trial 9 mutation was desirable and wants to restore it.

**Scope hygiene:**
- Files read on VM: the 5 candidate session JSONs (read-only), the target SKILL.md (read, then written once).
- Files written on VM: target SKILL.md (revert), `SKILL.md.pre-revert-20260418_1340` (backup), `/tmp/inspect_session.py`, `/tmp/extract_patch.py`, `/tmp/verify_revert.py`, `/tmp/do_revert.py`, `/tmp/extract_prepatch.py`, `/tmp/SKILL.md.prepatch` (all scratch helpers under `/tmp`).
- Files written on Mac: this artifact only.
- Git: no operations performed.
