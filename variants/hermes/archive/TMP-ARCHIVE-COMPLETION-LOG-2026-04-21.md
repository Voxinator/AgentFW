---
type: Mac /tmp full-archive completion log
date: 2026-04-21
purpose: preserve remaining campaign /tmp files (r7.2-7.5) + verify r7.6-7.8 coverage
---
# /tmp archive completion log

Executed by remaining-Mac-/tmp archive worker. Copied /tmp campaign files
to their per-campaign `tmp-archive/` destinations under
`variants/hermes/archive/`. Used `cp -a` semantics with per-file
existence check to preserve metadata and avoid clobbering files already
placed by the prior r7.6/7.7/7.8 archive worker.

## Per-campaign copy counts

| Campaign | /tmp source count | Copied now | Already-present (skipped) | Skipped (filter) | Total in archive |
|----------|------------------:|-----------:|--------------------------:|-----------------:|-----------------:|
| hermes-probe-r7 (side-effects) | 1    | 1   | 0   | 0 | 1     |
| r7.2-r7.3                      | 201  | 201 | 0   | 0 | 201   |
| r7.4                           | 97   | 97  | 0   | 0 | 97    |
| r7.5                           | 46   | 46  | 0   | 0 | 46    |
| r7.6                           | 96   | 3   | 93  | 0 | 97    |
| r7.7                           | 179  | 123 | 55  | 1 | 180   |
| r7.8                           | 158  | 114 | 44  | 0 | 159   |
| **Total**                      | 778  | 585 | 192 | 1 | 781   |

Notes:
- r7.2-r7.3 source breakdown: 104 r7.2 entries (11 r7.2-*, 92 probe-r7.2-*, plus `patch_toolsets_r7.3.py`) + 97 r7.3 entries (all probe-r7.3-*; zero plain r7.3-* on disk).
- r7.4 source breakdown: 1 r7.4-* + 96 probe-r7.4-*.
- r7.5 source breakdown: 1 r7.5-* + 45 probe-r7.5-*.
- r7.6 source breakdown: 3 r7.6-* + 93 probe-r7.6-* (of 96 sources, 93 were already archived by prior worker — only the 3 plain r7.6-* files were new).
- r7.7 source breakdown: 59 r7.7-* + 120 probe-r7.7-* = 179; 1 filter-skipped is `/tmp/r7.7-env.sh` per skip-list.
- r7.8 source breakdown: 48 r7.8-* + 110 probe-r7.8-*.
- Destination "Total in archive" may slightly exceed `copied + already-present` where the prior worker staged auxiliary content (e.g. r7.7 archive +2 non-/tmp-sourced entries).

## Sizes added

Post-archive `du -sh` per tmp-archive directory:

| Archive directory | Entries | Size |
|---|---:|---:|
| hermes-probe-r7-2026-04-18/tmp-archive          | 1   | 4.0K |
| hermes-probe-r7.2-r7.3-2026-04-18/tmp-archive   | 201 | 1.6M |
| r7.4-campaign/tmp-archive                       | 97  | 480K |
| r7.5-prerelease-2026-04-19/tmp-archive          | 46  | 1.2M |
| r7.6-campaign-2026-04-20/tmp-archive            | 97  | 6.8M |
| r7.7-campaign-2026-04-20/tmp-archive            | 180 | 8.8M |
| r7.8-campaign-2026-04-21/tmp-archive            | 159 | 11M  |

Aggregate: ~30 MB across 781 entries.

## Secret scan

Scans run against the full `variants/hermes/archive/` tree after copy
completion:

- `<raw-key>` (sentinel; operator knows literal): **0 matches**
- `OMLX_API_KEY=[A-Za-z0-9]{4,}` (literal-value leak pattern): **0 matches**
- Redactions applied: **none required**

## Skipped live / sensitive files

Per skip list, the following /tmp entries were explicitly not copied:

- `/tmp/hermes-live-HERMES.md` — operator's live Hermes instance log
- `/tmp/hermes-live-HERMES.err` — operator's live Hermes stderr
- `/tmp/r7.7-env.sh` — contains `OMLX_API_KEY` (secret; the prior worker
  placed a redacted copy under the r7.7 archive if needed)

Pre-existing destination files were also skipped (counted under
"Already-present" above) via per-file existence check before `cp -a`.

## /tmp originals left in place

Originals at `/tmp/r7.2-*`, `/tmp/r7.3-*`, `/tmp/r7.4-*`, `/tmp/r7.5-*`,
`/tmp/r7.6-*`, `/tmp/r7.7-*`, `/tmp/r7.8-*`, `/tmp/probe-r7.*-*`, and
`/tmp/probe-r7-side-effects` have **not** been deleted. They will clear
naturally on reboot. Operator can run `rm -rf /tmp/r7.*` /
`rm -rf /tmp/probe-r7*` when ready.

## Commit status

Per task constraints: **not committed**. Archive `tmp-archive/`
subdirectories are already covered by `.gitignore`, so these new files
do not appear in `git status`.
