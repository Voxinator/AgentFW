"""Tests for the aggregate stage (sessionization)."""

import unittest

from pipeline.aggregate import sessionize, summarize

MIN = 60.0


def ev(user, minute, value=1.0):
    return {"ts": minute * MIN, "timestamp": "t", "user_id": user,
            "event_type": "click", "value": value}


class TestSessionizeSorted(unittest.TestCase):
    def test_single_session_within_gap(self):
        events = [ev("alice", 0), ev("alice", 10), ev("alice", 25)]
        sessions = sessionize(events)["alice"]
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["event_count"], 3)

    def test_gap_splits_sessions(self):
        events = [ev("alice", 0), ev("alice", 5), ev("alice", 60), ev("alice", 65)]
        sessions = sessionize(events)["alice"]
        self.assertEqual(len(sessions), 2)


class TestSessionizeUnsorted(unittest.TestCase):
    """Sessionization must be correct on UNSORTED input.

    Event files are merged from multiple collectors and arrive in
    arbitrary timestamp order; the aggregate stage may not assume the
    input is chronologically sorted.
    """

    def test_unsorted_input_same_result_as_sorted(self):
        """Shuffled event order must yield exactly the sorted-order result."""
        sorted_events = [ev("bob", 0), ev("bob", 5), ev("bob", 60), ev("bob", 65)]
        shuffled = [sorted_events[2], sorted_events[0],
                    sorted_events[3], sorted_events[1]]
        self.assertEqual(sessionize(shuffled), sessionize(sorted_events))

    def test_unsorted_input_correct_session_count(self):
        """Regression guard: an implementation that walks events in file
        order (assuming they are already timestamp-sorted) sees the
        shuffled minutes [60, 0, 65, 5] as four >30min jumps and reports
        4 sessions. The correct answer for this data is 2."""
        shuffled = [ev("carol", 60), ev("carol", 0), ev("carol", 65), ev("carol", 5)]
        sessions = sessionize(shuffled)["carol"]
        self.assertEqual(len(sessions), 2)
        self.assertNotEqual(len(sessions), 4,
                            "sorted-input assumption regression detected")
        self.assertEqual([s["event_count"] for s in sessions], [2, 2])
        self.assertEqual(sessions[0]["start"], 0 * MIN)
        self.assertEqual(sessions[1]["start"], 60 * MIN)

    def test_unsorted_interleaved_users(self):
        events = [ev("a", 90), ev("b", 0), ev("a", 0), ev("b", 95), ev("a", 92)]
        result = sessionize(events)
        self.assertEqual(len(result["a"]), 2)
        self.assertEqual(len(result["b"]), 2)


class TestSummarize(unittest.TestCase):
    def test_summary_totals(self):
        events = [ev("dana", 0, 2.0), ev("dana", 5, 3.0), ev("dana", 90, 4.0)]
        summary = summarize(sessionize(events))["dana"]
        self.assertEqual(summary["session_count"], 2)
        self.assertEqual(summary["total_events"], 3)
        self.assertAlmostEqual(summary["total_value"], 9.0)


if __name__ == "__main__":
    unittest.main()
