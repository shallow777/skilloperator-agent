# SkillOps Agent

SkillOps Agent is a research prototype for repository maintenance under a continual task stream. The system is not a generic skill-library agent and not a self-expanding skill accumulation framework. Its focus is disciplined maintenance of an existing skill repository under limited change budget.

## Research Motivation

Long-running skill-based agents often fail because useful skills are misapplied, routed too broadly, or contain localized execution defects. In a single-domain continual setting, those issues matter more than endless creation of new skills. SkillOps Agent studies whether sparse, typed repository interventions can preserve long-term repository health while controlling regression risk and repository sprawl.

## What Makes This Different

Standard self-evolving skill agents usually emphasize discovering and adding new skills. This prototype instead restricts the maintenance action space to:

- `Guard`: contract/applicability update only
- `Repair`: procedure/execution update only
- `No-Op`: explicit decision to not edit

The central question is not "what new skill should be added?" but "should the repository be edited at all, and if yes, where?"

## Architecture

The end-to-end loop is:

1. Incoming task arrives.
2. `TaskAgent` selects and executes a skill from the current repository.
3. Execution produces output, trajectory, call log, success/failure, and evidence.
4. `SkillOpsAgent` observes the evidence and proposes `Guard`, `Repair`, or `No-Op`.
5. `Verifier` checks legality, locality, conflict risk, and replay-based regression.
6. Accepted proposals update the repository; rejected proposals are rolled back.
7. `RepositoryHealthMonitor` tracks repository-level health statistics over time.

The implementation keeps `TaskAgent` and `SkillOpsAgent` fully separate. The task agent never edits the repository directly.

## Skill Representation

Each skill is explicit structured state:

```python
Skill(
    id,
    name,
    description,
    contract,
    procedure,
    examples,
    dependencies,
    provenance,
    usage_stats,
    edit_history,
    status,
)
```

`contract` models applicability, routing hints, and abstention behavior. `procedure` models execution steps and validation behavior. This separation is enforced by the operators and verifier.

## Guard vs Repair vs No-Op

- `Guard` changes only the contract layer. It is intended for misuse, routing ambiguity, or unclear applicability boundaries.
- `Repair` changes only the procedure layer. It is intended for localized execution defects after correct invocation.
- `No-Op` is a first-class action for noisy external failures, weak evidence, or high edit risk.

This distinction is intentional: V1 is about repository maintenance discipline, not unconstrained editing.

## Qwen-4B Backbone Path

The project includes two policy paths:

- `HeuristicSkillOpsPolicy`: deterministic baseline used by the toy benchmark
- `QwenSkillOpsPolicy`: prompt/stub interface for future Qwen-4B-backed decision making

V1 does not deploy Qwen-4B, but the policy interface is structured so the heuristic policy can later be replaced by:

- prompted Qwen-4B
- supervised fine-tuned Qwen-4B
- RL-trained repository maintenance policy

## Toy Continual Benchmark

The synthetic environment includes three canonical scenarios:

- misuse scenario where `Guard` improves future routing
- localized procedure bug where `Repair` fixes an otherwise useful skill
- noisy external failure where `No-Op` is the correct repository decision

The default repository is intentionally imperfect:

- `json_parser` is initially too broad and incorrectly claims applicability to `csv_cleanup`
- `json_parser` also lacks a decimal normalization validation step
- `api_syncer` can encounter external timeout noise that should not trigger repository edits

## Repository Monitor and Verifier

`RepositoryHealthMonitor` tracks:

- repository size
- edit frequency
- accepted edit count
- rejected edit count
- regression count
- conflict count
- operator usage counts

`Verifier` is programmatic, not another free-form agent. It checks:

- proposal format and target existence
- contract-vs-procedure locality constraints
- duplicate/conflicting edits
- replay-based regressions over historical successful cases

## Running The Prototype

Use Python 3.10+.

Run the full benchmark:

```bash
python3 main.py
```

Run via the benchmark module:

```bash
python3 -m skillops_agent.evaluation.run_eval
```

Run one synthetic case:

```bash
python3 skillops_agent/scripts/run_single_case.py
```

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

## Evaluation Metrics

The benchmark reports:

- future task success rate
- misuse rate
- regression rate
- accepted edit count
- rejected edit count
- operator usage counts

Repository monitor output also exposes repository size and edit frequency.

## Code Structure

```text
skill_operator_agent/
├── skillops_agent/
│   ├── agents/
│   ├── configs/
│   ├── environments/
│   ├── evaluation/
│   ├── operators/
│   ├── policies/
│   ├── repository/
│   ├── scripts/
│   └── verifier/
├── tests/
├── main.py
└── README.md
```

## Current Limitations

- Single synthetic domain only
- Deterministic task execution model
- Replay regression uses a very small historical successful set
- Qwen-4B path is a stub interface rather than a deployed model
- No learned policy training in V1

## Natural Next Steps

- replace the heuristic policy with prompted Qwen-4B decisions
- log richer execution traces for supervised maintenance datasets
- add learned acceptance scoring or risk prediction
- expand the benchmark with more boundary ambiguity and localized defect patterns
- study maintenance under stricter edit budgets and longer horizons
