"""Explicit no-op operator."""

from __future__ import annotations

from skillops_agent.operators.base_operator import BaseOperator
from skillops_agent.repository.edit_record import UpdateProposal
from skillops_agent.repository.repository import SkillRepository


class NoOpOperator(BaseOperator):
    """Leaves the repository unchanged."""

    def apply(self, proposal: UpdateProposal, repository: SkillRepository) -> None:
        return None

