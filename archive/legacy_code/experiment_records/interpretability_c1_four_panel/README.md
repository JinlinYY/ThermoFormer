# Final C1 explainability

This experiment explains the validation-selected final C1 workflow on
`overall_binary_ternary` across seeds 0--4. It uses exact grouped Shapley values
for RDKit descriptors, Uni-Mol v2 and SMARTS functional-group features, together
with decoder pair-interaction and closed-simplex thermodynamic sensitivity
analyses.

The three-view background is the corresponding seed's training-set mean. Model
outputs are evaluated at observed T, P and x, so the attribution is explicitly
teacher-forced. SHAP values describe model dependence and must not be interpreted
as causal molecular mechanisms or experimental interaction energies.

Run the formal experiment with the command in `run.md`. Use `--smoke` for an
isolated diagnostic run under `runs/interpretability_smoke/`; smoke artifacts do
not overwrite formal results.
