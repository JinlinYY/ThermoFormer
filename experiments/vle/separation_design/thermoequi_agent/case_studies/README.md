# Agent-assisted separation design with ThermoFormer

SEPARATION_DESIGN / Agent-assisted separation design

The bundled ThermoAgent reproduces the three reported deterministic numerical case studies from archived equilibrium states. Fresh model evaluation is available through the registered checkpoints. LLM orchestration and external DWSIM integration remain optional integration layers.

## Protocol and results

Configuration: `configs/separation_design/autonomous/thermoequi_agent.json`.

- [ThermoAgent/cases](../../../../../ThermoAgent/cases)
- [experiments/supporting_information/s7_separation_design](../../../../supporting_information/s7_separation_design)
- [experiments/supporting_information/s8_agent_reliability](../../../../supporting_information/s8_agent_reliability)

Inspect the command with `python scripts/run_experiments.py show separation_design.thermoequi_agent.case_studies`.
