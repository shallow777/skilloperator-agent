"""Contract-only repository updates."""

from __future__ import annotations

from skillops_agent.operators.base_operator import BaseOperator
from skillops_agent.repository.edit_record import UpdateProposal
from skillops_agent.repository.repository import SkillRepository


class GuardOperator(BaseOperator):
    """Applies only contract-level patches."""

    def apply(self, proposal: UpdateProposal, repository: SkillRepository) -> None:
        if proposal.target_skill_id is None:
            raise ValueError("Guard proposal requires a target skill")
        repository.update_contract(proposal.target_skill_id, proposal.patch["contract"])

