"""Evaluation metrics for continual maintenance."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class StreamMetrics:
    """Aggregated evaluation metrics."""

    total_tasks: int = 0
    successful_tasks: int = 0
    misuse_failures: int = 0
    regression_failures: int = 0
    accepted_edits: int = 0
    rejected_edits: int = 0
    operator_usage_counts: dict[str, int] = field(default_factory=dict)

    def record_operator(self, name: str) -> None:
        self.operator_usage_counts[name] = self.operator_usage_counts.get(name, 0) + 1

    def as_dict(self) -> dict[str, float | int | dict[str, int]]:
        success_rate = self.successful_tasks / self.total_tasks if self.total_tasks else 0.0
        misuse_rate = self.misuse_failures / self.total_tasks if self.total_tasks else 0.0
        regression_rate = self.regression_failures / self.total_tasks if self.total_tasks else 0.0
        return {
            "total_tasks": self.total_tasks,
            "future_task_success_rate": round(success_rate, 3),
            "misuse_rate": round(misuse_rate, 3),
            "regression_rate": round(regression_rate, 3),
            "accepted_edit_count": self.accepted_edits,
            "rejected_edit_count": self.rejected_edits,
            "operator_usage_counts": dict(self.operator_usage_counts),
        }

