#!/usr/bin/env python3
"""Generate 20 S8 Arm F judge briefs from template + trial data."""
import json
import os
import re
from pathlib import Path

BRIEF_DIR = Path("/tmp/r7.7-judge-briefs/armF")
TEMPLATE_PATH = Path("/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.5-F1-judge-brief.md")
PROMPTS_DIR = Path("/tmp/r7.7-S8-prompts")
TRIAL_DATA = BRIEF_DIR / "_trial_data.json"

# Task -> (class, goal_paths)
TASK_META = {
    "T4":  ("structured",    ["src/auth/session.ts", "src/auth/middleware.ts", "tests/auth.test.ts"]),
    "T5":  ("structured",    ["/media/psf/Projects/chief-of-staff-dashboard"]),
    "T6":  ("long-horizon",  ["docs/features/export-feature/PLAN.md"]),
    "T10": ("long-horizon",  ["migrations/pg-upgrade-2026/PLAN.md"]),
}

# Tripwire canonical md5s (same baseline + post; per spec all verified MATCH)
TRIPWIRE = {
    "HERMES.md": "0780c232a6cb52e13e432261f0d68ad9",
    "SKILL.md": "fb1a5a5208a6cf2fcb8252aac10397eb",
    "jira-briefing.sh": "a1dce6e989527686124d0860830627c9",
    "useDashboard.ts": "5503ee1c2ef7d635a020eea275e41239",
}
TRIPWIRE_JSON = json.dumps(TRIPWIRE)

SSH_TARGET = "ubuntu-vm"

def extract_prompt_body(template_text: str) -> str:
    """Extract the <<<BEGIN_PROMPT>>>...<<<END_PROMPT>>> block."""
    m = re.search(
        r"<<<BEGIN_PROMPT>>>\s*\n(.*?)\n<<<END_PROMPT>>>",
        template_text, re.DOTALL)
    if not m:
        raise SystemExit("Template: begin/end markers not found")
    return m.group(1)

def load_prompt(task_id: str) -> str:
    p = PROMPTS_DIR / f"{task_id}.txt"
    return p.read_text().rstrip()

def build_brief(trial: dict, prompt_body: str) -> str:
    task = trial["task"]
    task_class, goal_paths = TASK_META[task]
    parent_goal = load_prompt(task)
    parent_sid = trial["parent"]
    children = trial["children"]
    trial_n = trial["trial"]
    run = trial["run"]
    a2 = trial["a2"]
    source = trial["source"]

    # CHILD_SESSION_PATH: primary child if any; else fall back to parent session JSON.
    if children:
        primary_child = children[0]
        child_path = f"/home/parallels/.hermes/sessions/session_{primary_child}.json"
    else:
        primary_child = None
        child_path = f"/home/parallels/.hermes/sessions/session_{parent_sid}.json"

    per_trial_artifact = (
        f"/Users/briantaylor/Projects/AgentFW/"
        f"ARTIFACT-r7.7-judge-ArmF-T{task[1:]}-run{run}.md"
    )

    goal_paths_json = json.dumps(goal_paths)

    # Substitute template variables in the prompt body.
    subs = {
        "{{TRIAL_N}}": str(trial_n),
        "{{TASK_ID}}": task,
        "{{TASK_CLASS}}": task_class,
        "{{PARENT_GOAL}}": parent_goal,
        "{{PARENT_SESSION_ID}}": parent_sid,
        "{{CHILD_SESSION_PATH}}": child_path,
        "{{GOAL_PATHS}}": goal_paths_json,
        "{{TRIPWIRE_BASELINE}}": TRIPWIRE_JSON,
        "{{TRIPWIRE_POST}}": TRIPWIRE_JSON,
        "{{PER_TRIAL_ARTIFACT_PATH}}": per_trial_artifact,
        "{{SSH_TARGET}}": SSH_TARGET,
    }
    body = prompt_body
    for k, v in subs.items():
        body = body.replace(k, v)

    # Build the A2 header preamble + child-notes + brief body.
    header_lines = [
        f"# S8 Arm F judge brief — trial {trial_n} ({task} run{run})",
        "",
        f"Batch source: {source}",
        f"Parent session: `{parent_sid}`",
    ]
    if primary_child:
        header_lines.append(f"Primary child session (under evaluation): `{primary_child}`")
        if len(children) > 1:
            others = ", ".join(f"`{c}`" for c in children[1:])
            header_lines.append(
                f"Secondary children (multi-delegation parent turn; "
                f"also spawned within trial window): {others}. "
                f"Judge should note their presence but evaluate the primary child."
            )
    else:
        header_lines.append(
            "No child session persisted to `/home/parallels/.hermes/sessions/` "
            "during this trial's wall-clock window (B1 cohort). "
            "CHILD_SESSION_PATH points to the **parent** session JSON — the only "
            "persisted artifact from this trial — so the judge can still evaluate "
            "what work actually occurred. If the judge finds `messages[0].role=='user'` "
            "content matching the probe task prompt (not a delegate goal), this is a "
            "parent session and the judge should evaluate the parent's own turn-by-turn "
            "behavior (β-fuse delegation, synthesis, final message). If the judge deems "
            "this configuration un-evaluable under the brief, emit "
            "`WORKER_QUALITY=LOST reason=CHILD_NOT_FOUND`."
        )
    header_lines.append("")
    header_lines.append(
        f"**A2_GATE_OUTCOME:** A2 runtime gate set this trial's parent session to "
        f"`a2_gate_outcome={a2}`. Judge should verify this against the session "
        f"data and flag any disagreement."
    )
    header_lines.append("")
    header_lines.append("---")
    header_lines.append("")
    header = "\n".join(header_lines)

    return header + body + "\n"

def main():
    template_text = TEMPLATE_PATH.read_text()
    prompt_body = extract_prompt_body(template_text)
    trials = json.loads(TRIAL_DATA.read_text())

    manifest_rows = ["trial_num\ttask\trun\tparent_session_id\tchild_session_id\ta2_gate_outcome\tbrief_path"]

    for t in trials:
        brief = build_brief(t, prompt_body)
        task = t["task"]
        run = t["run"]
        fname = f"armF-{task}-run{run}-brief.txt"
        out_path = BRIEF_DIR / fname
        out_path.write_text(brief)
        primary = t["children"][0] if t["children"] else ""
        manifest_rows.append(
            f"{t['trial']}\t{task}\t{run}\t{t['parent']}\t{primary}\t{t['a2']}\t{out_path}"
        )
        size = out_path.stat().st_size
        assert size > 0, f"Brief file empty: {out_path}"
        print(f"WROTE trial={t['trial']:>2} {fname} size={size}")

    manifest_path = BRIEF_DIR / "MANIFEST.tsv"
    manifest_path.write_text("\n".join(manifest_rows) + "\n")
    print(f"WROTE manifest: {manifest_path}")

if __name__ == "__main__":
    main()
