# Codex feasibility probe — 2026-07-13

- CLI: codex-cli 0.144.1 at /opt/homebrew/bin/codex, authenticated.
- Probe 1 (read-only, default config): session started (session id 019f5c82-551a-7343-8207-985c115ad69e),
  but the user's configured MCP servers emitted headless-auth errors (figma/vercel/atlassian/circleback/
  copilot) — noise, non-fatal. Run guarded by a manual kill window; reply not captured before the guard.
- Probe 2 (hermetic): `codex exec --skip-git-repo-check -s read-only -c mcp_servers='{}' "Reply with
  exactly: CODEX-SMOKE-OK"` in a fresh `git init` mktemp dir → **exit 0**, reply `CODEX-SMOKE-OK`
  present (3 occurrences incl. echo), session id 019f5c85-5217-78c1-80dd-7cdb99f56312, token usage
  reported. Defaults observed: sandbox read-only honored, reasoning effort high.
- VERDICT: **feasible**. Eval runs use: fresh mktemp fixture dir per GT, `git init`, adapter layout per
  adapters/codex/INSTALL.md (AGENTS.md content at repo root, .agents/skills/agentfw/ with SKILL.md +
  policy/ + tools/validate-plan, capability.yaml), `codex exec --skip-git-repo-check -s workspace-write
  -c mcp_servers='{}' < /dev/null`, shell-level kill-window guard (macOS has no `timeout`/`gtimeout`).
- Real-run authenticity: each transcript records its `session_id:`; rollout files under ~/.codex/sessions
  are cross-checked by E3's acceptance command.

Session ids recorded for the smoke probes (not eval cells):
session_id: 019f5c82-551a-7343-8207-985c115ad69e
session_id: 019f5c85-5217-78c1-80dd-7cdb99f56312
