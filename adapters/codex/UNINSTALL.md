# AgentFW r9 — Codex uninstall (manual)

Removal is the exact inverse of INSTALL.md's three-item inventory. Nothing else was installed;
nothing else gets touched.

## 1. Remove the marker block from AGENTS.md

Delete everything from the line containing `<!-- AGENTFW:BEGIN r9 -->` through the line
containing `<!-- AGENTFW:END r9 -->`, inclusive, in `~/.codex/AGENTS.md` (and in any repo-root
`AGENTS.md` where you installed per-project). All content outside the markers is yours and
stays byte-for-byte.

- If the file is now empty or whitespace-only, remove it: `rm ~/.codex/AGENTS.md`.

## 2. Remove the skill directory

```sh
rm -rf ~/.agents/skills/agentfw
```

This removes `SKILL.md` and the bundled `policy/` copy — everything the install placed there.
If you added your own files inside that directory (you shouldn't have), rescue them first.

## 3. Remove the config keys the install added

The install merged at most these keys into `~/.codex/config.toml`:

- `approval_policy`
- `sandbox_mode`
- `[sandbox_workspace_write]` → `network_access`, `writable_roots`

Remove them **only if AgentFW added them**. If they predated the install or you have since
tuned them for your own use, keep them — they are standard Codex settings, not AgentFW
artifacts. Your dated backup (`~/.codex/AGENTS.md.agentfw-backup-*` and any config backup you
made) is the ground truth for what predated the install.

## 4. Verify removal

```sh
grep -n 'AGENTFW' ~/.codex/AGENTS.md          # expect: no output (or "No such file")
ls ~/.agents/skills/agentfw 2>&1               # expect: No such file or directory
grep -rn 'AGENTFW' ~/.codex/config.toml        # expect: no output
```

Then start a fresh Codex session and ask it to state its operating framework: it should no
longer volunteer assurance levels or `[ASSURANCE: …]` markers.

## Intentionally left behind

- `~/.codex/AGENTS.md.agentfw-backup-*` files — your safety net; delete them yourself when
  you're confident.
- Any plan files, `agentfw-plan` blocks, or evidence artifacts committed into your own repos —
  those are your project's history, not the framework's installation.
