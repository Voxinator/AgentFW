"""End-to-end test: full pipeline over the sample data.

Verifies that aggregate results are independent of the on-disk event
order by comparing against a run over globally pre-sorted input.
"""

import os
import unittest

from pipeline.ingest import load_events
from pipeline.transform import normalize_events
from pipeline.aggregate import sessionize, summarize
from pipeline.report import render_report

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "events.jsonl")


class TestEndToEnd(unittest.TestCase):
    def test_order_independence_on_sample_data(self):
        """Running on the raw (unsorted) file must equal running on a
        globally sorted copy of the same events."""
        events = normalize_events(load_events(DATA))
        pre_sorted = sorted(events, key=lambda e: e["ts"])
        self.assertEqual(summarize(sessionize(events)),
                         summarize(sessionize(pre_sorted)))

    def test_report_renders(self):
        events = normalize_events(load_events(DATA))
        report = render_report(summarize(sessionize(events)))
        self.assertIn("User Activity Report", report)
        self.assertIn("alice", report)


if __name__ == "__main__":
    unittest.main()
