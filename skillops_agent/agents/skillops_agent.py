"""SkillOps agent orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from skillops_agent.agents.task_agent import TaskExecution
from skillops_agent.environments.base_env import Task
from skillops_agent.policies.base_policy import PolicyContext, SkillOpsPolicy
from skillops_agent.repository.edit_record import UpdateProposal
from skillops_agent.repository.repository import SkillRepository


@dataclass(slots=True)
class SkillOpsDecision:
    """Final policy output returned to the outer loop."""

    proposal: UpdateProposal


class SkillOpsAgent:
    """Delegates repository maintenance decisions to a pluggable policy."""

    def __init__(self, policy: SkillOpsPolicy) -> None:
        self.policy = policy

    def decide(
        self,
        task: Task,
        repository: SkillRepository,
        execution: TaskExecution,
    ) -> SkillOpsDecision:
        context = PolicyContext(
            task=task,
            repository_summary=repository.health_summary(),
            recent_edit_history=repository.edit_records[-5:],
            trajectory=execution.trajectory,
            call_log=execution.call_log,
            success=execution.success,
            evidence=execution.evidence,
        )
        return SkillOpsDecision(proposal=self.policy.decide(context, repository))

