# AgentFW r4 — Bootstrap Install

You are about to install AgentFW r4. This restructures how you work — from single-turn chatbot to structured agent with decomposition, verification, role separation, and persistent state.

## Step 1: Detect Your Environment

Determine which AI client you're running in:

- **Claude Code**: You have access to file system tools (Read, Write, Edit, Bash, Glob, Grep). You can read and write files directly.
- **Claude Projects**: You're in a Claude project with custom instructions and knowledge files. No file system access.
- **Other**: You're in a generic chat or API environment.

## Step 2: Locate AgentFW

The AgentFW files should be accessible at one of:
- `~/projects/AgenticHarness/` (default development location)
- A path the user specifies
- Files attached to this conversation

If you're in Claude Code, read the directory listing to confirm the files exist. Look for the `variants/`, `core/`, `references/`, `playbooks/`, and `templates/` directories.

## Step 3: Install

### If Claude Code:

1. Read `variants/claude-code/CLAUDE.md` from the AgentFW directory
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
6. Verify by reading back the installed file and confirming it contains the "AgentFW — Core Instructions" header and the Extended References section

### If Claude Projects:

1. Read and output the full contents of `variants/claude-projects/custom-instructions.md`
2. Instruct the user to:
   - Open Project Settings
   - Paste the content into Custom Instructions
   - Save
3. List the files from `references/`, `playbooks/`, and `templates/` that should be uploaded as project knowledge files:
   - `core/permissions.md`
   - All files in `references/`
   - All files in `playbooks/`
   - All `.md` files in `templates/`
4. Walk the user through uploading them one section at a time

### If Other:

1. Read and output the full contents of `variants/generic/system-prompt.md`
2. Instruct the user on how to use it as their system prompt or initial instructions
3. Explain that reference files should be provided on demand when the agent requests them
4. Suggest starting with the permissions reference and the playbook most relevant to their use case

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
AgentFW r4 — Install Report
====================================
AgentFW version:      r4
Install type:         [Global / Project-level / Custom Instructions / System Prompt]
Install path:         [where it was installed]
References accessible: [yes/no — path if yes]
Status:               [Ready / Needs attention — details]
```

## Upgrading from r3

If the user has an existing CLAUDE.md with the r3 version, you can identify it by:
- The heading "Agentic Harness Framework — Project Instructions" (the old project name)
- The "jagged frontier" paragraph in the introduction
- Sections on "The Harness Mindset" and "Decompose -> Parallelize -> Verify -> Iterate" without the permission protocol

When upgrading:

1. Note that the r3 content will be replaced by the r4 variant
2. The r3 originals are preserved in the `archive/` directory within the AgentFW installation
3. Key changes in r4:
   - **Permission model added** — Three-tier trust system (always-allow, ask-first, never-allow) with worker scoping
   - **State management enhanced** — Task state machine, structured checkpoints, enhanced PROGRESS.md
   - **Context budget managed** — Reference loading protocol, on-demand file loading instead of front-loading
   - **Guided mode role separation fixed** — Explicit role transition protocol for non-Claude-Code environments
   - **Evaluation system added** — Golden tasks and eval protocol for regression testing harness behavior
   - **Observability added** — SESSION_LOG protocol for autonomous mode transparency and permission audit
4. The core framework principles are unchanged — r4 restructures and extends, it doesn't rewrite the fundamentals
