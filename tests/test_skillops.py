"""SkillOps policy tests."""

from __future__ import annotations

import unittest

from skillops_agent.agents.skillops_agent import SkillOpsAgent
from skillops_agent.agents.task_agent import TaskAgent
from skillops_agent.environments.continual_task_env import ContinualTaskEnvironment
from skillops_agent.policies.heuristic_policy import HeuristicSkillOpsPolicy
from skillops_agent.repository.edit_record import SkillAction
from skillops_agent.evaluation.benchmark import build_default_repository


class SkillOpsPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = build_default_repository()
        self.task_agent = TaskAgent()
        self.skillops_agent = SkillOpsAgent(HeuristicSkillOpsPolicy())
        self.environment = ContinualTaskEnvironment.default_stream().stream()

    def test_misuse_triggers_guard(self) -> None:
        case = self.environment[0]
        execution = self.task_agent.run_task(case.task, self.repository, case)
        decision = self.skillops_agent.decide(case.task, self.repository, execution)
        self.assertEqual(decision.proposal.action, SkillAction.GUARD)

    def test_procedure_bug_triggers_repair(self) -> None:
        case = self.environment[1]
        execution = self.task_agent.run_task(case.task, self.repository, case)
        decision = self.skillops_agent.decide(case.task, self.repository, execution)
        self.assertEqual(decision.proposal.action, SkillAction.REPAIR)

    def test_noisy_failure_triggers_noop(self) -> None:
        case = self.environment[3]
        execution = self.task_agent.run_task(case.task, self.repository, case)
        decision = self.skillops_agent.decide(case.task, self.repository, execution)
        self.assertEqual(decision.proposal.action, SkillAction.NOOP)


if __name__ == "__main__":
    unittest.main()

