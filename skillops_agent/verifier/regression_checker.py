"""Replay-based regression checks."""

from __future__ import annotations

from skillops_agent.agents.task_agent import TaskAgent
from skillops_agent.environments.base_env import Task
from skillops_agent.environments.continual_task_env import SyntheticTaskCase
from skillops_agent.repository.repository import SkillRepository


class RegressionChecker:
    """Runs a small replay set after a tentative edit."""

    def __init__(self, task_agent: TaskAgent) -> None:
        self.task_agent = task_agent

    def check(self, repository: SkillRepository, replay_limit: int = 3) -> tuple[bool, list[str]]:
        regressions: list[str] = []
        for replay_case in repository.get_replay_cases(limit=replay_limit):
            case = SyntheticTaskCase(
                task=Task(**replay_case["task"]),
                scenario=replay_case["scenario"],
            )
            execution = self.task_agent.run_task(case.task, repository, case)
            if not execution.success:
                regressions.append(case.task.id)
        return (len(regressions) > 0, regressions)
