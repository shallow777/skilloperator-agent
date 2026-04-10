"""Repository edit records and proposals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now_iso() -> str:
    """Return a stable UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


class SkillAction(str, Enum):
    """Supported repository maintenance actions."""

    GUARD = "guard"
    REPAIR = "repair"
    NOOP = "noop"


@dataclass(slots=True)
class EditRecord:
    """Immutable record for an accepted or rejected repository edit."""

    action: SkillAction
    skill_id: str | None
    rationale: str
    patch: dict[str, Any]
    accepted: bool
    reason: str
    timestamp: str = field(default_factory=utc_now_iso)
    confidence: float | None = None


@dataclass(slots=True)
class UpdateProposal:
    """Structured maintenance proposal emitted by the SkillOps agent."""

    action: SkillAction
    target_skill_id: str | None
    rationale: str
    patch: dict[str, Any]
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

