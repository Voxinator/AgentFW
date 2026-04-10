# Claude Code — Install Notes

## Installation Options

### 1. Global Install (applies to all projects)

```bash
cp variants/claude-code/CLAUDE.md ~/.claude/CLAUDE.md
```

If you already have a `~/.claude/CLAUDE.md`, you can append instead:

```bash
cat variants/claude-code/CLAUDE.md >> ~/.claude/CLAUDE.md
```

Or back up the existing one first:

```bash
cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.backup
cp variants/claude-code/CLAUDE.md ~/.claude/CLAUDE.md
```

### 2. Project-Level Install (applies to one project)

```bash
cp variants/claude-code/CLAUDE.md /path/to/your/project/CLAUDE.md
```

Project-level CLAUDE.md takes precedence over global when both exist in a Claude Code session.

### 3. Making References Accessible

For the agent to load on-demand reference files (permissions, playbooks, domain guidelines, etc.), the AgentFW directory must be accessible from the file system. Options:

- **Keep it at a known path** (e.g., `~/projects/AgenticHarness/`)
- **Symlink into the Claude skills directory:**
  ```bash
  ln -s ~/projects/AgenticHarness ~/.claude/skills/agentfw
  ```
- **Use the bootstrap prompt** (`bootstrap.md`) to automate setup, including symlinking

### 4. Verify the Install

Start a new Claude Code session and ask:

> Describe your operating framework. How do you approach multi-step tasks?

The agent should mention:
- Decompose-Parallelize-Verify-Iterate as its core workflow
- Planner-Worker-Judge role separation
- Permission tiers (always-allow, ask-first, never-allow)
- PROGRESS.md for state tracking
- Dispatching sub-agents rather than doing implementation in the main session

If it doesn't reference these concepts, the CLAUDE.md may not have loaded. Check that the file is in the correct location and restart the session.

## Upgrading from r3

If you have the r3 version installed (the original `agentic-harness-project-instructions_r3.md` content in your CLAUDE.md), simply replace it with the r6 variant. The r3 originals are preserved in the `archive/` directory. Key changes since r3:

- Permission model added (r4)
- State management enhanced with task state machine (r4)
- Context budget management (r4)
- Guided mode role separation fixed (r4)
- Evaluation system added (r4)
- Observability (SESSION_LOG) added (r4)
- Structural enforcement hardening — classification gate, verification gates, domain-specific build requirements, Tier 1 enforcement (r5)
- Context degradation resistance — Critical Rules preamble, state-driven health gate, delegation self-check, Rubber-Stamp Compliance anti-pattern (r6)
- Core principles unchanged — r6 restructures and extends, it doesn't rewrite
