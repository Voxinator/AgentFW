"""Aggregate stage: per-user sessionization.

A *session* is a maximal run of a user's events in which consecutive
events (in chronological order) are separated by no more than
SESSION_GAP_SECONDS. Event files come from multiple collectors, so the
input is NOT guaranteed to be sorted by timestamp; this stage must not
depend on input order. It groups events by user and sorts each user's
events chronologically before walking the gaps.

Batch-style: consumes the full normalized event list in memory.
"""

from collections import defaultdict

SESSION_GAP_SECONDS = 30 * 60  # 30 minutes


def sessionize(events, gap_seconds=SESSION_GAP_SECONDS):
    """Group events into sessions per user.

    Returns {user_id: [session, ...]} where each session is a dict with
    start, end, event_count and total_value. Correct for arbitrarily
    ordered input: each user's events are sorted by `ts` first.
    """
    by_user = defaultdict(list)
    for event in events:
        by_user[event["user_id"]].append(event)

    sessions_by_user = {}
    for user_id, user_events in by_user.items():
        user_events.sort(key=lambda e: e["ts"])  # order-independence lives here
        sessions = []
        current = None
        for event in user_events:
            if current is None or event["ts"] - current["end"] > gap_seconds:
                current = {
                    "start": event["ts"],
                    "end": event["ts"],
                    "event_count": 0,
                    "total_value": 0.0,
                }
                sessions.append(current)
            current["end"] = event["ts"]
            current["event_count"] += 1
            current["total_value"] += event["value"]
        sessions_by_user[user_id] = sessions
    return sessions_by_user


def summarize(sessions_by_user):
    """Reduce per-user sessions to summary stats."""
    summary = {}
    for user_id, sessions in sorted(sessions_by_user.items()):
        durations = [s["end"] - s["start"] for s in sessions]
        summary[user_id] = {
            "session_count": len(sessions),
            "total_events": sum(s["event_count"] for s in sessions),
            "total_value": round(sum(s["total_value"] for s in sessions), 2),
            "avg_session_seconds": round(sum(durations) / len(sessions), 1)
            if sessions else 0.0,
        }
    return summary
