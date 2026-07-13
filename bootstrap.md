> **r9 note:** this file is the **r8** installer. The r9 draft installs via `adapters/<platform>/INSTALL.md` instead.

# AgentFW r8 — Bootstrap Install

You are about to install AgentFW r8. This restructures how you work — from single-turn chatbot to a governance layer over Claude Code 2.1's native runtime primitives (Workflow tool, Agent subagents, Plan mode, Skills, MEMORY, hooks, permission modes). The firmware decides whether/when/how-well to orchestrate; the runtime executes how. v8 is Claude-Code-only.

## Step 1: Confirm Your Environment

AgentFW v8 targets **Claude Code** exclusively. You have access to file system tools (Read, Write, Edit, Bash, Glob, Grep) and to the Claude Code 2.1 runtime primitives the firmware governs. If you are not in Claude Code, v8 does not apply.

## Step 2: Locate AgentFW

The AgentFW files should be accessible at one of:
- `~/projects/AgenticHarness/` (default development location)
- A path the user specifies
- Files attached to this conversation

Read the directory listing to confirm the files exist. Look for the `core/`, `references/`, `playbooks/`, and `templates/` directories.

## Step 3: Install

### Claude Code:

1. Read `core/harness-core.md` from the AgentFW directory — in v8 this is the always-load core that installs as CLAUDE.md (it carries the v8 governance layer over the native primitives)
2. Determine install scope with the user:
   - **Global** (all projects): Install to `~/.claude/CLAUDE.md`
   - **Project-level** (this project only): Install to the current project root as `CLAUDE.md`
3. If a CLAUDE.md already exists at the target location, show the user what's there and ask:
   - Replace entirely?
   - Append the harness framework?
   - Merge manually? (output both side by side for comparison)
4. Write the file to the chosen location
5. Ensure the AgentFW directory is accessible for on-demand references. If it's not in a standard location, suggest creating a symlink:
   ```bash
   ln -s /actual/path/to/AgenticHarness ~/.claude/skills/agentfw
   ```
6. Verify by reading back the installed file and confirming it contains the "AgentFW — Core Instructions" header and the Critical Rules section (including Rule 6: PREFER NATIVE PRIMITIVES)

v8 is Claude-Code-only; there are no Claude Projects or generic client variants to install.

## Step 4: Post-Install Verification

Run a quick smoke test:

1. Ask yourself: "If I received a multi-step feature request right now, would I:
   - Create a PLAN.md with decomposed sub-tasks?
   - Propose dispatching worker sub-agents with scoped permissions?
   - Plan for separate verification by a judge sub-agent?
   - Maintain PROGRESS.md for state tracking?
   - Respect the permission tiers (always-allow, ask-first, never-allow)?"
2. If yes to all, the harness is active.
3. If no, re-read the installed instructions and identify what's missing.

Report the install result to the user:

```
AgentFW r8 — Install Report
====================================
AgentFW version:      r8
Install type:         [Global / Project-level]
Install path:         [where it was installed]
References accessible: [yes/no — path if yes]
Status:               [Ready / Needs attention — details]
```

## Upgrading from r6 / r7

v8 installs `core/harness-core.md` as the CLAUDE.md core. If the user already has an r6 or r7 AgentFW core installed, the v8 install **overwrites the installed CLAUDE.md** — back it up first if the user wants to keep the prior version, then write the v8 core in its place. The behavioral fundamentals carry forward; v8 reframes the firmware as a governance layer over Claude Code 2.1's native primitives (it no longer hand-rolls the orchestration mechanics the runtime now provides).

## Upgrading from r3

If the user has an existing CLAUDE.md with the r3 version, you can identify it by:
- The heading "Agentic Harness Framework — Project Instructions" (the old project name)
- The "jagged frontier" paragraph in the introduction
- Sections on "The Harness Mindset" and "Decompose -> Parallelize -> Verify -> Iterate" without the permission protocol

When upgrading:

1. Note that the r3 content will be replaced by the r6 variant
2. The r3 originals are preserved in the `archive/` directory within the AgentFW installation
3. Key changes in r6 (since r3):
   - **Permission model added** — Three-tier trust system (always-allow, ask-first, never-allow) with worker scoping
   - **State management enhanced** — Task state machine, structured checkpoints, enhanced PROGRESS.md
   - **Context budget managed** — Reference loading protocol, on-demand file loading instead of front-loading
   - **Guided mode role separation fixed** — Explicit role transition protocol for non-Claude-Code environments
   - **Evaluation system added** — Golden tasks and eval protocol for regression testing harness behavior
   - **Observability added** — SESSION_LOG protocol for autonomous mode transparency and permission audit
   - **Structural enforcement gates** — Mandatory classification gate (`[TASK CLASS]`), verification gates blocking downstream dispatch, Tier 1 machine-check enforcement
   - **Context degradation resistance** — Critical Rules preamble, state-driven health gate (`[CONTEXT HEALTH]`), delegation self-check, Rubber-Stamp Compliance anti-pattern
4. The core framework principles are unchanged — r6 restructures and extends, it doesn't rewrite the fundamentals
