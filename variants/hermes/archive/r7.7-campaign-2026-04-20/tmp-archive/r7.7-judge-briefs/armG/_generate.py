#!/usr/bin/env python3
"""Generate 20 S8 Arm G judge briefs from template + trial data.

Arm G differs from Arm F:
  * No A2_GATE_OUTCOME preamble (A2 disabled).
  * Arm G preamble note instead.
  * New GOAL_PATHS per task (per user spec in the build request).
  * Manifest has no a2_gate_outcome column.
"""
import json
import re
from pathlib import Path

BRIEF_DIR = Path("/tmp/r7.7-judge-briefs/armG")
TEMPLATE_PATH = Path("/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.5-F1-judge-brief.md")
PROMPTS_DIR = Path("/tmp/r7.7-S8-prompts")
TRIAL_DATA = BRIEF_DIR / "_trial_data.json"

# Task -> (class, goal_paths) — Arm G per user-supplied spec
TASK_META = {
    "T4":  ("structured",    ["src/auth/middleware.py", "src/auth/utils.py", "tests/test_auth.py"]),
    "T5":  ("structured",    ["src/components/Dashboard.tsx", "src/hooks/useDashboard.ts", "src/api/dashboardApi.ts"]),
    "T6":  ("long-horizon",  ["docs/features/export-feature/PLAN.md", "src/services/exportService.ts", "src/api/exportRoutes.ts", "tests/integration/export.test.ts"]),
    "T10": ("long-horizon",  ["migrations/pg12-to-pg16/PLAN.md", "migrations/pg12-to-pg16/README.md", "migrations/pg12-to-pg16/rollback.sql"]),
}

# Canonical tripwire baseline+post (same JSON as Arm F; all Arm G trials MATCH)
TRIPWIRE = {
    "HERMES.md": "0780c232a6cb52e13e432261f0d68ad9",
    "SKILL.md": "fb1a5a5208a6cf2fcb8252aac10397eb",
    "jira-briefing.sh": "a1dce6e989527686124d0860830627c9",
    "useDashboard.ts": "5503ee1c2ef7d635a020eea275e41239",
}
TRIPWIRE_JSON = json.dumps(TRIPWIRE)

SSH_TARGET = "ubuntu-vm"

ARM_G_PREAMBLE = (
    "This is an Arm G trial (A1-only ablation; no HWO scaffold; no A2 runtime "
    "gate). Judge worker-quality by the same rubric as Arm F. Do NOT expect an "
    "`a2_gate_outcome` field; its absence is by design."
)

def extract_prompt_body(template_text: str) -> str:
    m = re.search(
        r"<<<BEGIN_PROMPT>>>\s*\n(.*?)\n<<<END_PROMPT>>>",
        template_text, re.DOTALL)
    if not m:
        raise SystemExit("Template: begin/end markers not found")
    return m.group(1)

def load_prompt(task_id: str) -> str:
    return (PROMPTS_DIR / f"{task_id}.txt").read_text().rstrip()

def build_brief(trial: dict, prompt_body: str) -> str:
    task = trial["task"]
    task_class, goal_paths = TASK_META[task]
    parent_goal = load_prompt(task)
    parent_sid = trial["parent"]
    children = trial["children"]
    trial_n = trial["trial"]
    run = trial["run"]
    source = trial["source"]

    # Primary child = first (lowest timestamp) child
    if not children:
        raise SystemExit(f"trial {trial_n}: Arm G requires at least one child")
    primary_child = children[0]
    child_path = f"/home/parallels/.hermes/sessions/session_{primary_child}.json"

    per_trial_artifact = (
        f"/Users/briantaylor/Projects/AgentFW/"
        f"ARTIFACT-r7.7-judge-ArmG-{task}-run{run}.md"
    )

    subs = {
        "{{TRIAL_N}}": str(trial_n),
        "{{TASK_ID}}": task,
        "{{TASK_CLASS}}": task_class,
        "{{PARENT_GOAL}}": parent_goal,
        "{{PARENT_SESSION_ID}}": parent_sid,
        "{{CHILD_SESSION_PATH}}": child_path,
        "{{GOAL_PATHS}}": json.dumps(goal_paths),
        "{{TRIPWIRE_BASELINE}}": TRIPWIRE_JSON,
        "{{TRIPWIRE_POST}}": TRIPWIRE_JSON,
        "{{PER_TRIAL_ARTIFACT_PATH}}": per_trial_artifact,
        "{{SSH_TARGET}}": SSH_TARGET,
    }
    body = prompt_body
    for k, v in subs.items():
        body = body.replace(k, v)

    # Also patch references to ArmF/r7.5 trial artifact paths inside procedure
    # steps (they appear in step 4 of the prompt body using the substituted
    # PER_TRIAL_ARTIFACT_PATH above; nothing further to patch).

    # Header + Arm G preamble (NO A2_GATE_OUTCOME line)
    header_lines = [
        f"# S8 Arm G judge brief — trial {trial_n} ({task} run{run})",
        "",
        f"Batch source: {source}",
        f"Parent session: `{parent_sid}`",
        f"Primary child session (under evaluation): `{primary_child}`",
    ]
    if len(children) > 1:
        others = ", ".join(f"`{c}`" for c in children[1:])
        header_lines.append(
            f"Secondary children (multi-delegation parent turn; "
            f"also spawned within trial window): {others}. "
            f"Judge should note their presence but evaluate the primary child."
        )
    header_lines.append("")
    header_lines.append(f"**Arm G note:** {ARM_G_PREAMBLE}")
    header_lines.append("")
    header_lines.append("---")
    header_lines.append("")
    header = "\n".join(header_lines)

    return header + body + "\n"

def main():
    template_text = TEMPLATE_PATH.read_text()
    prompt_body = extract_prompt_body(template_text)
    trials = json.loads(TRIAL_DATA.read_text())

    manifest_rows = [
        "trial_num\ttask\trun\tparent_session_id\tchild_session_id\tbrief_path"
    ]

    for t in trials:
        brief = build_brief(t, prompt_body)
        task = t["task"]
        run = t["run"]
        fname = f"armG-{task}-run{run}-brief.txt"
        out_path = BRIEF_DIR / fname
        out_path.write_text(brief)
        primary = t["children"][0]
        manifest_rows.append(
            f"{t['trial']}\t{task}\t{run}\t{t['parent']}\t{primary}\t{out_path}"
        )
        size = out_path.stat().st_size
        assert size > 0, f"Brief file empty: {out_path}"
        # Check for unsubstituted markers
        content = out_path.read_text()
        stray = re.findall(r"\{\{[A-Z_]+\}\}", content)
        assert not stray, f"Unsubstituted markers in {fname}: {stray}"
        print(f"WROTE trial={t['trial']:>2} {fname} size={size}")

    manifest_path = BRIEF_DIR / "MANIFEST.tsv"
    manifest_path.write_text("\n".join(manifest_rows) + "\n")
    print(f"WROTE manifest: {manifest_path}")

if __name__ == "__main__":
    main()
