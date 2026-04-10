"""Proposal conflict checks."""

from __future__ import annotations

from skillops_agent.repository.edit_record import SkillAction, UpdateProposal
from skillops_agent.repository.repository import SkillRepository


class ConflictChecker:
    """Detects simple conflicts against recent edits and proposal shape."""

    def check(self, proposal: UpdateProposal, repository: SkillRepository) -> tuple[bool, str]:
        if proposal.action == SkillAction.NOOP:
            return False, ""

        if proposal.target_skill_id is None or proposal.target_skill_id not in repository.skills:
            return True, "target skill missing"

        if proposal.action == SkillAction.GUARD and "procedure" in proposal.patch:
            return True, "guard proposal touches procedure"
        if proposal.action == SkillAction.REPAIR and "contract" in proposal.patch:
            return True, "repair proposal touches contract"

        recent = repository.edit_records[-1:] if repository.edit_records else []
        if recent:
            last = recent[0]
            if (
                last.accepted
                and last.skill_id == proposal.target_skill_id
                and last.action == proposal.action
                and last.patch == proposal.patch
            ):
                return True, "duplicate recent edit"
        return False, ""

