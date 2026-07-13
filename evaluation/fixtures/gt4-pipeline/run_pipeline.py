#!/usr/bin/env python3
"""Run the full batch pipeline: ingest -> transform -> aggregate -> report."""

import os
import sys

from pipeline.ingest import load_events
from pipeline.transform import normalize_events
from pipeline.aggregate import sessionize, summarize
from pipeline.report import render_report

DEFAULT_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "data", "events.jsonl")


def main(argv):
    path = argv[1] if len(argv) > 1 else DEFAULT_DATA
    raw = load_events(path)
    events = normalize_events(raw)
    sessions = sessionize(events)
    summary = summarize(sessions)
    print(render_report(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
