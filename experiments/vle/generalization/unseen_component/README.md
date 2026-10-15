# Unseen components

VLE / Generalization and extrapolation

Supervised initialization followed by three thermodynamic training stages. Both isothermal and isobaric evaluation. Backend regenerates registered VLE splits; formal provenance checks still apply.

## Protocol and results

Configuration: `configs/vle/generalization/unseen_component.json`.

- [experiments/vle/training_records/v1/three/results/thermoformer_vle_three_stage.on.vle_binary_unseen_component](../../training_records/v1/three/results/thermoformer_vle_three_stage.on.vle_binary_unseen_component)
- [datasets/splits/vle/vle_binary_unseen_component](../../../../datasets/splits/vle/vle_binary_unseen_component)
- [models/vle/generalization/vle_binary_unseen_component](../../../../models/vle/generalization/vle_binary_unseen_component)

Inspect the command with `python scripts/run_experiments.py show vle.generalization.unseen_component`.
