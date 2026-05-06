# skill-validation-harness — r7.11 → skill empirical campaign

Validates whether `r7-11-orchestrate` (the SKILL) holds the same RC threshold
that `hermes_multi.py` (the SUBPROCESS) cleared at r7.11 item 9.

## Pre-committed thresholds (matches r7.11 item-9 rubric)

- **Strict completion** — `verify-config.json` acceptance command exits 0,
  AND content_verify.py emits zero HIGH findings under consolidation rules.
- **Charitable completion** — strict criteria, OR HIGH findings only on
  files whose tier-3.7 acceptance test exercises them.
- **RC threshold** — n=5, ≥3/5 strict.

## Consolidation rules (mirroring r7.11 item-8 / item-9)

- `UNWIRED_API` + `UNWIRED_INLINE` on the same file → single HIGH finding.
- ≥2 `TEST_STUB` findings → consolidated single finding.
- All consolidation done by `bin/score.sh` calling content_verify.py with
  the campaign's flags. **Do not re-implement scoring.** The script is the
  rubric.

## Layout

```
skill-validation-harness/
├── README.md
├── bin/
│   ├── reset.sh            wipe + re-extract scaffold + fresh py3.11 .venv
│   ├── run-trial.sh        drive Hermes session, archive trajectory + state
│   ├── score.sh            invoke content_verify.py with consolidation rules
│   └── adherence.py        Track C scorer (per-trajectory)
├── manifest-template.json  campaign metadata baked into each trial archive
├── track-b-scaffolds/
│   ├── 2a-content-type/    semantic-break: /api/export.json → text/csv
│   └── 2b-bootstrap-child/ subprocess-authored PLAN, then skill from PLAN onward
├── track-c/                aggregate adherence outputs
└── archives/
    └── trial-N/
        ├── scaffold.tar
        ├── session-archive/
        ├── verified-state.json
        ├── manifest.json
        └── tui.log
```

## Launch method (Brian's call: OPTION A — TUI piped)

`bin/launch-tui.py` drives `hermes chat --tui -s r7-11-orchestrate` under a
stdlib pty. Operator's deployment path is the TUI, so the campaign tests
against the TUI. In-process AIAgent is fallback only if TUI control
sequences make capture intractable.

## Halt-and-flag policy (Brian's call)

**Trial 1** always halts for operator review. Surface regardless of outcome:
- Verifier verdict (`score.json`)
- Adherence scorecard (`adherence.json`)
- Wallclock per phase (extractable from `verified-state.json` timestamps)
- Anomalies: harness errors, unexpected tool calls, workflow deviations

Operator decides: continue 2-5, halt for investigation, or modify harness
and re-run trial 1.

**Trials 2-5** halt-on-anomaly when any of:
- Score script crashes (harness bug)
- Trial wallclock > 2× median of prior trials (degeneracy)
- Verifier errors instead of returning verdict (tier malfunction)
- Adherence scorer reports unclassifiable behavior

Pass `--prior-medians PATH` to trials 2-5; the JSON file should contain
`{"median_wallclock_seconds": N}` aggregated from prior trials.

## Wallclock timeout (Brian's call)

90 minutes default for trial 1 (T6 × 3 phases × up-to-3 revisions ×
5-7min/dispatch + verify_phase + orchestrator deliberation). If trial 1
lands well under, drop to 75 for trials 2-5. If trial 1 hits 90 and times
out, that's a finding (skill is slower than the subprocess wrapper).

Override per trial via `--timeout SECONDS`.

## Open inputs (waiting on Brian)

- `REPORT-r7.11-item9-n5.md` — for report-shape mirroring (`REPORT-TEMPLATE.md`
  is a reasonable inferred structure; will adjust when actual lands).
- Sanitized `content_verify.py` — current local copy at
  `r7.11/content_verify.py` is functional; will swap when received.
- `USER-PROMPT.md` for the item-9 T6 capability-curve task — needed for
  Track A trials (the prompt the orchestrator-skill receives).

Until inputs land, harness builds with sane defaults; Track A burn does
not start. Use `--dry-run` to validate the pipeline without LLM calls.
