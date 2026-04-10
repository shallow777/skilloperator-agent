"""Task agent that executes tasks with repository skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from skillops_agent.environments.base_env import Task, TaskResult
from skillops_agent.repository.repository import SkillRepository
from skillops_agent.repository.skill import Skill


@dataclass(slots=True)
class TaskExecution:
    """Observable TaskAgent output for SkillOps decisions."""

    output: Any
    trajectory: list[str]
    call_log: list[dict[str, Any]]
    success: bool
    evidence: dict[str, Any] = field(default_factory=dict)


class TaskAgent:
    """Simple task agent that routes to a repository skill and executes it."""

    def select_skill(self, task: Task, repository: SkillRepository) -> Skill:
        candidates = repository.list_skills()
        matching = [
            skill
            for skill in candidates
            if task.task_type in skill.contract.allowed_task_types
            and task.task_type not in skill.contract.disallowed_task_types
        ]
        if matching:
            return matching[0]
        return candidates[0]

    def run_task(self, task: Task, repository: SkillRepository, env: TaskResult) -> TaskExecution:
        skill = self.select_skill(task, repository)
        skill.usage_stats.total_calls += 1
        outcome = env.evaluate(skill)
        call_log = [
            {
                "skill_id": skill.id,
                "skill_name": skill.name,
                "task_id": task.id,
                "task_type": task.task_type,
            }
        ]
        trajectory = [f"selected:{skill.id}", *outcome.trace]
        if outcome.success:
            skill.usage_stats.successes += 1
        else:
            skill.usage_stats.failures += 1
            if outcome.evidence.get("misuse"):
                skill.usage_stats.misuse_events += 1
            if outcome.evidence.get("local_defect"):
                skill.usage_stats.local_defects += 1
        return TaskExecution(
            output=outcome.output,
            trajectory=trajectory,
            call_log=call_log,
            success=outcome.success,
            evidence=outcome.evidence,
        )

