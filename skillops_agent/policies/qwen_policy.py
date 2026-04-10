"""Qwen-4B policy interface/stub."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from skillops_agent.policies.base_policy import PolicyContext, SkillOpsPolicy
from skillops_agent.repository.edit_record import SkillAction, UpdateProposal
from skillops_agent.repository.repository import SkillRepository


class QwenSkillOpsPolicy(SkillOpsPolicy):
    """Prompt-ready wrapper that can later call a real Qwen-4B backend."""

    def build_prompt(self, context: PolicyContext, repository: SkillRepository) -> dict[str, Any]:
        return {
            "instruction": (
                "Choose exactly one action: guard, repair, or noop. "
                "Guard edits only contracts. Repair edits only procedures. "
                "Prefer sparse updates under limited change budget."
            ),
            "task": asdict(context.task),
            "repository_summary": context.repository_summary,
            "trajectory": context.trajectory,
            "call_log": context.call_log,
            "evidence": context.evidence,
            "recent_edit_history": [asdict(record) for record in context.recent_edit_history],
            "skills": [skill.to_dict() for skill in repository.list_skills()],
        }

    def decide(self, context: PolicyContext, repository: SkillRepository) -> UpdateProposal:
        prompt_payload = self.build_prompt(context, repository)
        return UpdateProposal(
            action=SkillAction.NOOP,
            target_skill_id=None,
            rationale="Stub Qwen-4B policy; replace with model inference over the generated prompt.",
            patch={},
            confidence=0.0,
            metadata={"prompt_payload": prompt_payload},
        )

