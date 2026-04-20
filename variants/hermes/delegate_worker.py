"""
Delegate Worker — single-arg dispatch wrapper around delegate_task.

Designed for models (e.g. Gemma-4-31B) that emit simple tool calls reliably
but struggle with delegate_task's two-mode union schema and nested-array
arguments.

Surface: one required string argument `goal`. Internally calls delegate_task
with sane defaults (no batch mode, inherit toolsets).

This file is a probe artifact for the AgentFW Variant D experiment. To remove,
delete the file and revert the corresponding entries in model_tools.py and
toolsets.py.
"""

from tools.delegate_tool import delegate_task
from tools.registry import registry


DELEGATE_WORKER_SCHEMA = {
    "name": "delegate_worker",
    "description": (
        "Spawn ONE worker subagent to complete a task in an isolated, fresh "
        "context. The worker has its own conversation, terminal, and toolset; "
        "only the final summary is returned to you.\n\n"
        "ALWAYS USE THIS TOOL when the task class is `structured` or "
        "`long-horizon`. Do NOT call patch, write_file, terminal, "
        "execute_code, or skill_manage directly from the main session for "
        "such tasks — dispatch to a worker via this tool instead.\n\n"
        "Pass everything the worker needs in the single `goal` argument — "
        "the worker has no memory of your conversation. Include: what to do, "
        "which files matter, what constraints apply, and what 'done' looks "
        "like. Be specific and self-contained."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "goal": {
                "type": "string",
                "description": (
                    "Self-contained task description for the worker. Include "
                    "all necessary context: file paths, constraints, success "
                    "criteria. The worker knows nothing about your "
                    "conversation."
                ),
            },
        },
        "required": ["goal"],
    },
}


def delegate_worker(goal, parent_agent=None):
    if not goal or not isinstance(goal, str):
        return {"error": "goal must be a non-empty string"}
    return delegate_task(
        goal=goal,
        context=None,
        toolsets=None,
        tasks=None,
        max_iterations=None,
        acp_command=None,
        acp_args=None,
        parent_agent=parent_agent,
    )


registry.register(
    name="delegate_worker",
    toolset="delegation",
    schema=DELEGATE_WORKER_SCHEMA,
    handler=lambda args, **kw: delegate_worker(
        goal=args.get("goal"),
        parent_agent=kw.get("parent_agent"),
    ),
    check_fn=lambda: True,
    emoji="🔀",
)
