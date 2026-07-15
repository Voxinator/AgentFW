#!/usr/bin/env bash
# Deterministic release gate for AgentFW v9.1.0.
#
# AGENTFW_RELEASE_ROOT may point at a scratch copy for red-path probes.
# AGENTFW_RELEASE_IDENTITY_ONLY=1 stops after release-document checks; the normal contracted
# acceptance command sets neither variable and always runs every deterministic suite below.
set -euo pipefail

SCRIPT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ROOT=${AGENTFW_RELEASE_ROOT:-$SCRIPT_ROOT}

fail() {
  printf 'release-v9.1.sh: FAIL: %s\n' "$*" >&2
  exit 1
}

require_file() {
  local path=$1
  [ -f "$ROOT/$path" ] || fail "missing required file: $path"
}

require_contains() {
  local path=$1
  local text=$2
  grep -Fq -- "$text" "$ROOT/$path" \
    || fail "$path is missing required text: $text"
}

require_not_contains() {
  local path=$1
  local text=$2
  if grep -Fq -- "$text" "$ROOT/$path"; then
    fail "$path contains stale current-facing text: $text"
  fi
}

for required in \
  metadata.json \
  README.md \
  CHANGELOG.md \
  DESIGN.md \
  RELEASE-NOTES-v9.1.0.md \
  R9X-CANDIDATES.md \
  PLAN-bonksnake-fixture.md \
  PROMPTS-v9-paces.md \
  profiles/chatgpt-projects.md \
  adapters/claude-code/INSTALL.md \
  adapters/codex/INSTALL.md
do
  require_file "$required"
done

python3 - "$ROOT/metadata.json" <<'PY' \
  || fail "metadata.json must report version 9.1.0 and revision r9.1"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
assert data.get("version") == "9.1.0", data.get("version")
assert data.get("revision") == "r9.1", data.get("revision")
PY

require_contains README.md '**Status: v9.1.0, released 2026-07-15**'
require_contains README.md 'deferred to **v9.2** as the designated adapter candidate'
require_contains README.md 'No new behavioral-evaluation round'
require_contains profiles/chatgpt-projects.md 'Current release: **AgentFW v9.1.0**'
require_contains profiles/chatgpt-projects.md 'designated v9.2 candidate'
require_contains adapters/claude-code/INSTALL.md 'Current release: **AgentFW v9.1.0**'
require_contains adapters/codex/INSTALL.md 'Current release: **AgentFW v9.1.0**'
require_contains DESIGN.md '**Current-release note (v9.1.0):**'

# These phrases were current-facing in v9.0.0. They are forbidden only in adopter-facing docs;
# historical changelog/plan records intentionally retain their original release-era wording.
require_not_contains README.md 'deferred to **r9.1** as the designated adapter candidate'
require_not_contains README.md 'reserved for **r9.1**'
require_not_contains profiles/chatgpt-projects.md 'designated r9.1 candidate'

require_contains CHANGELOG.md '## v9.1.0 (2026-07-15) — RELEASED'
require_contains CHANGELOG.md 'C-1 — acceptance-command red paths'
require_contains CHANGELOG.md 'C-2 — first-class mutation probes'
require_contains CHANGELOG.md 'C-3 — fixture leak-channel hygiene'
require_contains CHANGELOG.md 'C-4 — empirical critic duties'
require_contains CHANGELOG.md 'C-5 — named cap relaxations'
require_contains CHANGELOG.md 'C-6 — resolved command evidence'
require_contains CHANGELOG.md 'schema **1.3**'
require_contains CHANGELOG.md 'no golden task, Bonksnake prompt, or behavioral evaluation was'

require_contains RELEASE-NOTES-v9.1.0.md 'schema 1.3 mutation probes'
require_contains RELEASE-NOTES-v9.1.0.md 'both capability-validator parser paths'
require_contains RELEASE-NOTES-v9.1.0.md 'No golden task, Bonksnake prompt, or additional behavioral-evaluation round was run'
require_contains RELEASE-NOTES-v9.1.0.md 'are provenance only'

# Preserve public v9.0.0 history while adding v9.1.0 current-facing documentation.
require_contains CHANGELOG.md '## v9.0.0 (2026-07-15) — RELEASED'
require_contains CHANGELOG.md 'designated r9.1 *adapter* candidate'
require_contains README.md '**v9.0.0** (2026-07-15): **Released.**'
require_contains DESIGN.md '| v9.0.0 | 2026-07-15 |'

python3 - "$ROOT/R9X-CANDIDATES.md" <<'PY' \
  || fail "R9X-CANDIDATES.md must mark exactly C-1 through C-6 implemented and verified"
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()
ids = re.findall(r"^## (C-[1-6])\b", text, flags=re.MULTILINE)
assert ids == ["C-1", "C-2", "C-3", "C-4", "C-5", "C-6"], ids
statuses = re.findall(r"^\*\*Status:\*\* ([^\n]+)", text, flags=re.MULTILINE)
assert len(statuses) == 6, statuses
assert all(status.startswith("implemented and verified") for status in statuses), statuses
assert "[PLAN-bonksnake-fixture.md](PLAN-bonksnake-fixture.md)" in text
assert "[PROMPTS-v9-paces.md](PROMPTS-v9-paces.md)" in text
assert "provenance only" in text
assert "prompt battery was not executed" in text
PY

require_contains PLAN-bonksnake-fixture.md '**STATUS: HALTED AT PLAN GATE'
require_contains PROMPTS-v9-paces.md '# PROMPTS-v9-paces.md — Taking AgentFW v9 through its paces'

# Root release documents are outside tools/tests/check-links.sh's normal scan. Check their
# relative Markdown links here so the release-note/provenance chain is mechanically covered.
python3 - "$ROOT" <<'PY' \
  || fail "a root release-document link is unresolved"
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
for relative in ("README.md", "CHANGELOG.md", "RELEASE-NOTES-v9.1.0.md", "R9X-CANDIDATES.md"):
    source = root / relative
    text = source.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = target.split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        candidate = source.parent / target
        root_candidate = root / target
        assert candidate.exists() or root_candidate.exists(), f"{relative} -> {target}"
PY

printf 'release-v9.1.sh: PASS: release identity, current docs, candidate status, and provenance\n'

if [ "${AGENTFW_RELEASE_IDENTITY_ONLY:-0}" = 1 ]; then
  printf 'RELEASE_V9_1_IDENTITY_OK\n'
  exit 0
fi

(
  cd "$ROOT"
  bash tools/tests/validate-plan.sh
)
printf 'release-v9.1.sh: PASS: validator fixture harness\n'

(
  cd "$ROOT"
  bash tools/tests/install-roundtrip.sh
)
printf 'release-v9.1.sh: PASS: installer roundtrip\n'

(
  cd "$ROOT"
  bash tools/tests/check-links.sh
)
printf 'release-v9.1.sh: PASS: relative links\n'

# Prove the default interpreter has PyYAML before calling the validator, so this cannot silently
# exercise the fallback twice.
python3 -c 'import yaml' \
  || fail "PyYAML is unavailable; cannot exercise both capability parser paths"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
printf 'release-v9.1.sh: PASS: capability validation via PyYAML\n'

# -S omits site-package initialization, making PyYAML unavailable and deterministically selecting
# the validator's stdlib line-based fallback.
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
printf 'release-v9.1.sh: PASS: capability validation via stdlib fallback\n'

printf 'RELEASE_V9_1_OK\n'
