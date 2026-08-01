# AgentFW v9.5.0 — the witness-pair release

**Released 2026-07-31.** One field incident, one structural fix. In the drydock failure-routing
workstream, an acceptance command that was IMPOSSIBLE to pass — one leg required six files
changed, a later leg aborted unless they were unchanged — survived Layer 1, both Layer-2 judges'
first look, and three producer rounds, burning the entire two-pass Layer-2 cap before being
caught. It survived because the framework's calibration only proves acceptance commands can
FAIL (the schema-1.3 red-path duty), and an impossible command fails on *everything* — it aces
every red probe while being incapable of ever going green. **The gate structurally rewarded
impossible tests.** v9.5.0 closes that hole with two rules and one schema bump. The six-item
safety floor and the red-path duty are untouched throughout. Field evidence:
`drydock/.agentfw/evidence/failure-routing/receipt-authority-redesign-2026-07-31/round-3/layer2-pass2/VERDICTS-SUMMARY.md`.

## Rule 1 — the witness pair (schema 1.6, the new schema of record)

Before Layer-2 dispatch, every `acceptance_command` at A2+ carries TWO recorded end-to-end runs:

- **red** — on a deliberately broken or bare scratch, exiting non-zero (the existing schema-1.3
  duty, unchanged — the pair is red AND green, never green instead);
- **green** — on a **witness tree**: a planner-authored minimal tree (stubs allowed) that
  satisfies the contract, labeled `witness-tree` in its evidence record. The green witness
  claims exactly one thing — *this command CAN pass* — and is never evidence that work was
  done. At verification time the green run still happens on the REAL tree.

No green witness ⇒ the plan is rejected at plan time. A witness tree that an EMPTY
implementation would also satisfy is void — enforced mechanically by the red witness on the
bare scratch, and semantically by a new C2 duty (below).

The plan block carries a machine-checkable summary per contract:

```jsonc
"witness_pair": {
  "red":   {"tree": "bare scratch: deliverable stubbed to nothing",
            "command_sha256": "<sha256 of the contract's exact acceptance_command>",
            "exit_code": 1, "evidence_path": ".agentfw/evidence/<plan>/witness/T1-red.txt"},
  "green": {"tree": "witness-tree: minimal stub satisfying the contract",
            "command_sha256": "<same digest — same whole command>",
            "exit_code": 0, "evidence_path": ".agentfw/evidence/<plan>/witness/T1-green.txt"}
}
```

## Rule 2 — whole-command-only evidence

A witness (red or green) counts only as ONE recorded end-to-end invocation of the ENTIRE
command string from the contract, matched to the contract by `command_sha256`. Running one leg
of a multi-leg command and reporting the whole command is inadmissible — and mechanically
impossible to launder, because a record produced from a partial or drifted command cannot carry
the contract's digest. (The round-3 producer had only ever run the last leg; that is how the
contradiction survived three rounds.)

## Layer-1 enforcement (`tools/validate-plan`)

New stable defect keyword **`witness`**. Mechanically checked for every 1.6 contract at A2+
(optional below A2, fully checked when present):

- `witness_pair` present, exactly `{red, green}`, each leg exactly
  `{tree, command_sha256, exit_code, evidence_path}` — `exit_code` a JSON integer (a boolean
  `true` is rejected, dodging the bool-is-int coercion trap);
- BOTH legs' `command_sha256` equal the sha256 of the contract's exact `acceptance_command`
  string (case-insensitive hex);
- `red.exit_code != 0` and `green.exit_code == 0` — an honest record of an impossible command
  cannot put 0 on its green leg, so **the impossible command is rejected at plan time**.

Layer 1 does NOT judge witness-tree honesty (a C2 duty) and does not stat `evidence_path`
(hermetic single-file checker). Pre-1.6 schemas carrying `witness_pair` are rejected naming
schema 1.6. Six new fixtures, including `plan-bad-16-round3-contradiction.md` — the permanent
regression model of the field incident — and `plan-bad-16-digest-mismatch.md`, the leg-skipping
forgery red path.

## C2 upgrade — SHOULD becomes MUST, the hatch becomes scoped

The plan critic MUST re-execute both witness legs itself — red on a scratch it breaks itself,
green on the plan's witness tree — and MUST reject a green witness whose tree still passes with
the deliverables stubbed to nothing. The old "wherever feasible" escape hatch is **scoped, not
removed**: genuinely infeasible re-execution is tagged `reasoned` with the infeasibility
stated, using the existing demonstrated/reasoned machinery — a silent skip is a policy
violation; a named infeasibility is not. The temporal split ("at plan time the command is read
as a spec — it need not run green on a greenfield tree") is replaced by the witness-pair duty:
the *greenfield* waiver survives, the *green-evidence* waiver does not. Both judge prompts
(`agentfw-plan-critic`, `agentfw-verifier`) carry the new duties.

## Drift fix

`policy/acceptance-contract.md` had no schema-1.5 section and still named 1.4 the schema of
record, while `policy/plan-critique.md` and `tools/validate-plan` had shipped 1.5 in v9.4.0.
The section now exists and the versioning header matches the validator (which was always the
authority).

## Compatibility

Schemas 1.1–1.5 remain valid; **pre-1.6 plans validate byte-identically** — proven by 144
old-vs-new validator invocations over every shipped fixture and both adapter SKILL examples in
all three flag modes, plus two legacy drydock A3 plans. The sole output difference is the
precedented moving pointer in the legacy-`"1"` diagnostic ("migrate to \"1.6\"" — it moved
1.3→1.4→1.5 at each prior bump). Raw evidence:
[evaluation/evidence/witness-pair-upgrade-2026-07-31/](evaluation/evidence/witness-pair-upgrade-2026-07-31/).

## Verification

- Deterministic release gate: [tools/tests/release-v9.5.sh](tools/tests/release-v9.5.sh) —
  release identity, witness policy text on every surface, the six 1.6 fixtures, the `--digest`
  count oracle on the 1.5 AND 1.6 fixtures, plus every prior suite (validator harness,
  installer roundtrip 28/28, link resolution, capability validation both parser paths, adapter
  SKILL sync, sleep-posture and liveness invariants, candidate-ledger completeness).
- Independent verification: an input-curated `agentfw-verifier` re-executed the full harness
  from disk state, re-derived the 144-invocation byte-identical regression itself, ran its own
  digest-forgery mutation (one character changed in a command → both legs go red), and probed
  seven off-contract cases (uppercase digests, boolean exit codes, extra keys, below-A2
  behavior, flag-mode bypass). Verdict: VERIFIED, zero defects above informational.
- **Behavioral evidence boundary:** no behavioral-evaluation round was run for v9.5.0; the
  deterministic gate and the recorded witness evidence are the release's evidence. The witness
  pair discipline was applied to its own upgrade — the release ships with its own green witness
  (a valid 1.6 plan passing) and four red witnesses (missing green, the round-3 contradiction,
  digest forgery, shape defects) recorded with raw machine output.
