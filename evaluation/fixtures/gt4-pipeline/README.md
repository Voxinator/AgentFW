# Event Analytics Pipeline

A small batch pipeline that turns raw user event logs into a per-user
activity report. Pure Python 3 standard library — no dependencies.

## Stages

1. **Ingest** (`pipeline/ingest.py`) — reads `data/events.jsonl`
   (JSON lines) into memory, skipping malformed records.
2. **Transform** (`pipeline/transform.py`) — normalizes records:
   parses ISO-8601 timestamps to epoch seconds, coerces values.
3. **Aggregate** (`pipeline/aggregate.py`) — groups each user's events
   into sessions (a new session starts after a 30-minute gap of
   inactivity) and computes per-user stats.
4. **Report** (`pipeline/report.py`) — renders a fixed-width text report.

Note: event files are concatenated from multiple edge collectors, so
rows are **not** globally sorted by timestamp. The aggregate stage
sorts each user's events before sessionizing; results must never
depend on file order.

## Usage

```sh
python3 run_pipeline.py            # uses data/events.jsonl
python3 run_pipeline.py other.jsonl
```

## Tests

```sh
./run-tests.sh
```
