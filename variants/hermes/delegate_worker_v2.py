"""
β-fuse v2: fused classification + dispatch. Side-by-side with delegate_worker
during migration (r7.4). Spec: ARTIFACT-impl-3-beta-fuse-spec.md.

Rationale: the r7.3 probe found MoE's dominant structured-task failure mode
was "marker-without-dispatch" — the model writes `[TASK CLASS: structured]`
and then terminates generation without a tool call. Decoupling the
classification marker from the dispatch tool call lets that failure survive.
This tool fuses the two: calling it IS the classification, and for
structured/long-horizon tasks it also IS the dispatch. "Marker without
dispatch" becomes representationally impossible.

Surface:
  * classification (required, enum): one-shot | structured | long-horizon
  * justification  (required, string, len >= 30): concrete reason
  * goal           (optional in schema; required by handler for
                    structured/long-horizon): self-contained worker spawn

Semantics:
  * one-shot            -> returns immediately; model continues in main session.
  * structured          -> calls delegate_task(goal=..., parent_agent=...).
  * long-horizon        -> calls delegate_task(goal=..., parent_agent=...).

Migration: this tool is registered alongside the existing `delegate_worker`.
Both remain callable during r7.4 phase A. HERMES.md teaches v2 exclusively
starting in phase C. v1 is sunset in phase E once adoption holds.
"""

from tools.delegate_tool import delegate_task
from tools.registry import registry


DELEGATE_WORKER_V2_SCHEMA = {
    "name": "delegate_worker_v2",
    "description": (
        # Sentence 1 — the imperative. Highest-attention slot.
        "Call this tool as your FIRST action on every task — including one-shots. "
        # Sentence 2 — what it does + why it's required.
        "It records your task classification (one-shot, structured, or "
        "long-horizon) and, for structured/long-horizon tasks, spawns a worker "
        "subagent in an isolated context. "
        # Sentence 3 — the anti-pattern this prevents.
        "There is no other way to satisfy the AgentFW classification contract; "
        "writing `[TASK CLASS: ...]` in prose without calling this tool is a "
        "protocol violation.\n\n"
        # Behavior block.
        "Behavior by classification:\n"
        "  * one-shot: returns immediately with an acknowledgement. You then "
        "    answer in the main session. Use this ONLY when zero files will be "
        "    modified, OR exactly one file under 20 lines with no cross-file "
        "    dependencies.\n"
        "  * structured / long-horizon: spawns a worker via delegate_task. "
        "    `goal` is REQUIRED and must be self-contained (worker has no "
        "    memory of your conversation). Do NOT call patch, write_file, "
        "    terminal, execute_code, or skill_manage in the main session for "
        "    these classes — dispatch.\n\n"
        "When in doubt between one-shot and structured, choose structured."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "classification": {
                "type": "string",
                "enum": ["one-shot", "structured", "long-horizon"],
                "description": (
                    "Task class. one-shot = zero or one trivial file change. "
                    "structured = multi-file, multi-component, or has "
                    "side-effects worth tracking. long-horizon = spans "
                    "multiple sessions or requires accumulated state."
                ),
            },
            "justification": {
                "type": "string",
                "minLength": 30,
                "description": (
                    "Concrete reason this task falls in the chosen class. "
                    "Reference the specific properties of THIS task (files "
                    "involved, side-effect surface, verification needs) — not "
                    "generic boilerplate. Minimum 30 characters."
                ),
            },
            "goal": {
                "type": "string",
                "description": (
                    "REQUIRED for structured and long-horizon. Self-contained "
                    "worker spawn instruction: what to do, which file paths "
                    "matter, what constraints apply, what 'done' looks like. "
                    "Worker knows nothing about your conversation. "
                    "OPTIONAL for one-shot (ignored if provided)."
                ),
            },
        },
        "required": ["classification", "justification"],
    },
}


def delegate_worker_v2(classification, justification, goal=None,
                       parent_agent=None):
    """β-fuse handler. See module docstring + spec §2."""
    # Argument validation — classification enum
    if classification not in ("one-shot", "structured", "long-horizon"):
        return {"error": f"invalid classification: {classification!r}"}

    # Argument validation — justification type + length
    if not isinstance(justification, str) or len(justification) < 30:
        return {
            "error": "justification must be a string of at least 30 chars"
        }

    # One-shot: acknowledge and return. The classification + justification are
    # captured in the tool_call args (visible to the gate-checker). No child
    # spawn. The model continues in the main session.
    if classification == "one-shot":
        return {
            "ok": True,
            "classified": "one-shot",
            "message": (
                "Classified as one-shot. Proceed in the main session. "
                "Remember: if you find yourself touching more than one file "
                "or more than ~20 lines, stop and re-call delegate_worker_v2 "
                "with classification='structured'."
            ),
        }

    # Structured / long-horizon: goal is required.
    if not goal or not isinstance(goal, str):
        return {
            "error": (
                "goal is required for classification "
                f"{classification!r}. Provide a self-contained worker spawn "
                "instruction (what to do, file paths, constraints, success "
                "criteria)."
            )
        }

    # Spawn child via delegate_task internals (same path as legacy
    # delegate_worker).
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
    name="delegate_worker_v2",
    toolset="delegation",
    schema=DELEGATE_WORKER_V2_SCHEMA,
    handler=lambda args, **kw: delegate_worker_v2(
        classification=args.get("classification"),
        justification=args.get("justification"),
        goal=args.get("goal"),
        parent_agent=kw.get("parent_agent"),
    ),
    check_fn=lambda: True,
    emoji="🔀",
)
