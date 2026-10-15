# Ternary training → ternary test

VLE / Predictive benchmarks

Supervised initialization followed by three thermodynamic training stages. Both isothermal and isobaric evaluation. Backend regenerates registered VLE splits; formal provenance checks still apply.

## Protocol and results

Configuration: `configs/vle/prediction/ternary.json`.

- [experiments/vle/training_records/v1/three/results/thermoformer_vle_three_stage.on.vle_overall_ternary](../../training_records/v1/three/results/thermoformer_vle_three_stage.on.vle_overall_ternary)
- [datasets/splits/vle/vle_overall_ternary](../../../../datasets/splits/vle/vle_overall_ternary)
- [models/vle/prediction/vle_overall_ternary](../../../../models/vle/prediction/vle_overall_ternary)

Inspect the command with `python scripts/run_experiments.py show vle.prediction.ternary`.
