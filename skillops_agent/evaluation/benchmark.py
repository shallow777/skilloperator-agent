"""Benchmark assembly and end-to-end stream execution."""

from __future__ import annotations

from dataclasses import asdict

from skillops_agent.agents.skillops_agent import SkillOpsAgent
from skillops_agent.agents.task_agent import TaskAgent
from skillops_agent.environments.continual_task_env import ContinualTaskEnvironment
from skillops_agent.evaluation.metrics import StreamMetrics
from skillops_agent.policies.heuristic_policy import HeuristicSkillOpsPolicy
from skillops_agent.repository.edit_record import EditRecord, SkillAction
from skillops_agent.repository.repository import SkillRepository
from skillops_agent.repository.skill import Skill, SkillContract, SkillProcedure
from skillops_agent.verifier.verifier import Verifier


def build_default_repository() -> SkillRepository:
    """Create the intentionally imperfect V1 repository."""
    repository = SkillRepository()
    repository.add_skill(
        Skill(
            id="json_parser",
            name="JSON Parser",
            description="Parse lightweight JSON objects with decimal values.",
            contract=SkillContract(
                allowed_task_types=["json_parse", "csv_cleanup"],
                routing_notes=["Often selected for structured text parsing."],
            ),
            procedure=SkillProcedure(
                steps=["parse JSON payload", "extract numeric fields"],
                validation_steps=["check braces"],
                known_limitations=["decimal normalization missing"],
            ),
        )
    )
    repository.add_skill(
        Skill(
            id="csv_cleaner",
            name="CSV Cleaner",
            description="Clean CSV-like text and normalize rows.",
            contract=SkillContract(allowed_task_types=["csv_cleanup"]),
            procedure=SkillProcedure(
                steps=["split rows", "normalize separators"],
                validation_steps=["trim whitespace"],
            ),
        )
    )
    repository.add_skill(
        Skill(
            id="api_syncer",
            name="API Syncer",
            description="Perform API sync tasks with retry notes.",
            contract=SkillContract(allowed_task_types=["api_sync"]),
            procedure=SkillProcedure(
                steps=["call API endpoint", "parse status"],
                validation_steps=["check HTTP status"],
            ),
        )
    )
    return repository


def run_stream() -> tuple[SkillRepository, StreamMetrics]:
    """Run the full continual loop for the default benchmark."""
    repository = build_default_repository()
    task_agent = TaskAgent()
    skillops_agent = SkillOpsAgent(policy=HeuristicSkillOpsPolicy())
    verifier = Verifier(task_agent)
    environment = ContinualTaskEnvironment.default_stream()
    metrics = StreamMetrics()

    for case in environment.stream():
        repository.health_monitor.record_task(noisy_failure=case.scenario == "noisy_failure")
        execution = task_agent.run_task(case.task, repository, case)
        if execution.success:
            repository.add_replay_case({"task": asdict(case.task), "scenario": case.scenario})
        decision = skillops_agent.decide(case.task, repository, execution)
        verification = verifier.verify_and_apply(decision.proposal, repository)

        record = EditRecord(
            action=decision.proposal.action,
            skill_id=decision.proposal.target_skill_id,
            rationale=decision.proposal.rationale,
            patch=decision.proposal.patch,
            accepted=verification.accepted,
            reason=verification.reason,
            confidence=decision.proposal.confidence,
        )
        repository.record_edit(record)
        repository.health_monitor.record_operator(decision.proposal.action.value)
        repository.health_monitor.record_verifier_result(
            verification.accepted,
            counts_as_edit=decision.proposal.action != SkillAction.NOOP,
            regression=bool(verification.regression_cases),
            conflict=verification.conflict,
        )

        metrics.total_tasks += 1
        metrics.record_operator(decision.proposal.action.value)
        if execution.success:
            metrics.successful_tasks += 1
        if execution.evidence.get("misuse"):
            metrics.misuse_failures += 1
        if verification.regression_cases:
            metrics.regression_failures += len(verification.regression_cases)
        if verification.accepted and decision.proposal.action != SkillAction.NOOP:
            metrics.accepted_edits += 1
        if not verification.accepted and decision.proposal.action != SkillAction.NOOP:
            metrics.rejected_edits += 1

    return repository, metrics
