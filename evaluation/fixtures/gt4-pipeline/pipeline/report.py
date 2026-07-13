"""Report stage: render the aggregate summary as plain text."""


def render_report(summary):
    """Render {user_id: stats} into a fixed-width text report."""
    lines = []
    lines.append("User Activity Report")
    lines.append("=" * 62)
    header = "{:<10} {:>9} {:>8} {:>12} {:>16}".format(
        "user", "sessions", "events", "total_value", "avg_session_s")
    lines.append(header)
    lines.append("-" * 62)
    for user_id, stats in summary.items():
        lines.append("{:<10} {:>9} {:>8} {:>12.2f} {:>16.1f}".format(
            user_id,
            stats["session_count"],
            stats["total_events"],
            stats["total_value"],
            stats["avg_session_seconds"],
        ))
    lines.append("-" * 62)
    lines.append("users: {}  sessions: {}  events: {}".format(
        len(summary),
        sum(s["session_count"] for s in summary.values()),
        sum(s["total_events"] for s in summary.values()),
    ))
    return "\n".join(lines)
