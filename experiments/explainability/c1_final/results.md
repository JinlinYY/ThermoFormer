# C1 final ThermoFormer interpretability

解释对象为最终 **C1 RDKit + Uni-Mol v2 + functional groups + vanilla Transformer**，并使用每个 seed 经验证集选择后的最终 checkpoint。分析仅覆盖 `overall_binary_ternary` 测试集。

五个 checkpoint 的选择为：seed 0: stage2, seed 1: stage1, seed 2: stage2, seed 3: stage2, seed 4: stage1。
Grouped Shapley 使用各 seed 训练集的视图均值作为背景，将三类分子视图视为三个特征组；分析在观测 T、P、x 状态上解释模型内部热力学输出，因此属于 teacher-forced model attribution。

## Molecular-view contributions

| Explained output | Molecular view | Mean | SD | Normalized share |
|---|---|---:|---:|---:|
| $G^E/RT$ | Functional groups | 0.02992 | 0.001676 | 24.6% |
| $G^E/RT$ | RDKit descriptors | 0.077514 | 0.02415 | 63.6% |
| $G^E/RT$ | Uni-Mol v2 | 0.014415 | 0.002703 | 11.8% |
| mean $|\ln\alpha|$ | Functional groups | 0.39347 | 0.03312 | 32.5% |
| mean $|\ln\alpha|$ | RDKit descriptors | 0.72594 | 0.1934 | 60.0% |
| mean $|\ln\alpha|$ | Uni-Mol v2 | 0.091412 | 0.03568 | 7.5% |
| mean $|\ln\gamma|$ | Functional groups | 0.063143 | 0.007034 | 22.5% |
| mean $|\ln\gamma|$ | RDKit descriptors | 0.18459 | 0.04337 | 65.6% |
| mean $|\ln\gamma|$ | Uni-Mol v2 | 0.033504 | 0.007725 | 11.9% |
| mean $|I_{ij}|$ | Functional groups | 0.15982 | 0.01395 | 22.3% |
| mean $|I_{ij}|$ | RDKit descriptors | 0.46676 | 0.1197 | 65.2% |
| mean $|I_{ij}|$ | Uni-Mol v2 | 0.089486 | 0.02154 | 12.5% |

按 mean |Shapley|，各输出的最大贡献视图为：$G^E/RT$—**RDKit descriptors**；mean $|\ln\alpha|$—**RDKit descriptors**；mean $|\ln\gamma|$—**RDKit descriptors**；mean $|I_{ij}|$—**RDKit descriptors**。这说明三视图贡献可量化，但不能把归因值解释为因果化学机制。
本分析包含 **1073** 个 seed-state 解释实例；RDKit 在四类输出上均为 **5/5** 个 seed 的首位视图。
精确三组 Shapley 的最大加和误差为 `5.96e-07`。

## Pair interaction and thermodynamic sensitivity

`pair_potential` 的 |Iij| 与同状态 mean |lnγ| 的 seed-wise Spearman 相关为 **0.6539 ± 0.141**。它是模型内部 decoder interaction，不是实验测得的键能或相互作用能。
- 2组分代表状态：组成闭合方向响应 RMS `0.6365 ± 0.144`；温度响应 RMS `7.004e-05 ± 4.08e-05` K⁻¹。
- 3组分代表状态：组成闭合方向响应 RMS `0.6119 ± 0.317`；温度响应 RMS `5.802e-05 ± 3.24e-05` K⁻¹。

## Interpretation

1. 三类视图通过独立 projection 和融合共同影响热力学输出；归因结果回答“模型依赖什么”，不回答“分子为何真实相互作用”。
2. Pair potential 与活度非理想性之间的相关只支持 decoder 内部一致性，不能单独证明氢键、络合或共沸机理。
3. 闭单纯形导数保持 Σx=1，因而比直接对独立 x 分量求导更符合组成变量约束。
4. 解释使用五个验证集选择 checkpoint 汇总，避免以单一随机种子下结论。

## Reproducibility

- Grouped Shapley values: `analysis/interpretability_c1_final/results/modality_shapley.csv`
- Pair interactions: `analysis/interpretability_c1_final/results/pair_interactions.csv`
- Thermodynamic sensitivities: `analysis/interpretability_c1_final/results/thermodynamic_sensitivity.csv`
- Figure: `analysis/interpretability_c1_final/figures/Figure_c1_interpretability.{png,pdf,svg}`
