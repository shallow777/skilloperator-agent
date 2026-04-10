"""Heuristic SkillOps policy."""

from __future__ import annotations

from skillops_agent.policies.base_policy import PolicyContext, SkillOpsPolicy
from skillops_agent.repository.edit_record import SkillAction, UpdateProposal
from skillops_agent.repository.repository import SkillRepository


class HeuristicSkillOpsPolicy(SkillOpsPolicy):
    """Simple typed policy for the synthetic benchmark."""

    def decide(self, context: PolicyContext, repository: SkillRepository) -> UpdateProposal:
        observed_skill_id = context.call_log[0]["skill_id"] if context.call_log else None
        expected_skill_id = context.evidence.get("expected_skill_id")

        if context.evidence.get("noisy_failure"):
            return UpdateProposal(
                action=SkillAction.NOOP,
                target_skill_id=None,
                rationale="Observed failure is external noise; editing repository is not justified.",
                patch={},
                confidence=0.9,
            )

        if context.evidence.get("misuse") and expected_skill_id:
            skill = repository.get_skill(observed_skill_id)
            disallowed = sorted(set(skill.contract.disallowed_task_types + [context.task.task_type]))
            notes = skill.contract.routing_notes + [
                f"Do not route {context.task.task_type}; prefer {expected_skill_id}."
            ]
            return UpdateProposal(
                action=SkillAction.GUARD,
                target_skill_id=observed_skill_id,
                rationale="Task failed because the wrong skill was invoked; tighten applicability.",
                patch={
                    "contract": {
                        "disallowed_task_types": disallowed,
                        "routing_notes": notes,
                    }
                },
                confidence=0.82,
                metadata={"expected_skill_id": expected_skill_id},
            )

        if context.evidence.get("local_defect") and observed_skill_id:
            skill = repository.get_skill(observed_skill_id)
            validations = skill.procedure.validation_steps + ["normalize decimals"]
            limitations = [
                limitation
                for limitation in skill.procedure.known_limitations
                if limitation != "decimal normalization missing"
            ]
            return UpdateProposal(
                action=SkillAction.REPAIR,
                target_skill_id=observed_skill_id,
                rationale="Invocation was correct but the procedure has a localized validation defect.",
                patch={
                    "procedure": {
                        "validation_steps": validations,
                        "known_limitations": limitations,
                    }
                },
                confidence=0.88,
            )

        return UpdateProposal(
            action=SkillAction.NOOP,
            target_skill_id=None,
            rationale="Evidence is insufficient for a repository edit.",
            patch={},
            confidence=0.55,
        )

