# S8 agent reliability

Final experiment records and source data for manuscript Section 2.2, Fig. 3, and SI S8.

| Test | Final records | Scope |
|---|---|---|
| Equivalent requests and invalid inputs | `results/reliability-20260926-v3/` | 45 valid and 27 challenged interactions; 3 fresh numerical executions, 42 cache reuses |
| Paired schema/contract replay | `results/evidence_interventions/paired_routing_replay.json` | Same LLM outputs; 18/27 schema blocks and 27/27 full-contract blocks |
| Clarification recovery | `results/evidence_interventions/recovery/` | 27/27 task reconstructions, cached-result retrievals, evidence-linked reports |
| Evidence decisions | `results/evidence_interventions/decisions/` | 27 initial decisions and 9 follow-up decisions after restored evidence |
| Figure and per-panel source tables | `figures/` and `figures/source_data/` | Final six-panel agent figure and source CSVs |

The three systems and scripted corrections are predefined. Repeats do not increase
the number of independent chemical systems, and these tests do not establish
held-out molecular generalization. The report catalog constrains claims to registered
evidence. Numerical validation, experimental support, and global phase stability are
separate evidence levels.

## Inspect or reproduce

Install the scientific environment and `pydantic>=2.10,<3`, `httpx>=0.28,<1`,
and `python-dotenv>=1,<2` for the agent command-line tools. Live reruns require the
`DEEPSEEK_API_KEY` environment variable and the endpoint/model configuration in
`Web/ThermoFormer-web/backend/paper_agent/policy.py`.

```powershell
python scripts/benchmarks/paper_agent/audit_reliability.py --input experiments/supporting_information/s8_agent_reliability/results/reliability-20260926-v3
python scripts/benchmarks/paper_agent/reliability_run.py --output outputs/reliability --repeats 3
python scripts/benchmarks/paper_agent/main_figure_experiment.py --source outputs/reliability --output outputs/evidence_interventions
python scripts/benchmarks/paper_agent/agent_publication_figure.py --reliability experiments/supporting_information/s8_agent_reliability/results/reliability-20260926-v3 --experiment experiments/supporting_information/s8_agent_reliability/results/evidence_interventions --output outputs/agent_figure
```

The audit reads existing records without API calls. New runs must use new output
directories. Exact LLM outputs and costs may vary with provider implementation;
the released final records remain available for offline inspection.
