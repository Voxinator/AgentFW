---
type: session-JSON archive log
date: 2026-04-21
purpose: offline reference for 120-trial research
---
# Session JSON archive log

Pulled all parent + child session JSONs referenced from r7.6 / r7.7 / r7.8
campaign artifacts (batch-trials, judge-verdicts, vet-logs) from
`ubuntu-vm:/home/parallels/.hermes/sessions/` into each campaign's local
`tmp-archive/sessions/` directory. Method: tar-over-ssh pipe (read-only on VM).

## Per-campaign counts

| Campaign | Session IDs identified | Pulled | Missing (GCed?) | Total size |
|----------|-----------------------|--------|-----------------|------------|
| r7.6     | 81                    | 81     | 0               | 4.9M       |
| r7.7     | 121                   | 121    | 0               | 6.4M       |
| r7.8     | 141                   | 141    | 0               | 7.6M       |
| Total    | 343                   | 343    | 0               | 19M        |

All session IDs identified in artifacts were present on the VM — nothing has
been garbage-collected yet on the VM side. 100% pull success.

## Manifests

- `/tmp/r7.6-session-ids.txt` — 81 unique IDs
- `/tmp/r7.7-session-ids.txt` — 121 unique IDs
- `/tmp/r7.8-session-ids.txt` — 141 unique IDs

Parsing regex: `[0-9]{8}_[0-9]{6}_[0-9a-f]{6,8}` across `batch-trials/`,
`judge-verdicts/`, and (r7.8 only) `vet-logs/`. Deduped. All IDs are 22 chars
(YYYYMMDD_HHMMSS_6hex).

## Destinations

- `variants/hermes/archive/r7.6-campaign-2026-04-20/tmp-archive/sessions/` (81 files)
- `variants/hermes/archive/r7.7-campaign-2026-04-20/tmp-archive/sessions/` (121 files)
- `variants/hermes/archive/r7.8-campaign-2026-04-21/tmp-archive/sessions/` (141 files)

## Missing sessions (if any)

None. All 343 identified IDs existed on the VM at pull time and transferred
successfully.

## Secret scan

- `<raw-key>` (operator knows literal): 0
- `OMLX_API_KEY=<literal>`: 0

Clean. Session JSONs do not contain auth tokens as expected.

## Total disk added to variants/hermes/archive/

19M total (across all three `tmp-archive/sessions/` directories).

## Git status

`git status --porcelain | grep tmp-archive/sessions` — empty (no staged or
modified paths under `tmp-archive/sessions/`). The three `tmp-archive/`
parent directories show as untracked (`??`) — this matches the pre-existing
state (they already held probe logs, corpora, etc., and were untracked
before this pull). Per commit plan: session JSONs stay Mac-local, not
committed to repo.

## Notes

- Pre-existing 34 local session_*.json files under other tmp-archive subdirs
  (`r7.7-a2-corpus/`, `r7.8-P3a-C1-sessions/trial*/`) were unaffected. All of
  their IDs were re-pulled into the new `tmp-archive/sessions/` directories
  as part of this pass, so the new dirs are a complete, self-contained set
  per campaign.
- VM still holds ~796 session_*.json files total, of which 343 are the
  campaign trial set covered here.
