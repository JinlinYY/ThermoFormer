# ThermoFormer implementation changes

This log records changes made in response to the paper-grade audit request. It distinguishes corrective implementation work from scientific results.

## 2026-08-21

### Corrected validation selection across the two training stages

- Added a regression test showing that the previous implementation accepted a worse physics-fine-tuned checkpoint.
- Changed `src/training.py` so supervised and physics epochs are monitored with the same experimental validation objective.
- Initialized physics-stage selection from the best supervised validation value/state. Physics fine-tuning is now accepted only when it improves that criterion; otherwise the supervised checkpoint is restored.

### Added stable chemical/state identities and persisted split artifacts

- Added `src/splits.py` with RDKit canonical isomeric SMILES, order-invariant component/system/state IDs and a full modeling-dataset SHA-256 digest.
- Added atomic JSON split writing and strict reload validation. Dataset drift, unknown rows, duplicate IDs and train/validation/test overlap are hard failures.
- Added `rdkit` to the declared project requirements; the configured `ggnn39` environment currently provides RDKit 2025.03.5.
- Added tests for A–B/B–A invariance, exact round-trip reuse, overlap rejection and dataset-digest mismatch.

### Added reproducible data-audit artifacts

- Added `src/auditing.py` and `scripts/audit_dataset.py`.
- Generated `reports/data_audit.md`, `reports/data_audit.json` and `reports/ternary_binary_subsystem_coverage.csv` from the same loader and filtering rules used by training.
- Recorded the complete row ledger, cardinality/system/component coverage, state ranges, quality/mode/DOI summaries, pure-anchor coverage, canonical identity checks and ternary binary-subsystem categories.

### Stabilized deterministic GPU execution and two-stage fine-tuning

- Set `CUBLAS_WORKSPACE_CONFIG=:4096:8` in the common seed entry point before CUDA operations; this fixes deterministic Uni-Mol v2 execution under PyTorch 2.6.
- Reseed immediately after Uni-Mol feature extraction so cache-hit and cache-miss runs initialize ThermoFormer identically. Repeated smoke metrics are byte-identical.
- Added independent `physics_learning_rate` (`2e-5`), reduced the default continuity weight to `1e-5` based on controlled pilot diagnostics, and increased evaluation solver iterations to 48.
- Added validation early stopping (patience 12, minimum 10 supervised epochs) while retaining 80/5 as maximum supervised/physics epochs.
- Added pre-clipping gradient mean/max values to every training epoch record.
- Used a separate single-seed pilot to freeze optimization settings before formal evaluation; the final `reports/first_training_diagnosis.md` now reports the complete five-seed experiment suite.

### Added complete paper experiment protocols and evaluation

- Generated and round-trip validated 75 split artifacts (15 protocols × seeds 0–4) under `splits/`, with zero row overlap, zero strict-state boundary violations, zero stale binary-subsystem coverage labels, and zero unanchored training components. The nominal 1% ternary-scaling point was removed because it selected exactly the same one system as 5%; the retained 5% point records its realized 1/18 = 5.56% fraction.
- Reserved complete pure-endpoint reference systems for state protocols; those calibration systems are train-only and excluded from strict mixture-state validation/test metrics. This prevents endpoint rows from crossing a state boundary and prevents one reference mixture from appearing in both train and validation.
- Added unseen-component holdouts with no train/test component leakage and both binary/ternary test coverage; strict all-components-unseen sample IDs are saved.
- Added binary-to-ternary zero-shot and 5/10/25/50/100% scaling protocols. The zero-shot 0% endpoint and every positive fraction share the exact held-out ternary test systems within each seed; zero-shot model selection remains binary-only. Test sets include both experimental directions, and binary-subsystem coverage is computed from the actual binary training partition, never from validation/test-only binaries.
- Added row-level solver prediction export and point/system/component-macro metrics with explicit coverage/failure/nonphysical denominators.
- Added single-seed runner, five-seed suite, strict seed aggregator, experiment configs and per-experiment command/result records.

### Hardened formal-run provenance and failure behavior

- Formal runs now require every inherited config, split, dataset workbook and optional pure-property catalog to be inside the project and tracked by Git; split protocol names are validated before entering output paths.
- The runner records SHA-256 hashes for the resolved experiment definition, split, full feature cache, exact Uni-Mol feature subset, resolved runtime environment and every material output artifact, plus CPU/GPU, CUDA/cuDNN and NumPy/RDKit/Uni-Mol/PyTorch versions.
- A seed start first invalidates both formal and diagnostic protocol-level aggregate manifests, then replaces the seed completion marker with `running`; an interrupted job therefore cannot retain any old valid summary or seed status while partially replacing artifacts.
- Resume checks reject stale Git/config/split/cache/environment fingerprints. Formal aggregation requires exactly seeds 0–4 and rejects duplicate metric scopes, mixed training provenance, any missing/changed material artifact and all non-finite metrics. Global and component-cardinality headline scopes must cover all five seeds; finer direction/cardinality strata, or a specific observable inside an otherwise complete scope, may be absent when a split contains no such samples. Each summary field records the exact contributing seed IDs instead of fabricating values or suppressing the available measurements. The aggregate manifest distinguishes the training-code commit from the clean post-processing commit. A single atomic aggregate manifest is invalidated before replacement and marked complete only after both tables and their hashes are committed; partial-seed summaries are isolated under `diagnostic_*` names.
- Both suite and single-experiment smoke commands automatically redirect runs, checkpoints, results and aggregate markers below `runs/*_smoke/`; they cannot overwrite or block formal artifacts by default.

### Completed formal training and paper outputs

- Completed 15 registered protocols with seeds 0–4 (75 formal runs) in `ggnn39`; every seed includes a best checkpoint, history, curves, predictions, metrics, resolved configuration and cryptographic provenance. All protocol aggregate manifests are `completed`.
- Added `src/paper_outputs.py` and `scripts/build_paper_outputs.py` to generate the requested performance/generalization tables, parity/error plots, difficulty ladder, state-distance plots, binary-to-ternary transfer figure, formal diagnosis and experiment result pages from validated aggregates.
- Generated PDF, SVG and 600-dpi PNG figures plus machine-readable CSV tables. The reports retain non-monotonic ternary scaling, sparse direction-specific measurements, solver failures and unseen-component degradation rather than filtering or smoothing them away.
- Activity-coefficient error is deliberately omitted from confirmatory claims because the workbooks do not provide a complete independent trusted pure-property reference for experimental inversion. The scope remains binary/ternary VLE below 500 kPa; no quaternary result is claimed.
- Expanded every formal report and experiment result page from MAE-only summaries to separate point-wise MAE, RMSE and R² tables for pressure, temperature and vapor composition. Each aggregate value records its actual contributing seed count; system-macro and component-macro fields remain available in the machine-readable CSV files.
