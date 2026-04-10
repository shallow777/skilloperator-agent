"""SkillOps policy tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from skillops_agent.agents.skillops_agent import SkillOpsAgent
from skillops_agent.agents.task_agent import TaskAgent
from skillops_agent.config import load_model_config
from skillops_agent.environments.continual_task_env import ContinualTaskEnvironment
from skillops_agent.policies.heuristic_policy import HeuristicSkillOpsPolicy
from skillops_agent.policies.qwen_policy import QwenSkillOpsPolicy
from skillops_agent.repository.edit_record import SkillAction
from skillops_agent.evaluation.benchmark import build_default_repository


class SkillOpsPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = build_default_repository()
        self.task_agent = TaskAgent()
        self.skillops_agent = SkillOpsAgent(HeuristicSkillOpsPolicy())
        self.environment = ContinualTaskEnvironment.default_stream().stream()

    def test_misuse_triggers_guard(self) -> None:
        case = self.environment[0]
        execution = self.task_agent.run_task(case.task, self.repository, case)
        decision = self.skillops_agent.decide(case.task, self.repository, execution)
        self.assertEqual(decision.proposal.action, SkillAction.GUARD)

    def test_procedure_bug_triggers_repair(self) -> None:
        case = self.environment[1]
        execution = self.task_agent.run_task(case.task, self.repository, case)
        decision = self.skillops_agent.decide(case.task, self.repository, execution)
        self.assertEqual(decision.proposal.action, SkillAction.REPAIR)

    def test_noisy_failure_triggers_noop(self) -> None:
        case = self.environment[3]
        execution = self.task_agent.run_task(case.task, self.repository, case)
        decision = self.skillops_agent.decide(case.task, self.repository, execution)
        self.assertEqual(decision.proposal.action, SkillAction.NOOP)

    def test_qwen_policy_loads_parameters(self) -> None:
        config = load_model_config(
            env={
                "SKILLOPS_POLICY": "qwen",
                "SKILLOPS_MODEL_MODE": "local",
                "SKILLOPS_MODEL_NAME": "/models/Qwen3.5-4B",
                "SKILLOPS_TORCH_DTYPE": "bfloat16",
                "SKILLOPS_DEVICE_MAP": "cuda:0",
                "SKILLOPS_ATTN_IMPLEMENTATION": "flash_attention_2",
                "SKILLOPS_MAX_NEW_TOKENS": "256",
                "SKILLOPS_TEMPERATURE": "0.2",
                "SKILLOPS_TOP_P": "0.8",
                "SKILLOPS_TIMEOUT_SECONDS": "12",
            }
        )
        policy = QwenSkillOpsPolicy(config)
        case = self.environment[0]
        execution = self.task_agent.run_task(case.task, self.repository, case)
        with patch.object(
            QwenSkillOpsPolicy,
            "_generate_raw_response",
            return_value=(
                '{"action": "noop", "target_skill_id": null, "rationale": "test", '
                '"patch": {}, "confidence": 0.7}'
            ),
        ):
            decision = SkillOpsAgent(policy).decide(case.task, self.repository, execution)
        self.assertEqual(config.policy, "qwen")
        self.assertEqual(config.mode, "local")
        self.assertEqual(config.model_name, "/models/Qwen3.5-4B")
        self.assertEqual(config.torch_dtype, "bfloat16")
        self.assertEqual(config.device_map, "cuda:0")
        self.assertEqual(config.attn_implementation, "flash_attention_2")
        self.assertEqual(config.max_new_tokens, 256)
        self.assertEqual(config.temperature, 0.2)
        self.assertEqual(config.top_p, 0.8)
        self.assertEqual(config.timeout_seconds, 12)
        self.assertEqual(decision.proposal.action, SkillAction.NOOP)
        self.assertEqual(
            decision.proposal.metadata["qwen_request"]["torch_dtype"],
            "bfloat16",
        )


if __name__ == "__main__":
    unittest.main()
