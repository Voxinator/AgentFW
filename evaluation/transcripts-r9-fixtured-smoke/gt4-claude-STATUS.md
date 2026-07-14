# gt4-claude — administration note

Attempt 1 (2026-07-13 22:58–23:28 UTC): turn 1 was killed by the harness timeout the
administrator set (1800 s; perl-alarm SIGALRM, runner exit 142, turn never completed, no
transcript emitted). This was an administration error — a live streaming-refactor build under the
full r9 harness needs more than 30 minutes — not a subject failure. Per the smoke run's integrity
rules (one retry permitted for a purely mechanical harness failure, noted here), the cell was
retried once with --timeout 3600. The transcript in gt4-claude.md is from the retry; no content
from attempt 1 survives (none was emitted).
