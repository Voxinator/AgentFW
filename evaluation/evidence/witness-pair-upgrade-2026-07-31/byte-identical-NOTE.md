# Byte-identical pre-1.6 regression — result

144 validator invocations compared (48 pre-1.6 inputs — every git-tracked fixture plus both
adapter SKILL.md files — under default, --legacy, and --digest modes), old v9.4.0 validator
(from ~/.claude/skills/agentfw-backup-2026-07-31) vs new 1.6 validator.

Result: byte-identical EXCEPT one precedented moving pointer — the legacy-"1" rejection
diagnostic names the current schema of record ("migrate to \"1.6\"" was "migrate to \"1.5\"").
git history shows the same pointer moved 1.4→1.5 at the v9.4.0 bump (commit 2c054a1) and
1.3→1.4 before that. Verdicts, exit codes, defect keywords, and every other output line are
identical. Diff: byte-identical-diff.txt (8 lines = 2 changed line-pairs × diff framing).
