"""Base operator interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from skillops_agent.repository.edit_record import UpdateProposal
from skillops_agent.repository.repository import SkillRepository


class BaseOperator(ABC):
    """Applies a typed maintenance proposal to the repository."""

    @abstractmethod
    def apply(self, proposal: UpdateProposal, repository: SkillRepository) -> None:
        """Apply a proposal in-place."""

