# Hermes Variant — Usage Guide (r7.11)

Progressive examples of how to use the r7.11 firmware, ordered from "10-second sanity check" to "build your own task." Each level builds on the previous one. You don't need to do them in order, but if you're new to r7.11, going through Levels 0 → 3 in sequence is the fastest path to understanding what the architecture actually does.

**Prerequisite**: r7.11 installed on your VM. Run `bash variants/hermes/install.sh --check` to confirm. If unstaged, run `bash variants/hermes/install.sh` first.

**Conventions** in this doc:
- `$HERMES_HOST` — your ssh alias for the VM (default `ubuntu-vm`)
- `$HERMES_PATH` — Hermes path on VM, `$HOME`-relative (default `.hermes/hermes-agent`)
- `$OMLX_API_KEY` — your local-dev oMLX auth token (set in env)
- `$REPO` — your AgentFW repo path; substitute as needed

---

## Level 0 — Smoke test (~10 seconds)

**Demonstrates**: the staged firmware loads cleanly into Hermes; tools register without error.

```bash
OMLX_API_KEY=... bash variants/hermes/install.sh --smoke
```

**Success signal**: report at `/tmp/r7.11-smoke-report.md` shows tool dispatch worked. No `tool.*load.*error` or `cannot.*import.*tools.*r7_11_lib` in stderr.

**If it fails**: check `--check` first (firmware integrity); check `OMLX_API_KEY` is valid; check oMLX is reachable from the VM.

---

## Level 1 — Tool visibility from a Hermes session (~30 seconds)

**Demonstrates**: the four r7.11 tools (`verify_phase`, `end_session_for_handoff`, `escalate_to_operator`, `write_plan_md`) are visible to a fresh `hermes chat` invocation.

```bash
ssh $HERMES_HOST "cd ~/$HERMES_PATH && OMLX_API_KEY='$OMLX_API_KEY' \
  ./venv/bin/hermes chat -m gemma-4-26B-A4B-it-MLX-8bit -Q --max-turns 1 \
  -t hermes-cli \
  -q 'List the names of all tools you have available. Just list them, do not call them.'"
```

**Success signal**: response includes `verify_phase`, `end_session_for_handoff`, `escalate_to_operator`, `write_plan_md` (alongside the standard Hermes tools like `read_file`, `write_file`, `delegate_worker`, `todo`).

**Discord variant**: if you have a Discord bot connected to this Hermes, ask it the same question. Same success signal. **Caveat**: if the bot is a long-running process that loaded toolsets before staging, it won't see the new tools until restart.

---

## Level 2 — One-phase trial (~3-5 minutes)

**Demonstrates**: the full multi-session lifecycle on a trivial task. Bootstrap session writes PLAN.md → wrapper drives phase 1 as its own Hermes session → verifier checks the deliverable → wrapper exits SUCCESS.

### Step 2a — Build a minimal scaffold

```bash
ssh $HERMES_HOST '
SCAFFOLD=/tmp/r7.11-mini
rm -rf $SCAFFOLD && mkdir -p $SCAFFOLD/src $SCAFFOLD/tests

# Build a Python venv that matches Hermes Python (3.11.x — F-6)
PY=$(readlink -f ~/.hermes/hermes-agent/venv/bin/python)
$PY -m venv $SCAFFOLD/.venv
$SCAFFOLD/.venv/bin/pip install --quiet pytest

# Empty package init
touch $SCAFFOLD/src/__init__.py $SCAFFOLD/tests/__init__.py

# The user prompt — what the parent agent reads to plan its work
cat > $SCAFFOLD/USER-PROMPT.md <<EOF
Write a single Python function add(a, b) -> int that returns a+b.
Put it in src/calc.py. Add a pytest test in tests/test_calc.py
that proves add(2,3)==5. The test must pass.
Scaffold root: /tmp/r7.11-mini
EOF

# Verifier configuration (defaults are fine for this trial)
cat > $SCAFFOLD/verify-config.json <<EOF
{"schema_version": "1.0", "verify_phase": {}, "wrapper": {}}
EOF
echo "scaffold ready at $SCAFFOLD"
ls $SCAFFOLD
'
```

### Step 2b — Run the trial

```bash
ssh $HERMES_HOST "cd /media/psf/$REPO/variants/hermes/r7.9-research/r7.11/ && \
  OMLX_API_KEY='$OMLX_API_KEY' python3 hermes_multi.py run /tmp/r7.11-mini/ \
  --transport local" 2>&1 | tee /tmp/r7.11-mini.log
```

(Adjust the `cd` path to where the r7.11 source is mounted on your VM; on the tested rig it's `/media/psf/Projects/AgentFW/variants/hermes/r7.9-research/r7.11/`.)

### Step 2c — Verify success

**Success signal in stdout**:
```
hermes-multi: SUCCESS — all phases verified_passed
```

**Success signal in artifacts**:
```bash
ssh $HERMES_HOST 'cat /tmp/r7.11-mini/verified-state.json | python3 -m json.tool | head -40'
# Look for: "status": "verified_passed" on all phases
```

**Real-test verification**:
```bash
ssh $HERMES_HOST 'cd /tmp/r7.11-mini && .venv/bin/python -m pytest tests/'
# Look for: "1 passed"
```

### What you just exercised

- Bootstrap session: parent read `USER-PROMPT.md`, wrote `PLAN.md`, called `end_session_for_handoff`
- Wrapper polled the sentinel, killed Hermes, archived the bootstrap session
- Wrapper read `PLAN.md`, bootstrapped `verified-state.json` with the phase definitions
- Phase 1 session: parent read PLAN.md + verified-state.json, dispatched a worker child to write `calc.py` + `test_calc.py`, called `verify_phase`, called `end_session_for_handoff`
- Wrapper read `verified-state.json`, saw all phases `verified_passed`, exited SUCCESS

`/tmp/r7.11-mini/.session-archive/` contains the bootstrap + phase-1 session JSONs + stdout/stderr logs + manifest.

---

## Level 3 — Multi-phase trial with `Acceptance Command` (~10-15 minutes)

**Demonstrates**: tier 3.7 acceptance-runner — the load-bearing r7.11 component that closes the synthesis-trust gap. Parent declares `Acceptance Command:` per phase; verifier actually executes it; verdict reflects reality.

This is the same pattern as Level 2 but with an explicit `Acceptance Command:` and multiple phases. The architecture's value-prop is exercised end-to-end.

### Step 3a — Build the scaffold

```bash
ssh $HERMES_HOST '
SCAFFOLD=/tmp/r7.11-multi
rm -rf $SCAFFOLD && mkdir -p $SCAFFOLD/src $SCAFFOLD/tests

PY=$(readlink -f ~/.hermes/hermes-agent/venv/bin/python)
$PY -m venv $SCAFFOLD/.venv
$SCAFFOLD/.venv/bin/pip install --quiet pytest

touch $SCAFFOLD/src/__init__.py $SCAFFOLD/tests/__init__.py

cat > $SCAFFOLD/USER-PROMPT.md <<EOF
Implement a small string-utilities module with two phases:

Phase 1 — Core utilities
  Write src/strutil.py with:
    - reverse(s: str) -> str
    - count_vowels(s: str) -> int

Phase 2 — Tests
  Write tests/test_strutil.py with pytest tests that prove:
    - reverse("hello") == "olleh"
    - reverse("") == ""
    - count_vowels("hello") == 2
    - count_vowels("xyz") == 0
  Tests MUST pass. Acceptance Command: .venv/bin/pytest tests/test_strutil.py

Scaffold root: /tmp/r7.11-multi
EOF

cat > $SCAFFOLD/verify-config.json <<EOF
{"schema_version": "1.0", "verify_phase": {}, "wrapper": {}}
EOF
echo "multi-phase scaffold ready at $SCAFFOLD"
'
```

### Step 3b — Run the trial

```bash
ssh $HERMES_HOST "cd /media/psf/$REPO/variants/hermes/r7.9-research/r7.11/ && \
  OMLX_API_KEY='$OMLX_API_KEY' python3 hermes_multi.py run /tmp/r7.11-multi/ \
  --transport local" 2>&1 | tee /tmp/r7.11-multi.log
```

### Step 3c — Verify the synthesis-trust mechanism

**Look for tier 3.7 firing on phase 2**:
```bash
ssh $HERMES_HOST 'cat /tmp/r7.11-multi/verified-state.json | python3 -m json.tool' | grep -A1 acceptance_runner
```

Expected:
```json
"acceptance_runner_findings": [
    "[ACCEPTANCE_PASSED] acceptance command exited 0: `.venv/bin/pytest tests/test_strutil.py`"
],
```

**Confirm pytest actually passes** (the load-bearing check — verifier verdict matches reality):
```bash
ssh $HERMES_HOST 'cd /tmp/r7.11-multi && .venv/bin/pytest tests/test_strutil.py'
# Expected: "4 passed"
```

### What you just exercised

- Parent's `write_plan_md` produced PLAN.md with `Acceptance Command:` on phase 2 (the teaching mechanism worked)
- Phase 1 (utilities) verified via static checks (presence + syntax + wiring)
- Phase 2 (tests) verified via tier 3.7 — wrapper actually ran `pytest`, captured exit code, classified as `[ACCEPTANCE_PASSED]`
- Multi-session boundaries: bootstrap + 2 phases = 3 separate Hermes sessions

This is what the r7.11 architecture is for. **The verifier verdict aligns with reality** because the verifier executed the acceptance criterion, not just the static analysis.

---

## Level 4 — Reproduce the campaign baseline (~15-20 minutes)

**Demonstrates**: r7.11 against the T6 capability-curve workload that drove the n=5 RC measurement. ~60% strict completion expected (per pre-committed RC threshold; matches trials 4c/4d/5.1/5.2/5.5).

The scaffold from the campaign is preserved at `/tmp/r7.11-item8-scaffold/` on the tested rig. If it's been deleted, rebuild from `variants/hermes/r7.9-research/r7.10/scaffold-baseline/` (commit `a87d144` or later).

### Step 4a — Reset to pristine baseline

```bash
ssh $HERMES_HOST '
SCAFFOLD=/tmp/r7.11-item8-scaffold
BASELINE=/media/psf/'"$REPO"'/variants/hermes/r7.9-research/r7.10/scaffold-baseline

# Wipe trial state, restore baseline
rm -rf $SCAFFOLD/PLAN.md $SCAFFOLD/verified-state.json \
       $SCAFFOLD/.session-archive $SCAFFOLD/.session-end-signal.json \
       $SCAFFOLD/.session-escalate-signal.json $SCAFFOLD/.pytest_cache \
       $SCAFFOLD/src $SCAFFOLD/tests $SCAFFOLD/docs
rm -f  $SCAFFOLD/pyproject.toml $SCAFFOLD/README.md
cp -r  $BASELINE/src $BASELINE/tests $SCAFFOLD/
cp     $BASELINE/pyproject.toml $BASELINE/README.md $SCAFFOLD/

# Confirm preserved files unchanged
ls -la $SCAFFOLD/USER-PROMPT.md $SCAFFOLD/verify-config.json
$SCAFFOLD/.venv/bin/python --version  # should be 3.11
echo "scaffold reset to pristine"
'
```

### Step 4b — Run the trial

```bash
ssh $HERMES_HOST "cd /media/psf/$REPO/variants/hermes/r7.9-research/r7.11/ && \
  OMLX_API_KEY='$OMLX_API_KEY' python3 hermes_multi.py run /tmp/r7.11-item8-scaffold/ \
  --transport local" 2>&1 | tee /tmp/r7.11-baseline.log
```

### Step 4c — Score the result

```bash
# Wrapper outcome
tail -3 /tmp/r7.11-baseline.log

# Per-phase verdict
ssh $HERMES_HOST 'cat /tmp/r7.11-item8-scaffold/verified-state.json | python3 -m json.tool' | head -50

# Real-test reality check
ssh $HERMES_HOST 'cd /tmp/r7.11-item8-scaffold && .venv/bin/python -m pytest tests/test_export.py'

# Strict scoring (the campaign rubric — runs from the Mac)
cd $REPO/variants/hermes/r7.9-research/r7.11
ssh $HERMES_HOST "cd /media/psf/$REPO/variants/hermes/r7.9-research/r7.11 && python3 content_verify.py /tmp/r7.11-item8-scaffold/"
```

### Expected outcomes

Per n=5 baseline:
- 3/5 trials: `SUCCESS — all phases verified_passed` + tier 3.7 ACCEPTANCE_PASSED + pytest exit 0
- 2/5 trials: ESCALATE on a real, operator-actionable issue (parent-recovery exhaustion OR bootstrap-handoff ceremony)
- Wall-clock: 6-20 min per trial

If you run this multiple times, you should see roughly the same distribution. Both outcomes prove the architecture is working — SUCCESS demonstrates the lifecycle composes; ESCALATE demonstrates the verifier catches real issues without silently passing.

---

## Level 5 — Adapt to your own task

To use r7.11 for actual work, you build a scaffold for your task. The structure is small.

### Required scaffold contents

| File / Dir | Purpose | Example |
|---|---|---|
| `USER-PROMPT.md` | Task description for the parent agent | Plain-prose Markdown describing what to build, where files go, what acceptance looks like |
| `verify-config.json` | Verifier config | `{"schema_version": "1.0", "verify_phase": {}, "wrapper": {}}` (defaults are usually fine) |
| `.venv/` | Python venv matching Hermes Python (3.11.x) | Build with the same Python that backs Hermes' venv (F-6 — ABI must match) |
| `src/` | Source-code root | Initially empty (or stubs); parent fills in per-phase |
| `tests/` | Test root | Initially empty (or stubs); parent fills in per-phase |

The parent reads `USER-PROMPT.md` during the bootstrap session and writes `PLAN.md` describing the phase decomposition.

### Writing a good `USER-PROMPT.md`

The parent uses `write_plan_md` (whose tool description teaches the format) to convert your prompt into a phased PLAN.md. Help it produce a good plan by:

1. **Naming the scaffold root explicitly** in the prompt (parent uses absolute paths)
2. **Listing the required files** with intended paths
3. **Stating acceptance criteria** for each deliverable (parent will translate these into `Acceptance Criteria:` lines per phase)
4. **For test phases**: explicitly state "tests must pass" — parent then declares `Acceptance Command: .venv/bin/pytest tests/<file>` and tier 3.7 verifies execution

### Example USER-PROMPT.md template

```markdown
Implement <feature> with these phases:

Phase 1 — <name>
  Write <path/to/file.py> with:
    - <function/class signature>
    - <what it does>

Phase 2 — <name>
  ...

Phase N — Tests
  Write tests/test_<feature>.py with pytest tests that prove:
    - <specific assertion 1>
    - <specific assertion 2>
  Tests MUST pass. Acceptance Command: .venv/bin/pytest tests/test_<feature>.py

Scaffold root: /tmp/<your-scaffold>
```

### Writing a good `Acceptance Command:`

**Rules** (taught to the parent via `write_plan_md`'s description; you can declare them directly to be sure):

- Single executable invocation. **No** shell builtins (`cd`, `&&`, `||`, `;`, pipes)
- Parsed via `shlex.split` and run via `subprocess.run` with `cwd=scaffold_root` — use cwd-relative paths

GOOD:
- `.venv/bin/python -m pytest tests/test_foo.py`
- `.venv/bin/pytest tests/test_foo.py`
- `.venv/bin/python -m my_tool --check src/`

BAD:
- `cd /tmp/scaffold && pytest tests/test_foo.py` (`cd` is a shell builtin)
- `pytest tests/ | tee log.txt` (pipe requires a shell)

### Run the trial

Same pattern as Level 2/3:

```bash
ssh $HERMES_HOST "cd /media/psf/$REPO/variants/hermes/r7.9-research/r7.11/ && \
  OMLX_API_KEY='$OMLX_API_KEY' python3 hermes_multi.py run /tmp/<your-scaffold>/ \
  --transport local" 2>&1 | tee /tmp/<your-scaffold>.log
```

### When NOT to use r7.11

r7.11 is built for **decomposable, verifiable tasks** with clear acceptance criteria. It's excellent for:
- Library implementation with unit/integration tests
- API endpoints with executable test suites
- Refactors with regression-test gates
- Anything where "did the AI's code actually work?" is verifiable by a runnable command

It's a poor fit for:
- One-shot questions or single-file edits (use plain `hermes chat` directly)
- Tasks without an executable acceptance criterion (the synthesis-trust value-prop doesn't apply)
- Tasks where the operator's role IS the verification (e.g., subjective design review)

---

## Wrapper subcommands reference

The Mac-side wrapper is `hermes_multi.py` in the r7.11 source dir. It has three subcommands:

```bash
python3 hermes_multi.py run    <scaffold_root> [--fresh] [--transport local|ssh]
python3 hermes_multi.py resume <scaffold_root>
python3 hermes_multi.py status <scaffold_root>
```

| Command | Purpose |
|---|---|
| `run` | Drive the state machine through every phase from current state to completion or escalate. Use `--fresh` to re-bootstrap `verified-state.json` from PLAN.md (rare — only after manual edits). `--transport local` runs Hermes on the same host as the wrapper; default `ssh` runs Hermes on the remote VM. |
| `resume` | After an escalate-pause, clears the stale escalate sentinel and re-evaluates from current state. Use after operator-side intervention (manual fixes, verify-config tweaks, etc.). |
| `status` | Read-only diagnostic. Prints scaffold path, per-phase digest of `verified-state.json`, sentinel presence, last manifest entry. Use anytime; no side effects. |

See `r7.9-research/r7.11/HOWTO-r7.11-multi.md` for full subcommand detail + advanced flags.

---

## Wrapper exit codes

| Code | Meaning | What to do |
|---|---|---|
| `0` | SUCCESS — all phases verified_passed | Inspect deliverables; you're done |
| `2` | ESCALATE — parent called `escalate_to_operator` OR max revisions exceeded | Read `verified-state.json` corrective_dispatch; fix the issue manually; `resume` |
| `3` | Wrapper internal error | Read `wrapper.log` in `.session-archive/`; file a bug |
| `4` | Malformed scaffold or config | Verify `USER-PROMPT.md` + `verify-config.json` + scaffold structure |

Exit-code 2 ESCALATEs come with a `corrective_dispatch` field in `verified-state.json` for the failing phase — that text is operator-actionable diagnostic.

---

## Troubleshooting (usage layer)

| Symptom | Likely cause | Action |
|---|---|---|
| Wrapper exits 0 but pytest fails when run manually | Phase didn't declare `Acceptance Command:` — only static checks ran | Add `Acceptance Command:` to PLAN.md (or update USER-PROMPT.md to be explicit about pytest passing); re-run |
| Phase 1 SUCCESS but phase 2 escalates with `[CAT2:imported-unused]` | Parent left an unused import; tier-3 caught it; parent ran out of revisions | Manual fix the import; `python3 hermes_multi.py resume <scaffold>` |
| Bootstrap escalates with `bootstrap_failed_anomalous_exit` | Parent wrote PLAN.md but didn't fire `end_session_for_handoff` (n=5 trial 5.4 pattern) | Re-run; usually a one-off parent stochasticity. If persistent, check the bootstrap session JSON in `.session-archive/` |
| Acceptance command escalates with `[ENVIRONMENT:command-not-found: cd]` | PLAN.md acceptance command uses shell syntax (this should NOT happen with current write_plan_md teaching; F-11) | Check write_plan_md's tool description on VM — `grep "GOOD:" ~/.hermes/hermes-agent/tools/write_plan_md.py` should show single-executable examples |
| Acceptance command escalates with `[ENVIRONMENT:command-not-found: pytest]` | pytest not installed in scaffold venv | `<scaffold>/.venv/bin/pip install pytest` |
| Tier 3.7 says `[ACCEPTANCE_PASSED]` but manual pytest fails with `ModuleNotFoundError` | Scaffold venv Python version doesn't match Hermes Python (F-6) | Rebuild `.venv` with `~/.hermes/hermes-agent/venv/bin/python -m venv <scaffold>/.venv` |
| Hermes session ends without writing PLAN.md | Parent ran out of `--max-turns` budget | Increase via verify-config.json `wrapper.max_turns_bootstrap` (default 15) |

For deeper troubleshooting see `r7.9-research/r7.11/r7.x-followups.md`.

---

## Where to read more

- `INSTALL.md` — install + uninstall + canonical-drift handling
- `r7.9-research/r7.11/README.md` — milestone tree overview, architectural patterns vs Hermes-specific implementation
- `r7.9-research/r7.11/HANDOFF-r7.11-current.md` — campaign-close runbook with full trial-by-trial evidence
- `r7.9-research/r7.11/HOWTO-r7.11-multi.md` — wrapper subcommand reference (advanced flags)
- `r7.9-research/r7.11/HOWTO-r7.11-stage.md` — staging script internals (low-level)
- `r7.9-research/r7.11/DESIGN-r7.11-architecture.md` — original sign-off design doc (the "why")
- `r7.9-research/r7.11/r7.x-followups.md` — F-1 through F-12 with closure status (known issues)
