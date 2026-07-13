"""Ingest stage: read raw event records from a JSON-lines file.

Batch-style: reads the whole file into memory and returns a list.
"""

import json

REQUIRED_FIELDS = ("timestamp", "user_id", "event_type", "value")


def load_events(path):
    """Load all events from a .jsonl file into a list of dicts.

    Lines that are blank or not valid JSON objects with the required
    fields are skipped.
    """
    events = []
    with open(path, "r", encoding="utf-8") as fh:
        raw_lines = fh.readlines()  # whole file in memory
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        if any(field not in record for field in REQUIRED_FIELDS):
            continue
        events.append(record)
    return events
