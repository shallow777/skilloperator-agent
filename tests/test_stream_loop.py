"""End-to-end stream loop tests."""

from __future__ import annotations

import unittest

from skillops_agent.evaluation.benchmark import run_stream


class StreamLoopTests(unittest.TestCase):
    def test_stream_runs_end_to_end(self) -> None:
        repository, metrics = run_stream()
        summary = metrics.as_dict()
        self.assertEqual(summary["total_tasks"], 5)
        self.assertEqual(summary["accepted_edit_count"], 2)
        self.assertEqual(summary["rejected_edit_count"], 0)
        self.assertEqual(summary["operator_usage_counts"]["guard"], 1)
        self.assertEqual(summary["operator_usage_counts"]["repair"], 1)
        self.assertEqual(summary["operator_usage_counts"]["noop"], 3)
        self.assertEqual(
            repository.get_skill("json_parser").contract.disallowed_task_types,
            ["csv_cleanup"],
        )
        self.assertIn(
            "normalize decimals",
            repository.get_skill("json_parser").procedure.validation_steps,
        )


if __name__ == "__main__":
    unittest.main()
