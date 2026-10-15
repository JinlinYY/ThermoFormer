# Agent reliability experiment: results and reproduction record

Completed 72/72 scheduled requests. Model(s): deepseek-flash.

This is a development pilot over three known chemical systems: 15 equivalent requests and 9 input challenges, each repeated independently three times at temperature 0. Repeated runs are not independent design tasks.

|Case|Task compilation|Tool plan|Tool execution*|Result consistency*|Grounded report|LLM clarification|System blocks invalid|
|---|---:|---:|---:|---:|---:|---:|---:|
|Binary distillation|15/15|15/15|15/15|15/15|1/15|3/9|9/9|
|Extractive distillation|7/15|15/15|7/15|7/15|7/15|9/9|9/9|
|Crossflow extraction|14/15|15/15|14/15|14/15|12/15|9/9|9/9|

*First matching contract invokes fresh ThermoFormer/process calculations. Later matches reuse the same hashed numerical artifact. Cached equivalence is a routing/reproducibility check, not independent numerical validation or repeated model inference.

## Paper result checks

- Extractive distillation: agreement=True; tolerance: 2e-6 absolute mole/recovery fractions AND identical unrounded threshold decisions.
- Crossflow extraction: agreement=True; tolerance: 1e-7 absolute recovery/retention fractions and identical stage selection.
- Binary distillation: agreement=True; tolerance: exact integer stages and feed location.

Unrounded extractive-column targets are checked separately from floating-point agreement. Original scientific source files, weights, and archived paper outputs are not overwritten.

## Interpretation

Task compilation includes deterministic unit conversion and source/applicability checks. LLM clarification is scored on its raw status, issue type and named field; system blocking is separate. Grounding is scored on the LLM's raw structured claims before the output gate. Reports use a constrained claim catalog and evidence IDs; this does not measure unrestricted prose hallucination.

No fixed/rule/LLM search competition, new process optimization, held-out molecular generalization, independent process experiments, or DWSIM certification is claimed. Reference agreement does not establish physical accuracy or global phase stability.

Provider calls: 108; provider-reported total tokens: 171842.

See evaluation.csv, runs.csv and repeats.csv for denominators, time, tokens and cache counts. See summary.json for all failures (including empty lists), manifest.json for pre-run inputs and hashes, source_integrity.json for the end-of-run integrity check, runs/ for exact requests/responses/tool provenance, and numerical/ for complete solver observations.

## Reproduce (PowerShell)

```powershell
& E:/anaconda/envs/ggnn39/python.exe -m benchmarks.paper_agent.reliability_run --output outputs/paper_agent/reliability-new --repeats 3
& E:/anaconda/envs/ggnn39/python.exe -m benchmarks.paper_agent.reliability_report --input outputs/paper_agent/reliability-new
```
