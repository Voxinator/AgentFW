# Generic Client — Install Notes

## Installation

### 1. Use as System Prompt or Initial Instructions

Copy the contents of `system-prompt.md` and use it as your system prompt or initial instructions for any AI client. This works with:

- API-based integrations (system message)
- Custom chat interfaces (system prompt field)
- Other AI assistants that accept custom instructions
- Any environment where you can set persistent instructions

### 2. Provide Reference Files on Demand

The system prompt references additional documents (permissions, playbooks, domain guidelines, etc.) that the agent may request during complex tasks. When the agent asks for a reference:

1. Find the file in the AgentFW directory under `references/`, `playbooks/`, or `templates/`
2. Copy the contents and paste them into the conversation
3. The agent will incorporate the reference and continue working

You do not need to provide all references upfront. The agent will request only what it needs.

### 3. Verify

Start a new conversation with the system prompt active and ask:

> Describe your operating framework. How do you approach multi-step tasks?

The agent should mention:
- Decompose-Parallelize-Verify-Iterate as its core workflow
- Planner-Worker-Judge role separation
- Permission tiers (always-allow, ask-first, never-allow)
- Progress tracking for state management

### 4. Best Practices

For best results with the generic variant:

- **Provide the relevant playbook** for your task type (feature dev, bug hunting, etc.) at the start of the conversation
- **Paste templates** (PROGRESS.md, PLAN.md) when the agent begins structured work so it has the format to follow
- **Provide the permissions reference** when the task involves side effects or system changes
- **Start a fresh conversation** when the agent's context gets crowded — bring forward only the PROGRESS.md summary

## Limitations

Without file system access or project knowledge file support, the generic variant requires manual reference delivery. The agent will ask for what it needs, but the human must provide the files. For a more seamless experience, consider using Claude Code (file system access) or Claude Projects (knowledge files).
