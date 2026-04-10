"""Structured skill repository state."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from skillops_agent.repository.edit_record import EditRecord, SkillAction
from skillops_agent.repository.health_monitor import RepositoryHealthMonitor
from skillops_agent.repository.skill import Skill


@dataclass(slots=True)
class SkillRepository:
    """Structured evolving repository with snapshot and rollback support."""

    skills: dict[str, Skill] = field(default_factory=dict)
    relation_edges: list[tuple[str, str, str]] = field(default_factory=list)
    edit_records: list[EditRecord] = field(default_factory=list)
    replay_buffer: list[dict[str, Any]] = field(default_factory=list)
    health_monitor: RepositoryHealthMonitor = field(default_factory=RepositoryHealthMonitor)
    _snapshots: list[dict[str, Any]] = field(default_factory=list, repr=False)

    def add_skill(self, skill: Skill) -> None:
        self.skills[skill.id] = copy.deepcopy(skill)

    def get_skill(self, skill_id: str) -> Skill:
        return self.skills[skill_id]

    def list_skills(self) -> list[Skill]:
        return list(self.skills.values())

    def update_contract(self, skill_id: str, contract_patch: dict[str, Any]) -> None:
        skill = self.get_skill(skill_id)
        for field_name, value in contract_patch.items():
            setattr(skill.contract, field_name, value)

    def update_procedure(self, skill_id: str, procedure_patch: dict[str, Any]) -> None:
        skill = self.get_skill(skill_id)
        for field_name, value in procedure_patch.items():
            setattr(skill.procedure, field_name, value)

    def snapshot(self) -> int:
        self._snapshots.append(self.to_dict())
        return len(self._snapshots) - 1

    def rollback(self, snapshot_id: int) -> None:
        state = self._snapshots[snapshot_id]
        restored = self.from_dict(state)
        self.skills = restored.skills
        self.relation_edges = restored.relation_edges
        self.edit_records = restored.edit_records
        self.replay_buffer = restored.replay_buffer
        self.health_monitor = restored.health_monitor

    def record_edit(self, record: EditRecord) -> None:
        self.edit_records.append(record)
        if record.skill_id and record.skill_id in self.skills:
            self.skills[record.skill_id].edit_history.append(record.timestamp)

    def add_replay_case(self, case: dict[str, Any]) -> None:
        self.replay_buffer.append(copy.deepcopy(case))

    def get_replay_cases(self, limit: int = 5) -> list[dict[str, Any]]:
        return copy.deepcopy(self.replay_buffer[-limit:])

    def repository_size(self) -> int:
        return len(self.skills)

    def edit_frequency(self) -> float:
        task_count = self.health_monitor.task_count
        if task_count == 0:
            return 0.0
        return self.health_monitor.accepted_edit_count / task_count

    def health_summary(self) -> dict[str, Any]:
        return self.health_monitor.summary(
            repository_size=self.repository_size(),
            edit_frequency=self.edit_frequency(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "skills": {key: skill.to_dict() for key, skill in self.skills.items()},
            "relation_edges": copy.deepcopy(self.relation_edges),
            "edit_records": [asdict(record) for record in self.edit_records],
            "replay_buffer": copy.deepcopy(self.replay_buffer),
            "health_monitor": asdict(self.health_monitor),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SkillRepository":
        from skillops_agent.repository.skill import (
            Skill,
            SkillContract,
            SkillProcedure,
            UsageStats,
        )

        repository = cls()
        for skill_id, raw in payload["skills"].items():
            repository.skills[skill_id] = Skill(
                id=raw["id"],
                name=raw["name"],
                description=raw["description"],
                contract=SkillContract(**raw["contract"]),
                procedure=SkillProcedure(**raw["procedure"]),
                examples=raw.get("examples", []),
                dependencies=raw.get("dependencies", []),
                provenance=raw.get("provenance", {}),
                usage_stats=UsageStats(**raw.get("usage_stats", {})),
                edit_history=raw.get("edit_history", []),
                status=raw.get("status", "active"),
            )
        repository.relation_edges = [tuple(edge) for edge in payload.get("relation_edges", [])]
        repository.edit_records = [
            EditRecord(
                action=SkillAction(raw["action"]),
                skill_id=raw["skill_id"],
                rationale=raw["rationale"],
                patch=raw["patch"],
                accepted=raw["accepted"],
                reason=raw["reason"],
                timestamp=raw["timestamp"],
                confidence=raw.get("confidence"),
            )
            for raw in payload.get("edit_records", [])
        ]
        repository.replay_buffer = payload.get("replay_buffer", [])
        repository.health_monitor = RepositoryHealthMonitor(**payload.get("health_monitor", {}))
        return repository

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
