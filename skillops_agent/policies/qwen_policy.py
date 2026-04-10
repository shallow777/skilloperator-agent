"""Qwen policy with local Transformers loading."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from skillops_agent.config import ModelConfig
from skillops_agent.policies.base_policy import PolicyContext, SkillOpsPolicy
from skillops_agent.repository.edit_record import SkillAction, UpdateProposal
from skillops_agent.repository.repository import SkillRepository


@dataclass(slots=True)
class QwenDecisionEnvelope:
    """Serializable prompt bundle for local model inference."""

    model_name: str
    mode: str
    prompt_payload: dict[str, Any]


class QwenSkillOpsPolicy(SkillOpsPolicy):
    """Loads a local Qwen model through Transformers and emits repository decisions."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self._tokenizer: Any | None = None
        self._model: Any | None = None

    def build_prompt(self, context: PolicyContext, repository: SkillRepository) -> dict[str, Any]:
        return {
            "instruction": (
                "Choose exactly one action: guard, repair, or noop. "
                "Guard edits only contracts. Repair edits only procedures. "
                "Prefer sparse updates under limited change budget. "
                "Return valid JSON only with keys: action, target_skill_id, rationale, patch, confidence. "
                "For guard, patch must only contain a contract object. "
                "For repair, patch must only contain a procedure object. "
                "For noop, patch must be an empty object and target_skill_id must be null."
            ),
            "task": asdict(context.task),
            "repository_summary": context.repository_summary,
            "trajectory": context.trajectory,
            "call_log": context.call_log,
            "evidence": context.evidence,
            "recent_edit_history": [asdict(record) for record in context.recent_edit_history],
            "skills": [skill.to_dict() for skill in repository.list_skills()],
        }

    def build_envelope(
        self, context: PolicyContext, repository: SkillRepository
    ) -> QwenDecisionEnvelope:
        return QwenDecisionEnvelope(
            model_name=self.config.model_name,
            mode=self.config.mode,
            prompt_payload=self.build_prompt(context, repository),
        )

    def _resolve_torch_dtype(self) -> Any:
        import torch

        if self.config.torch_dtype == "auto":
            return "auto"
        if not hasattr(torch, self.config.torch_dtype):
            raise ValueError(f"Unsupported torch dtype: {self.config.torch_dtype}")
        return getattr(torch, self.config.torch_dtype)

    def _ensure_model_loaded(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name,
            trust_remote_code=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            torch_dtype=self._resolve_torch_dtype(),
            device_map=self.config.device_map,
            attn_implementation=self.config.attn_implementation,
            trust_remote_code=True,
        )
        self._tokenizer = tokenizer
        self._model = model

    def _render_messages(self, envelope: QwenDecisionEnvelope) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "You are the SkillOps Agent for repository maintenance. "
                    "Choose exactly one action from {guard, repair, noop}. "
                    "Follow typed edit constraints strictly and output JSON only."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(envelope.prompt_payload, indent=2, ensure_ascii=False),
            },
        ]

    def _generate_raw_response(self, envelope: QwenDecisionEnvelope) -> str:
        if self.config.mode != "local":
            raise ValueError(
                f"QwenSkillOpsPolicy only supports local mode in this build; got {self.config.mode}"
            )

        self._ensure_model_loaded()
        messages = self._render_messages(envelope)
        prompt = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        model_inputs = self._tokenizer([prompt], return_tensors="pt")

        if hasattr(self._model, "device"):
            model_inputs = {key: value.to(self._model.device) for key, value in model_inputs.items()}

        generated_ids = self._model.generate(
            **model_inputs,
            max_new_tokens=self.config.max_new_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            do_sample=self.config.temperature > 0,
        )
        trimmed_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs["input_ids"], generated_ids)
        ]
        return self._tokenizer.batch_decode(trimmed_ids, skip_special_tokens=True)[0].strip()

    def _extract_json_text(self, raw_text: str) -> str:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            raise ValueError(f"Model output did not contain JSON: {raw_text[:200]}")
        return match.group(0)

    def _coerce_action(self, raw_action: str) -> SkillAction:
        normalized = raw_action.strip().lower()
        if normalized == "guard":
            return SkillAction.GUARD
        if normalized == "repair":
            return SkillAction.REPAIR
        if normalized in {"noop", "no-op", "no_op"}:
            return SkillAction.NOOP
        raise ValueError(f"Unsupported model action: {raw_action}")

    def _parse_response(self, raw_text: str) -> dict[str, Any]:
        json_text = self._extract_json_text(raw_text)
        payload = json.loads(json_text)
        if not isinstance(payload, dict):
            raise ValueError("Model response JSON must be an object")
        return payload

    def _proposal_from_payload(
        self,
        payload: dict[str, Any],
        envelope: QwenDecisionEnvelope,
        raw_text: str,
    ) -> UpdateProposal:
        action = self._coerce_action(str(payload["action"]))
        target_skill_id = payload.get("target_skill_id")
        rationale = str(payload.get("rationale", "")).strip()
        confidence = float(payload.get("confidence", 0.0))
        patch = payload.get("patch", {})

        if action == SkillAction.NOOP:
            target_skill_id = None
            patch = {}
        elif not isinstance(patch, dict):
            raise ValueError("Model patch must be a JSON object")

        return UpdateProposal(
            action=action,
            target_skill_id=target_skill_id,
            rationale=rationale or "Qwen local inference decision.",
            patch=patch,
            confidence=confidence,
            metadata={
                "qwen_request": {
                    "model_name": envelope.model_name,
                    "mode": envelope.mode,
                    "torch_dtype": self.config.torch_dtype,
                    "device_map": self.config.device_map,
                    "attn_implementation": self.config.attn_implementation,
                    "max_new_tokens": self.config.max_new_tokens,
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p,
                },
                "qwen_request_json": json.dumps(asdict(envelope), indent=2),
                "raw_model_response": raw_text,
            },
        )

    def decide(self, context: PolicyContext, repository: SkillRepository) -> UpdateProposal:
        envelope = self.build_envelope(context, repository)
        raw_text = self._generate_raw_response(envelope)
        payload = self._parse_response(raw_text)
        return self._proposal_from_payload(payload, envelope, raw_text)
