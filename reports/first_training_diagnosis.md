# First ThermoFormer training diagnosis

Date: 2026-08-21. Hardware: NVIDIA GeForce RTX 3090 Ti. Environment: `ggnn39`, Python 3.9.25, PyTorch 2.6.0+cu126, Uni-Mol v2 84M. Dataset/split: retained 11,014-row modeling set, `overall_binary_ternary/seed_0` (7,684 train / 1,660 validation / 1,670 test rows). These are **diagnostic single-seed pilots, not paper results**.

## Environment and data-path checks

- The real `unimol-tools` backend loaded `unimolv2.py` and the 84M checkpoint; all 138 SMILES received `cls_repr` vectors.
- Conformer generation reported one 3D fallback for the single-atom SMILES `O`; representation generation still completed. The cache is `cache/unimolv2_84m.npz` and is reused by all subsequent runs.
- The initial GPU attempt correctly failed before training because deterministic PyTorch operations lacked `CUBLAS_WORKSPACE_CONFIG`. The unified seed setup now defines `:4096:8` before CUDA work.
- A second reproducibility issue was found: cache-miss Uni-Mol inference consumed RNG state before ThermoFormer initialization. The runner now reseeds immediately after feature extraction. Two repeated runs then produced byte-identical metric JSON SHA-256 values.
- No NaN/Inf loss or gradient was observed. Non-finite values remain hard failures.

## Pilot A: 2 supervised + 1 physics epoch

Purpose: execution, memory, gradient and solver smoke test.

- Training time: 7.26 s; peak allocated GPU memory: 474.35 MiB; trainable ThermoFormer parameters: 1,780,419.
- Supervised epoch 1 validation objective: 0.6389; epoch 2: 0.7247. The epoch-1 checkpoint was retained.
- The physics epoch validation objective was 1.0802 and was rejected, proving that physics fine-tuning can no longer overwrite a better supervised checkpoint.
- Pre-clipping gradient norms were mean/max 20.6/82.3 (supervised epoch 1), 46.8/127.6 (supervised epoch 2), and 71.8/803.4 (physics). All updates were clipped at the configured norm 5.
- With only eight evaluation iterations, the isothermal solver converged on essentially none of the rows. An iteration sensitivity check gave isothermal coverage 0.5% / 54.3% / 100% at 8 / 16 / 24 iterations for this checkpoint; 24 and 48 iterations produced the same converged predictions to numerical precision. This confirms iteration truncation, not nonphysical output, caused the early failures.

## Pilot B: 20 supervised + 5 physics epochs, original physics scaling

Configuration: common learning rate `2e-4`, continuity weight `1e-3`, one solver batch/epoch, eight training-solver iterations.

- Training time: 48.17 s; peak allocated GPU memory: 969.75 MiB.
- Best supervised validation objective: 0.1667 at epoch 18.
- Physics validation did not improve on 0.1667 and the supervised checkpoint was restored.
- The first physics epoch had raw continuity 655 and pre-clipping gradient maximum 4,784.8. The continuity contribution dominated the intended small fine-tuning step.

Verdict: the two-stage control flow was correct, but the original physical-stage scale was not a credible fine-tuning regime.

## Pilot C: 20 supervised + 5 physics epochs, balanced fine-tuning

Configuration: supervised learning rate `2e-4`, physics learning rate `2e-5`, continuity weight `1e-5`, one solver batch/epoch, eight training-solver iterations, 48 evaluation iterations.

- Training time: 48.11 s; peak allocated GPU memory: 969.75 MiB.
- Best supervised validation objective remained 0.1667.
- Physics epoch 4 achieved 0.1519, an 8.9% reduction in the common experimental validation objective, so that checkpoint was accepted. Epoch 5 worsened to 0.1931 and was rejected.
- Physics pre-clipping gradient maxima across epochs were 93.7, 89.7, 72.8, 63.8 and 120.0—still clipped, but no longer several orders larger than the supervised regime.
- All 1,676 requested test-direction solves converged at 48 iterations; nonphysical rate was 0%.

For context only, the accepted diagnostic checkpoint produced P/T/y point-wise MAE of 17.03 kPa / 9.40 K / 0.0937. Relative to the supervised-only checkpoint evaluated at the same 48 iterations, T and y improved (10.82→9.40 K and 0.0983→0.0937), while P MAE slightly worsened (16.44→17.03 kPa). This single seed does not support a superiority claim; it supports the feasibility and safety of the staged procedure.

## Decisions for formal runs

1. Keep the user's intended strategy: supervised training followed by a short physics fine-tune.
2. Use independent learning rates: `2e-4` supervised and `2e-5` physics.
3. Use continuity weight `1e-5`; keep solver and boundary terms configurable for later ablation.
4. Use 48 evaluation iterations. Report coverage/failure/nonphysical rates even when they are zero.
5. Treat 80 supervised epochs as a maximum and use validation patience 12 (minimum 10 epochs). Use at most five physics epochs with the supervised checkpoint as the epoch-0 candidate.
6. Preserve gradient clipping at norm 5 and record pre-clipping mean/max norms in every training curve.
7. Do not claim a physics-loss benefit until five-seed ablation confirms it. Pilot C is a hyperparameter diagnosis, not confirmatory evidence.
