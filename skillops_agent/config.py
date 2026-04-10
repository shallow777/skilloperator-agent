"""Lightweight configuration loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _parse_scalar(raw: str) -> object:
    value = raw.strip()
    if not value:
        return ""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("'\"")


def load_simple_yaml(path: str | Path) -> dict[str, object]:
    """Parse a flat key-value YAML file without external dependencies."""
    payload: dict[str, object] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        payload[key.strip()] = _parse_scalar(raw_value)
    return payload


@dataclass(slots=True)
class ModelConfig:
    """Model/policy parameters for SkillOps."""

    backbone: str = "qwen3.5-4b"
    mode: str = "local"
    policy: str = "qwen"
    model_name: str = "Qwen/Qwen3-4B"
    torch_dtype: str = "auto"
    device_map: str = "auto"
    attn_implementation: str = "sdpa"
    max_new_tokens: int = 512
    temperature: float = 0.1
    top_p: float = 0.9
    api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    api_key_env: str = "DASHSCOPE_API_KEY"
    timeout_seconds: int = 30
    decision_output: str = "structured_update_proposal"


def load_model_config(
    path: str | Path | None = None,
    *,
    env: dict[str, str] | None = None,
) -> ModelConfig:
    """Load model config from YAML and environment overrides."""
    resolved_env = env or os.environ
    config_path = Path(path or Path(__file__).parent / "configs" / "model.yaml")
    raw = load_simple_yaml(config_path)

    config = ModelConfig(
        backbone=str(raw.get("backbone", "qwen")),
        mode=str(raw.get("mode", "local")),
        policy=str(raw.get("policy", "qwen")),
        model_name=str(raw.get("model_name", "Qwen/Qwen3-4B")),
        torch_dtype=str(raw.get("torch_dtype", "auto")),
        device_map=str(raw.get("device_map", "auto")),
        attn_implementation=str(raw.get("attn_implementation", "sdpa")),
        max_new_tokens=int(raw.get("max_new_tokens", 512)),
        temperature=float(raw.get("temperature", 0.1)),
        top_p=float(raw.get("top_p", 0.9)),
        api_base=str(raw.get("api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1")),
        api_key_env=str(raw.get("api_key_env", "DASHSCOPE_API_KEY")),
        timeout_seconds=int(raw.get("timeout_seconds", 30)),
        decision_output=str(raw.get("decision_output", "structured_update_proposal")),
    )

    config.policy = resolved_env.get("SKILLOPS_POLICY", config.policy)
    config.mode = resolved_env.get("SKILLOPS_MODEL_MODE", config.mode)
    config.model_name = resolved_env.get("SKILLOPS_MODEL_NAME", config.model_name)
    config.torch_dtype = resolved_env.get("SKILLOPS_TORCH_DTYPE", config.torch_dtype)
    config.device_map = resolved_env.get("SKILLOPS_DEVICE_MAP", config.device_map)
    config.attn_implementation = resolved_env.get(
        "SKILLOPS_ATTN_IMPLEMENTATION", config.attn_implementation
    )
    config.api_base = resolved_env.get("SKILLOPS_API_BASE", config.api_base)
    config.api_key_env = resolved_env.get("SKILLOPS_API_KEY_ENV", config.api_key_env)
    timeout_override = resolved_env.get("SKILLOPS_TIMEOUT_SECONDS")
    if timeout_override:
        config.timeout_seconds = int(timeout_override)
    max_new_tokens_override = resolved_env.get("SKILLOPS_MAX_NEW_TOKENS")
    if max_new_tokens_override:
        config.max_new_tokens = int(max_new_tokens_override)
    temperature_override = resolved_env.get("SKILLOPS_TEMPERATURE")
    if temperature_override:
        config.temperature = float(temperature_override)
    top_p_override = resolved_env.get("SKILLOPS_TOP_P")
    if top_p_override:
        config.top_p = float(top_p_override)
    return config
