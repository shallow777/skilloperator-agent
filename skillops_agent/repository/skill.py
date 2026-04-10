"""Structured skill representation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class SkillContract:
    """Applicability layer for a skill."""

    allowed_task_types: list[str]
    disallowed_task_types: list[str] = field(default_factory=list)
    routing_notes: list[str] = field(default_factory=list)
    abstain_conditions: list[str] = field(default_factory=list)
    required_inputs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SkillProcedure:
    """Execution layer for a skill."""

    steps: list[str]
    validation_steps: list[str] = field(default_factory=list)
    known_limitations: list[str] = field(default_factory=list)


@dataclass(slots=True)
class UsageStats:
    """Lightweight skill usage counters."""

    total_calls: int = 0
    successes: int = 0
    failures: int = 0
    misuse_events: int = 0
    local_defects: int = 0


@dataclass(slots=True)
class Skill:
    """Skill state stored in the repository."""

    id: str
    name: str
    description: str
    contract: SkillContract
    procedure: SkillProcedure
    examples: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    usage_stats: UsageStats = field(default_factory=UsageStats)
    edit_history: list[str] = field(default_factory=list)
    status: str = "active"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the skill into plain Python types."""
        return asdict(self)

