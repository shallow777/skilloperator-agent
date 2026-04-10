"""Repository health tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RepositoryHealthMonitor:
    """Tracks repository-level health statistics over time."""

    accepted_edit_count: int = 0
    rejected_edit_count: int = 0
    regression_count: int = 0
    conflict_count: int = 0
    operator_usage_counts: dict[str, int] = field(default_factory=dict)
    task_count: int = 0
    noisy_failure_count: int = 0

    def record_operator(self, operator_name: str) -> None:
        self.operator_usage_counts[operator_name] = (
            self.operator_usage_counts.get(operator_name, 0) + 1
        )

    def record_verifier_result(
        self,
        accepted: bool,
        *,
        counts_as_edit: bool,
        regression: bool = False,
        conflict: bool = False,
    ) -> None:
        if counts_as_edit:
            if accepted:
                self.accepted_edit_count += 1
            else:
                self.rejected_edit_count += 1
        if regression:
            self.regression_count += 1
        if conflict:
            self.conflict_count += 1

    def record_task(self, noisy_failure: bool = False) -> None:
        self.task_count += 1
        if noisy_failure:
            self.noisy_failure_count += 1

    def summary(self, repository_size: int, edit_frequency: float) -> dict[str, Any]:
        """Return summary features for the SkillOps policy."""
        return {
            "repository_size": repository_size,
            "accepted_edit_count": self.accepted_edit_count,
            "rejected_edit_count": self.rejected_edit_count,
            "regression_count": self.regression_count,
            "conflict_count": self.conflict_count,
            "task_count": self.task_count,
            "edit_frequency": edit_frequency,
            "noisy_failure_count": self.noisy_failure_count,
            "operator_usage_counts": dict(self.operator_usage_counts),
        }
