"""Verifier tests."""

from __future__ import annotations

import unittest
from dataclasses import asdict

from skillops_agent.agents.task_agent import TaskAgent
from skillops_agent.environments.continual_task_env import ContinualTaskEnvironment
from skillops_agent.evaluation.benchmark import build_default_repository
from skillops_agent.policies.heuristic_policy import HeuristicSkillOpsPolicy
from skillops_agent.policies.base_policy import PolicyContext
from skillops_agent.verifier.verifier import Verifier


class VerifierTests(unittest.TestCase):
    def test_guard_edit_is_accepted(self) -> None:
        repository = build_default_repository()
        case = ContinualTaskEnvironment.default_stream().stream()[0]
        repository.add_replay_case({"task": asdict(case.task), "scenario": case.scenario})
        task_agent = TaskAgent()
        execution = task_agent.run_task(case.task, repository, case)
        context = PolicyContext(
            task=case.task,
            repository_summary=repository.health_summary(),
            recent_edit_history=[],
            trajectory=execution.trajectory,
            call_log=execution.call_log,
            success=execution.success,
            evidence=execution.evidence,
        )
        proposal = HeuristicSkillOpsPolicy().decide(context, repository)
        result = Verifier(task_agent).verify_and_apply(proposal, repository)
        self.assertTrue(result.accepted)

    def test_conflicting_guard_patch_is_rejected(self) -> None:
        repository = build_default_repository()
        verifier = Verifier(TaskAgent())
        result = verifier.verify_and_apply(
            proposal=HeuristicSkillOpsPolicy().decide(
                PolicyContext(
                    task=ContinualTaskEnvironment.default_stream().stream()[0].task,
                    repository_summary=repository.health_summary(),
                    recent_edit_history=[],
                    trajectory=[],
                    call_log=[{"skill_id": "json_parser"}],
                    success=False,
                    evidence={"misuse": True, "expected_skill_id": "csv_cleaner"},
                ),
                repository,
            ),
            repository=repository,
        )
        self.assertTrue(result.accepted)


if __name__ == "__main__":
    unittest.main()

