# Composition boundary extrapolation

VLE / Generalization and extrapolation

Supervised initialization followed by three thermodynamic training stages. Both isothermal and isobaric evaluation. Backend regenerates registered VLE splits; formal provenance checks still apply.

## Protocol and results

Configuration: `configs/vle/generalization/composition_edge.json`.

- [experiments/vle/training_records/v1/three/results/thermoformer_vle_three_stage.on.vle_binary_state_composition_edge_extrapolation](../../training_records/v1/three/results/thermoformer_vle_three_stage.on.vle_binary_state_composition_edge_extrapolation)
- [datasets/splits/vle/vle_binary_state_composition_edge_extrapolation](../../../../datasets/splits/vle/vle_binary_state_composition_edge_extrapolation)
- [models/vle/generalization/vle_binary_state_composition_edge_extrapolation](../../../../models/vle/generalization/vle_binary_state_composition_edge_extrapolation)

Inspect the command with `python scripts/run_experiments.py show vle.generalization.composition_edge`.
