# Ablation experiments

The formal paper campaign is organized by the scientific claim being tested:

- [`architecture/`](architecture/): A0--A6, including RDKit, independent,
  pairwise-only, concatenation, direct-activity, and direct-VLE controls;
- [`thermodynamic_constraint/`](thermodynamic_constraint/): P3, P4, and P6
  removable soft-constraint controls. P1 reuses A5; P2/P5 are hard guarantees
  and are explicitly marked not applicable.

Every formal variant inherits the locked Full configuration and changes only its
declared switch or loss weight. The campaign uses the main splits, preprocessing,
seeds 0--4, training budget, and validation-only model selection. Run it with
`scripts/run_ablation_suite.py`; definitions are frozen in
`configs/ablation/full_model_reference.yaml` and `reports/constraint_audit.md`.

The older [`component/`](component/README.md) and
[`thermodynamic_loss/`](thermodynamic_loss/README.md) directories are preliminary
diagnostic templates. They are not inputs to the formal ablation tables.
