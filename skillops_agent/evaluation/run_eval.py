"""Evaluation entrypoint."""

from __future__ import annotations

import json

from skillops_agent.evaluation.benchmark import run_stream


def main() -> None:
    repository, metrics = run_stream()
    payload = {
        "metrics": metrics.as_dict(),
        "repository_health": repository.health_summary(),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

