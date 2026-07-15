# AgentFW v9.1.0 release notes

Released 2026-07-15. v9.1.0 is a backward-compatible minor release that strengthens how AgentFW
proves acceptance commands can detect defects. It does not add an adapter or break schema 1.1/1.2
plans. Project metadata identifies the release as version `9.1.0`, revision `r9.1`.

## What changed

The six completed improvements are tracked with their original scenarios and root causes in
[R9X-CANDIDATES.md](R9X-CANDIDATES.md).

1. **C-1 — producer red-path self-probes and weak-command lint.** Before Layer-2 review, a
   contract producer runs each acceptance command against at least one deliberately broken case.
   The schema 1.3 validator also rejects known weak command shapes: a pipe before a gating `&&`,
   an unguarded success signal, and a success signal that is not terminal.
2. **C-2 — schema 1.3 mutation probes.** Acceptance contracts can declare exact
   `mutation_probes` entries with `{mutation, expected: "red"}`. Schema 1.3 requires at least one
   for every integration seam and every A3/A4 contract. The verifier executes each probe
   independently on a fresh scratch copy; unchanged authoritative state is part of the duty.
   Schema 1.3 is additive, and historical schema 1.1/1.2 behavior remains supported.
3. **C-3 — fixture leak-channel guidance.** [Fixture hygiene](references/fixture-hygiene.md)
   now treats names, file contents, comments, committed tooling, commit messages, refs, and reflogs
   as contamination channels. It keeps validation tooling outside the evaluated artifact and
   derives guard patterns and worker bans from one source.
4. **C-4 — empirical plan critics.** C2 reviewers execute minimal hostile probes when feasible
   and label findings as `demonstrated` with live output or `reasoned` when they cannot execute.
5. **C-5 — standard cap-with-open-blocker choices.** The recovery policy now names three paths:
   one bounded extra pass under stated conditions, mutation-gated dispatch only for C2-local
   blockers with contracted mechanical compensation, or halt. Anything else is a named bespoke
   relaxation.
6. **C-6 — command-resolution preflight.** Claude Code's status evidence records `command -v` and
   `type` resolution for `grep`, `sed`, `find`, `md5`, and `sqlite3`, including wrapper/function
   and missing-command states.

The policy and validator details live in [acceptance-contract.md](policy/acceptance-contract.md),
[plan-critique.md](policy/plan-critique.md), [recovery.md](policy/recovery.md), and
[validate-plan](tools/validate-plan).

## Release evidence

The deterministic release gate is [tools/tests/release-v9.1.sh](tools/tests/release-v9.1.sh).
It checks current release identity, adopter-facing roadmap wording, all six candidate statuses,
and provenance presence before running:

- the complete validator fixture harness, including schema 1.3 positive and hostile cases;
- the installer roundtrip suite, 28/28;
- the relative-link checker; and
- both capability-validator parser paths: PyYAML and the stdlib line-based fallback.

The two contracted scratch mutations also ran: reverting scratch metadata to `9.0.0` and restoring
the old scratch README reservation of the deferred adapter for r9.1 each made the gate exit
nonzero. The unchanged acceptance run's raw stdout/stderr and exit status are recorded in
[evidence/release-v9.1.log](evidence/release-v9.1.log).

## Behavioral-evidence boundary

No golden task, Bonksnake prompt, or additional behavioral-evaluation round was run for v9.1.0.
The bounded n=1 behavioral record published with v9.0.0 remains the behavioral evidence; this
release adds deterministic contract, fixture, and installer evidence only.

[PLAN-bonksnake-fixture.md](PLAN-bonksnake-fixture.md) and
[PROMPTS-v9-paces.md](PROMPTS-v9-paces.md) are provenance only. The Bonksnake plan was halted at
its plan gate, no workers were dispatched, the target was not built, and the prompt battery was
not executed for this release.

## Roadmap

The ChatGPT Work adapter remains deferred under the Adapter Sprawl rule. It is now a v9.2
candidate; v9.1.0 continues to ship the Claude Code and Codex native adapters plus the standard
ChatGPT/Projects and Claude.ai Projects guided profiles.
