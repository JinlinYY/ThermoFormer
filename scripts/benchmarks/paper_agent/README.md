# Paper-agent reliability runner

The Python files in this directory are the frozen task definitions, runner, report generator, and
audit utility used to produce the S8 reliability records. They were copied from the source tree
under `D:\VLE` so that the public repository contains the protocol alongside its results.

The final records are in [`experiments/supporting_information/s8_agent_reliability/results/reliability-20260926-v3/`](../../../experiments/supporting_information/s8_agent_reliability/results/reliability-20260926-v3/).
The runner uses the backend implementation under `Web/ThermoFormer-web/backend/` and a configured
DeepSeek endpoint; it is therefore an archival reproduction entry point rather than a zero-config
offline test. Do not place API keys in source files or output directories.

For a local audit of an existing batch, use:

```powershell
python scripts/benchmarks/paper_agent/audit_reliability.py <batch-directory>
```

The batch itself remains the authoritative record of the exact command-line options, source
hashes, prompts, responses, and evidence bindings used for the paper-aligned run.
