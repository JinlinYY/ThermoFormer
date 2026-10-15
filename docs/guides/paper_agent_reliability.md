# Paper-agent reliability release

The S8 protocol and its complete output records are released under
[`experiments/supporting_information/s8_agent_reliability/`](../../experiments/supporting_information/s8_agent_reliability/).
The final v3 batch contains 72 requests (15 equivalent and 9 challenge prompts per case, repeated
three times) and preserves raw runs, numerical evidence, reports, source hashes, and audit data.

Use [`scripts/benchmarks/paper_agent/`](../../scripts/benchmarks/paper_agent/) to inspect the
task definitions and audit an existing batch. Live reruns require the configured model endpoint;
keep credentials outside the repository. The reliability batch checks orchestration, deterministic
input gates, evidence binding, and agreement with the frozen paper protocols. It does not claim
that an LLM can safely answer arbitrary thermodynamics questions without the deterministic
`thermo_engine` validation boundary.
