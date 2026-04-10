"""Base environment schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from skillops_agent.repository.skill import Skill


@dataclass(slots=True)
class Task:
    """Single task from the continual stream."""

    id: str
    task_type: str
    payload: dict[str, Any]
    expected_skill_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EnvironmentOutcome:
    """Environment response for a skill invocation."""

    success: bool
    output: Any
    trace: list[str]
    evidence: dict[str, Any]


class TaskResult(Protocol):
    """Interface required by the TaskAgent."""

    def evaluate(self, skill: Skill) -> EnvironmentOutcome:
        """Evaluate one task-skill pairing."""

