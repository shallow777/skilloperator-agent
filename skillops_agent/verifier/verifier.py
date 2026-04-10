"""Programmatic proposal verification."""

from __future__ import annotations

from dataclasses import dataclass

from skillops_agent.agents.task_agent import TaskAgent
from skillops_agent.operators.guard_operator import GuardOperator
from skillops_agent.operators.noop_operator import NoOpOperator
from skillops_agent.operators.repair_operator import RepairOperator
from skillops_agent.repository.edit_record import SkillAction, UpdateProposal
from skillops_agent.repository.repository import SkillRepository
from skillops_agent.verifier.conflict_checker import ConflictChecker
from skillops_agent.verifier.regression_checker import RegressionChecker


@dataclass(slots=True)
class VerificationResult:
    """Verifier output."""

    accepted: bool
    reason: str
    regression_cases: list[str]
    conflict: bool = False


class Verifier:
    """Validates legality, locality, regressions, and conflicts."""

    def __init__(self, task_agent: TaskAgent) -> None:
        self.conflict_checker = ConflictChecker()
        self.regression_checker = RegressionChecker(task_agent)
        self.operators = {
            SkillAction.GUARD: GuardOperator(),
            SkillAction.REPAIR: RepairOperator(),
            SkillAction.NOOP: NoOpOperator(),
        }

    def verify_and_apply(
        self, proposal: UpdateProposal, repository: SkillRepository
    ) -> VerificationResult:
        conflict, reason = self.conflict_checker.check(proposal, repository)
        if conflict:
            return VerificationResult(
                accepted=False,
                reason=reason,
                regression_cases=[],
                conflict=True,
            )

        if proposal.action == SkillAction.NOOP:
            self.operators[proposal.action].apply(proposal, repository)
            return VerificationResult(accepted=True, reason="noop accepted", regression_cases=[])

        snapshot_id = repository.snapshot()
        self.operators[proposal.action].apply(proposal, repository)
        has_regression, regression_cases = self.regression_checker.check(repository)
        if has_regression:
            repository.rollback(snapshot_id)
            return VerificationResult(
                accepted=False,
                reason="regression detected",
                regression_cases=regression_cases,
            )
        return VerificationResult(accepted=True, reason="accepted", regression_cases=[])

