# AI Product Idea Validator

Is your product idea worth testing? Use AI to discover opportunities, compare concepts, and plan low-cost validation experiments.

Three independent agents for **product discovery**, **concept development**, and **idea evaluation and validation planning**. Each works on its own and loads only the relevant method cards. Built for physical products, digital products, and services.

**Version 0.3.0a1 — public alpha.** Six innovation mechanisms connect a user's task and resource constraints to concrete concepts. Every discovery or concept result records its baseline, tension, mechanism, implementation, behavior change, reason to switch, capability gaps, tradeoffs and falsifier. Structural checks do not prove originality or commercial value. Live API integration and independent output-quality evaluation remain untested.

Discovery includes an initial concept mechanism in the same model call. An existing idea can go straight to concept development; comparison and review use validation. Cosmetic improvements are valid when requested. The agent may return no proposed directions when none are justified. No automatic multi-agent debate is required.

The agents provide comparable options, decision reasons, resource assumptions and experiment plans. Teams decide what to fund and execute using their people, budget, time and delivery capabilities. Real market validation happens through that execution; commercial success is not a prerequisite for releasing this decision-support tool.

## Quick start

Python 3.10+, standard-library runtime, no dependencies:

```bash
python -m innovation_agent task demo --agent validation --output-dir work/demo
```

This replays synthetic fixtures; it does not call a model. See `work/demo/report.md`.

Copy one of `agents/{opportunity,concept,validation}/AGENT.md` into an AI conversation for prompt-only use. For a persistent ChatGPT Project, upload [PROJECT_KNOWLEDGE.txt](chatgpt/PROJECT_KNOWLEDGE.txt) and paste [PROJECT_INSTRUCTIONS.txt](chatgpt/PROJECT_INSTRUCTIONS.txt) into its instructions. Replace older copies manually. Program checks require the CLI. Instructions are primarily Chinese; they follow the requested output language. Native English task-quality evaluation has not been performed.

For a real task, provide `goal` and `context`; validation also requires `candidates` with `id`, `title`, and `description`. See `examples/tasks/`.

```bash
python -m innovation_agent task prepare --agent validation --input examples/tasks/validation.input.json --output work/prompt.md
python -m innovation_agent task import --agent validation --input examples/tasks/validation.input.json --analysis answer.json --output-dir work/run-001
```

API mode requires `OPENAI_API_KEY` and `INNOVATION_MODEL` for a model supporting Responses API Structured Outputs:

```bash
python -m innovation_agent task run --agent validation --input examples/tasks/validation.input.json --output-dir work/api-001
```

One paid API call, no automatic retries. `result.json` preserves input, analysis, checks, version and usage metadata. Each run needs a new output directory. Input changes invalidate previous outputs.

Upgrade: v0.3 discovery and concept outputs require an `innovation` object. Reuse existing inputs, but regenerate old outputs. Do not bypass the new contract by changing only the digest. Project instructions, standalone prompts and API prompts are generated from shared sources using `python scripts/build_guidance.py`; release checks reject stale copies.

Simulated users do not validate demand. Verified flags are supplied by the user, not independently verified by the software. Matching citations do not establish semantic sufficiency. Passing selected checks is not business approval. No automatic web research, outreach, ad spend or experiment execution.

[中文完整说明](README.md) · [Contribution guide](CONTRIBUTING.md) · [Known release limits](docs/RELEASE_READINESS.md) · [MIT](LICENSE)
