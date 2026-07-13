"""Transform stage: normalize raw event records.

Batch-style: takes the full list of raw events and returns a new full
list of normalized events.
"""

from datetime import datetime, timezone


def parse_timestamp(ts):
    """Parse an ISO-8601 timestamp string into epoch seconds (UTC)."""
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    return dt.replace(tzinfo=timezone.utc).timestamp()


def normalize_events(raw_events):
    """Normalize a list of raw events.

    - parses `timestamp` into epoch seconds under the key `ts`
    - coerces `value` to float
    - lower-cases `event_type`
    Records that fail normalization are dropped.
    """
    normalized = []
    for record in raw_events:
        try:
            normalized.append({
                "ts": parse_timestamp(record["timestamp"]),
                "timestamp": record["timestamp"],
                "user_id": str(record["user_id"]),
                "event_type": str(record["event_type"]).lower(),
                "value": float(record["value"]),
            })
        except (KeyError, TypeError, ValueError):
            continue
    return normalized
