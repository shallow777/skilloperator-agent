"""Evaluation entrypoint."""

from __future__ import annotations

import json

from skillops_agent.config import load_model_config
from skillops_agent.evaluation.benchmark import run_stream


def main() -> None:
    config = load_model_config()
    repository, metrics = run_stream(config=config)
    payload = {
        "model_config": {
            "policy": config.policy,
            "mode": config.mode,
            "model_name": config.model_name,
            "torch_dtype": config.torch_dtype,
            "device_map": config.device_map,
            "attn_implementation": config.attn_implementation,
            "max_new_tokens": config.max_new_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "api_base": config.api_base,
            "api_key_env": config.api_key_env,
        },
        "metrics": metrics.as_dict(),
        "repository_health": repository.health_summary(),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
