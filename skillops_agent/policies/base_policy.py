"""SkillOps policy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from skillops_agent.environments.base_env import Task
from skillops_agent.repository.edit_record import EditRecord, UpdateProposal
from skillops_agent.repository.repository import SkillRepository


@dataclass(slots=True)
class PolicyContext:
    """Observable context for repository maintenance decisions."""

    task: Task
    repository_summary: dict[str, Any]
    recent_edit_history: list[EditRecord]
    trajectory: list[str]
    call_log: list[dict[str, Any]]
    success: bool
    evidence: dict[str, Any]


class SkillOpsPolicy(ABC):
    """Base policy that maps execution evidence to a typed proposal."""

    @abstractmethod
    def decide(self, context: PolicyContext, repository: SkillRepository) -> UpdateProposal:
        """Choose Guard, Repair, or No-Op."""

