"""Tests for the ingest and transform stages."""

import os
import unittest

from pipeline.ingest import load_events
from pipeline.transform import normalize_events, parse_timestamp

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "events.jsonl")


class TestIngest(unittest.TestCase):
    def test_loads_sample_data(self):
        events = load_events(DATA)
        self.assertGreater(len(events), 20)
        for field in ("timestamp", "user_id", "event_type", "value"):
            self.assertIn(field, events[0])

    def test_sample_data_is_not_presorted(self):
        """The collectors do not merge-sort their output; downstream
        stages must tolerate unsorted timestamps."""
        keys = [e["timestamp"] for e in load_events(DATA)]
        self.assertNotEqual(keys, sorted(keys))


class TestTransform(unittest.TestCase):
    def test_parse_timestamp(self):
        self.assertEqual(parse_timestamp("1970-01-01T00:01:00Z"), 60.0)

    def test_normalize_drops_bad_rows(self):
        raw = [
            {"timestamp": "2026-03-14T08:00:00Z", "user_id": "u1",
             "event_type": "Click", "value": "3.5"},
            {"timestamp": "not-a-date", "user_id": "u2",
             "event_type": "click", "value": 1},
        ]
        out = normalize_events(raw)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["event_type"], "click")
        self.assertAlmostEqual(out[0]["value"], 3.5)


if __name__ == "__main__":
    unittest.main()
