# Claude Projects — Install Notes

## Installation

### 1. Set Custom Instructions

1. Open your Claude Project
2. Go to **Project Settings** (gear icon or "Edit project")
3. Find **Custom Instructions** (sometimes labeled "Set custom instructions" or "System prompt")
4. Copy the entire contents of `custom-instructions.md` and paste it into the custom instructions field
5. Save

### 2. Upload Project Knowledge Files

Upload the following files from the AgentFW directory as project knowledge files:

**Core:**
- `core/permissions.md`

**References:**
- `references/state-management.md`
- `references/verification-tiers.md`
- `references/error-recovery.md`
- `references/prompt-design.md`
- `references/domain-guidelines.md`
- `references/anti-patterns.md`
- `references/observability.md`

**Playbooks:**
- `playbooks/feature-dev.md`
- `playbooks/bug-hunting.md`
- `playbooks/maker-project.md`
- `playbooks/pm-investigation.md`
- `playbooks/cross-scenario-patterns.md`

**Templates:**
- `templates/PROGRESS.md`
- `templates/PLAN.md`
- `templates/SESSION_LOG.md`
- `templates/DIAGNOSTIC.md`

**Evaluation (optional):**
- `evaluation/golden-tasks.md`
- `evaluation/eval-protocol.md`

You do not need to upload all files at once. Start with the core and references, then add playbooks and templates as needed. Claude Projects has a knowledge file limit, so prioritize based on your use case.

### 3. Verify the Install

Start a new conversation in the project and ask:

> Describe your operating framework. How do you approach multi-step tasks?

The agent should mention:
- Decompose-Parallelize-Verify-Iterate as its core workflow
- Planner-Worker-Judge role separation
- Permission tiers (always-allow, ask-first, never-allow)
- Progress tracking for state management
- Role separation between planning, implementation, and verification

If it doesn't reference these concepts, check that the custom instructions saved correctly and that the knowledge files uploaded.

### 4. Test with a Real Task

Give the project a multi-step request such as:

> I need to design a REST API for a task management system. It should support creating, reading, updating, and deleting tasks, with user authentication and team-based permissions.

The agent should:
1. Decompose the problem into sub-tasks
2. Create a structured plan before jumping into implementation
3. Propose verification criteria for each piece
4. Work through sub-tasks systematically rather than producing one massive answer

## Upgrading from r3

If your project has the r3 framework in custom instructions, replace it entirely with the r6 `custom-instructions.md` content. The core principles are unchanged — r6 restructures and extends with permissions, observability, evaluation, structural enforcement gates, and context degradation resistance.
