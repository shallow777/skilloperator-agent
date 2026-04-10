"""Synthetic continual task benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from skillops_agent.environments.base_env import EnvironmentOutcome, Task
from skillops_agent.repository.skill import Skill


@dataclass(slots=True)
class SyntheticTaskCase:
    """A task plus its encoded environment dynamics."""

    task: Task
    scenario: str

    def evaluate(self, skill: Skill) -> EnvironmentOutcome:
        if self.scenario == "misuse":
            correct = skill.id == self.task.expected_skill_id
            success = correct
            evidence = {
                "misuse": not correct,
                "local_defect": False,
                "noisy_failure": False,
                "expected_skill_id": self.task.expected_skill_id,
                "observed_skill_id": skill.id,
            }
            trace = ["contract_match_check", "routing_failure" if not success else "routing_success"]
            return EnvironmentOutcome(success, f"route:{skill.id}", trace, evidence)

        if self.scenario == "procedure_bug":
            buggy = "normalize decimals" not in skill.procedure.validation_steps
            success = not buggy
            evidence = {
                "misuse": False,
                "local_defect": buggy,
                "noisy_failure": False,
                "expected_skill_id": self.task.expected_skill_id,
                "observed_skill_id": skill.id,
            }
            trace = ["procedure_execution", "missing_decimal_validation" if buggy else "validated"]
            return EnvironmentOutcome(success, f"parsed:{not buggy}", trace, evidence)

        success = False
        evidence = {
            "misuse": False,
            "local_defect": False,
            "noisy_failure": True,
            "expected_skill_id": self.task.expected_skill_id,
            "observed_skill_id": skill.id,
        }
        trace = ["tool_call", "external_timeout"]
        return EnvironmentOutcome(success, "external_timeout", trace, evidence)


class ContinualTaskEnvironment:
    """Provides a deterministic continual stream for evaluation."""

    def __init__(self, tasks: Iterable[SyntheticTaskCase]) -> None:
        self._tasks = list(tasks)

    def stream(self) -> list[SyntheticTaskCase]:
        return list(self._tasks)

    @classmethod
    def default_stream(cls) -> "ContinualTaskEnvironment":
        tasks = [
            SyntheticTaskCase(
                task=Task(
                    id="t1",
                    task_type="csv_cleanup",
                    payload={"text": "Revenue was 42.5"},
                    expected_skill_id="csv_cleaner",
                    metadata={"scenario": "misuse"},
                ),
                scenario="misuse",
            ),
            SyntheticTaskCase(
                task=Task(
                    id="t2",
                    task_type="json_parse",
                    payload={"text": '{"price": "42.5"}'},
                    expected_skill_id="json_parser",
                    metadata={"scenario": "procedure_bug"},
                ),
                scenario="procedure_bug",
            ),
            SyntheticTaskCase(
                task=Task(
                    id="t3",
                    task_type="json_parse",
                    payload={"text": '{"price": "43.0"}'},
                    expected_skill_id="json_parser",
                    metadata={"scenario": "procedure_bug"},
                ),
                scenario="procedure_bug",
            ),
            SyntheticTaskCase(
                task=Task(
                    id="t4",
                    task_type="api_sync",
                    payload={"endpoint": "/status"},
                    expected_skill_id="api_syncer",
                    metadata={"scenario": "noisy_failure"},
                ),
                scenario="noisy_failure",
            ),
            SyntheticTaskCase(
                task=Task(
                    id="t5",
                    task_type="csv_cleanup",
                    payload={"text": "Revenue was 44.1"},
                    expected_skill_id="csv_cleaner",
                    metadata={"scenario": "misuse"},
                ),
                scenario="misuse",
            ),
        ]
        return cls(tasks)

