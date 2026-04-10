"""Run a single synthetic case for debugging."""

from __future__ import annotations

import json
from dataclasses import asdict

from skillops_agent.agents.skillops_agent import SkillOpsAgent
from skillops_agent.agents.task_agent import TaskAgent
from skillops_agent.environments.continual_task_env import ContinualTaskEnvironment
from skillops_agent.policies.heuristic_policy import HeuristicSkillOpsPolicy
from skillops_agent.repository.edit_record import EditRecord
from skillops_agent.verifier.verifier import Verifier
from skillops_agent.evaluation.benchmark import build_default_repository


def main() -> None:
    repository = build_default_repository()
    case = ContinualTaskEnvironment.default_stream().stream()[0]
    task_agent = TaskAgent()
    skillops_agent = SkillOpsAgent(HeuristicSkillOpsPolicy())
    verifier = Verifier(task_agent)

    execution = task_agent.run_task(case.task, repository, case)
    decision = skillops_agent.decide(case.task, repository, execution)
    verification = verifier.verify_and_apply(decision.proposal, repository)
    repository.record_edit(
        EditRecord(
            action=decision.proposal.action,
            skill_id=decision.proposal.target_skill_id,
            rationale=decision.proposal.rationale,
            patch=decision.proposal.patch,
            accepted=verification.accepted,
            reason=verification.reason,
            confidence=decision.proposal.confidence,
        )
    )
    print(
        json.dumps(
            {
                "execution": {
                    "success": execution.success,
                    "trajectory": execution.trajectory,
                    "evidence": execution.evidence,
                },
                "proposal": {
                    "action": decision.proposal.action.value,
                    "target_skill_id": decision.proposal.target_skill_id,
                    "rationale": decision.proposal.rationale,
                    "patch": decision.proposal.patch,
                },
                "verification": asdict(verification),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
