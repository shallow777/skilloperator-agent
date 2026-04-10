"""Repository tests."""

from __future__ import annotations

import unittest

from skillops_agent.evaluation.benchmark import build_default_repository


class RepositoryTests(unittest.TestCase):
    def test_snapshot_and_rollback_restore_contract(self) -> None:
        repository = build_default_repository()
        snapshot_id = repository.snapshot()
        repository.update_contract("json_parser", {"disallowed_task_types": ["csv_cleanup"]})
        repository.rollback(snapshot_id)
        self.assertEqual(
            repository.get_skill("json_parser").contract.disallowed_task_types,
            [],
        )

    def test_health_summary_exposes_repository_size(self) -> None:
        repository = build_default_repository()
        summary = repository.health_summary()
        self.assertEqual(summary["repository_size"], 3)


if __name__ == "__main__":
    unittest.main()

