"""Evidence-bounded narrative report for ThermoFormer interpretation."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from .analysis import InterpretabilityContext


def _fmt(value: float, digits: int = 3) -> str:
    return "not available" if not math.isfinite(value) else f"{value:.{digits}g}"


def _seedwise_spearman(
    frame: pd.DataFrame,
    first: str,
    second: str,
) -> tuple[float, float, int]:
    values = []
    for _, rows in frame.groupby("seed"):
        if rows[first].nunique() > 1 and rows[second].nunique() > 1:
            value = stats.spearmanr(rows[first], rows[second]).statistic
            if np.isfinite(value):
                values.append(float(value))
    return (
        float(np.mean(values)) if values else math.nan,
        float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
        len(values),
    )


def write_interpretability_report(
    path: Path,
    context: InterpretabilityContext,
    attribution: pd.DataFrame,
    composition: pd.DataFrame,
    sensitivity: pd.DataFrame,
    manybody: pd.DataFrame,
) -> None:
    pair_mask = _seedwise_spearman(
        attribution, "absolute_pair_potential", "mean_pair_mask_delta_y"
    )
    pair_mask_gamma = _seedwise_spearman(
        attribution, "absolute_pair_potential", "mean_pair_mask_delta_log_gamma"
    )
    pair_gamma = _seedwise_spearman(
        attribution, "absolute_pair_potential", "mean_abs_log_gamma"
    )
    pair_alpha = _seedwise_spearman(
        attribution,
        "absolute_pair_potential",
        "mean_abs_log_relative_volatility_shift",
    )
    pair_ideality = _seedwise_spearman(
        attribution, "absolute_pair_potential", "vle_deviation_from_ideality"
    )

    representative = attribution.loc[
        attribution["representative_categories"].fillna("").ne("")
        & attribution["seed"].eq(context.best_seed)
    ].copy()
    representative["category"] = representative["representative_categories"].str.split("; ")
    representative = representative.explode("category")
    representative_summary = representative.groupby("category", as_index=False).agg(
        systems=("system_id", "nunique"),
        states=("sample_id", "nunique"),
        pair_potential=("absolute_pair_potential", "mean"),
        mask_delta_y=("mean_pair_mask_delta_y", "mean"),
        abs_log_gamma=("mean_abs_log_gamma", "mean"),
        ideality_delta=("vle_deviation_from_ideality", "mean"),
    )

    trajectory_rows = []
    isothermal_composition = composition.loc[composition["direction"].eq("isothermal")]
    for (category, system), rows in isothermal_composition.groupby(["category", "system_id"]):
        rows = rows.sort_values("x_1")
        steps = np.sqrt(
            np.diff(rows["latent_pc1"]) ** 2 + np.diff(rows["latent_pc2"]) ** 2
        )
        abs_gamma = 0.5 * (
            rows["log_gamma_1"].abs() + rows["log_gamma_2"].abs()
        )
        rho_gamma = stats.spearmanr(
            rows["latent_nonideality_ge_rt"], abs_gamma
        ).statistic
        rho_alpha = stats.spearmanr(
            rows["latent_nonideality_ge_rt"],
            np.log(rows["relative_volatility_12"].clip(lower=1e-12)),
        ).statistic
        trajectory_rows.append(
            {
                "category": category,
                "system_id": system,
                "max_step": float(np.max(steps)),
                "median_step": float(np.median(steps)),
                "rho_gamma": float(rho_gamma),
                "rho_alpha": float(rho_alpha),
            }
        )
    trajectories = pd.DataFrame(trajectory_rows)
    azeotrope = isothermal_composition.loc[
        isothermal_composition["category"].str.contains(
            "experimental azeotrope proxy", regex=False
        )
    ].sort_values("x_1")
    predicted_azeotrope = azeotrope.iloc[
        np.argmin(np.abs(np.log(azeotrope["relative_volatility_12"].clip(lower=1e-12))))
    ]
    experimental_azeotrope = float(
        azeotrope["experimental_azeotrope_x1"].dropna().iloc[0]
    )

    experimental = manybody.loc[manybody["record_type"].eq("experimental_test")].copy()
    paired = experimental.groupby(
        ["seed", "system_id", "chemical_family", "direction"], as_index=False
    ).agg(
        full_y_mae=("full_y_mae", "mean"),
        pairwise_y_mae=("pairwise_y_mae", "mean"),
        full_state_mae=("full_state_abs_error", "mean"),
        pairwise_state_mae=("pairwise_state_abs_error", "mean"),
    )
    paired["delta_y"] = paired["pairwise_y_mae"] - paired["full_y_mae"]
    paired["delta_state"] = paired["pairwise_state_mae"] - paired["full_state_mae"]
    aggregate_count = len(paired)
    positive_rate = 100.0 * float(np.mean(paired["delta_y"] > 0.0))
    wilcoxon_y = (
        float(stats.wilcoxon(paired["delta_y"]).pvalue)
        if np.any(np.abs(paired["delta_y"].to_numpy()) > 0.0)
        else 1.0
    )
    family = paired.groupby("chemical_family", as_index=False).agg(
        systems=("system_id", "nunique"),
        delta_y=("delta_y", "mean"),
        delta_state=("delta_state", "mean"),
    )
    simplex = manybody.loc[manybody["record_type"].eq("simplex_scan")]
    strongest = simplex.iloc[int(simplex["manybody_y_l1"].argmax())]
    third_path = manybody.loc[manybody["record_type"].eq("third_component_path")].sort_values(
        "third_component_fraction"
    )
    third_boundary = third_path.iloc[0]
    third_endpoint = third_path.iloc[-1]

    ternary_sensitivity = sensitivity.loc[
        sensitivity["category"].eq("complete-subsystem ternary")
    ]
    full_matrix = ternary_sensitivity.loc[ternary_sensitivity["model"].eq("full")].pivot(
        index="affected_component",
        columns="increased_component",
        values="d_log_gamma_i_d_closed_x_j",
    )
    pair_matrix = ternary_sensitivity.loc[
        ternary_sensitivity["model"].eq("pairwise-only")
    ].pivot(
        index="affected_component",
        columns="increased_component",
        values="d_log_gamma_i_d_closed_x_j",
    )
    matrix_difference = float(np.linalg.norm(full_matrix.to_numpy() - pair_matrix.to_numpy()))
    ternary_components = (
        ternary_sensitivity[
            ["affected_component", "affected_name", "affected_smiles"]
        ]
        .drop_duplicates()
        .sort_values("affected_component")
    )
    component_names = ternary_components["affected_name"].tolist()
    full_third_response = full_matrix.loc[:, 3].to_numpy()
    pair_third_response = pair_matrix.loc[:, 3].to_numpy()
    largest_response = sensitivity.iloc[
        int(sensitivity["d_log_gamma_i_d_closed_x_j"].abs().argmax())
    ]

    target_dmso = tuple(sorted(("COC(=O)C", "CO", "CS(=O)C")))
    dmso_present = any(sample.system_key == target_dmso for sample in context.samples)

    lines = [
        "# ThermoFormer Interpretability: Learned Multicomponent Thermodynamics",
        "",
        "This report interprets the locked full ThermoFormer and pairwise-only ablation. "
        "The full latent analysis uses the seed selected solely by minimum validation loss; "
        "attribution and full-versus-pairwise test statistics retain seeds 0–4. No test metric "
        "was used to choose a checkpoint.",
        "",
        "## Scope and safeguards",
        "",
        f"- Validation-selected full-model seed: **{context.best_seed}** "
        f"(validation loss {_fmt(context.full.best_validation_loss, 5)}).",
        f"- Matching pairwise-only seed: **{context.best_seed}** "
        f"(validation loss {_fmt(context.pairwise.best_validation_loss, 5)}).",
        "- `pair_interactions` is the learned scalar pair potential used inside the excess-Gibbs decoder. "
        "It is not called a physical bond strength or mechanism. Mean-training-token masking is an "
        "independent perturbation cross-check, but remains an embedding-space intervention.",
        "- Latent PCA coordinates are descriptive axes from one checkpoint. Raw latent coordinates are "
        "not compared across independently trained seeds because those spaces are not identifiable.",
        "- All selected molecular systems are held-out test systems for the selected seed.",
        "",
        "## Molecular interaction attribution across chemical environments",
        "",
        r"| Representative environment | Test states | Mean $|h_{ij}|$ | Mean masking Δy | Mean $|\ln \gamma|$ | Mean nonideal−ideal Δy |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in representative_summary.iterrows():
        lines.append(
            f"| {row['category']} | {int(row['states'])} | {_fmt(row['pair_potential'])} | "
            f"{_fmt(row['mask_delta_y'])} | {_fmt(row['abs_log_gamma'])} | "
            f"{_fmt(row['ideality_delta'])} |"
        )
    lines += [
        "",
        "Across the complete test attribution table, seed-wise Spearman correlations "
        f"(mean ± SD across n={pair_mask[2]} seeds) are: |h_ij| versus masking Δy "
        f"**{_fmt(pair_mask[0])} ± {_fmt(pair_mask[1])}**; versus |ln γ| "
        f"**{_fmt(pair_gamma[0])} ± {_fmt(pair_gamma[1])}**; versus the activity contribution "
        f"to log relative volatility **{_fmt(pair_alpha[0])} ± {_fmt(pair_alpha[1])}**; and "
        f"versus nonideal−ideal vapor shift **{_fmt(pair_ideality[0])} ± {_fmt(pair_ideality[1])}**.",
        f"The corresponding |h_ij| versus masking Δlnγ correlation is "
        f"**{_fmt(pair_mask_gamma[0])} ± {_fmt(pair_mask_gamma[1])}**.",
        "",
        "The pair potential tracks thermodynamic nonideality, but the independent masking response is "
        "essentially uncorrelated and the masking−log-gamma association is seed dependent. Therefore "
        "the perturbation experiment does **not** validate h_ij as a causal molecular-interaction "
        "attribution. It remains a decoder-internal thermodynamic signal, not a measured interaction strength.",
        "",
        "The water/alcohol and experimental-azeotrope labels refer to the same held-out system and are "
        "not counted as independent chemical examples. The hydrocarbon label denotes the lowest-|gE| "
        "composition-complete hydrocarbon available in the selected test split; its residual nonideality "
        "is retained rather than calling it strictly ideal.",
        "",
        "## Composition-dependent evolution of molecular nonideality",
        "",
        "| Environment | Max latent PC step | Median step | ρ(gE, mean |lnγ|) | ρ(gE, ln α12) |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in trajectories.iterrows():
        lines.append(
            f"| {row['category']} | {_fmt(row['max_step'])} | {_fmt(row['median_step'])} | "
            f"{_fmt(row['rho_gamma'])} | {_fmt(row['rho_alpha'])} |"
        )
    lines += [
        "",
        "All trajectories were evaluated on the fixed x1=0.01–0.99 grid in both isothermal "
        "(predict P and y) and isobaric (predict T and y) directions; the table summarizes the "
        "isothermal path. Finite adjacent PC steps and smooth decoded observables show continuous "
        "composition response; correlation signs vary "
        "by chemistry, so one universal one-dimensional latent-to-volatility law is not claimed.",
        "",
        f"For the experimentally detected azeotrope proxy, the observed y1−x1 crossing is at "
        f"x1≈**{experimental_azeotrope:.3f}**. The model's closest α12=1 point is at "
        f"x1=**{float(predicted_azeotrope['x_1']):.3f}**. The local latent trajectory is shown "
        "without asserting that a bend or turning point is itself an azeotrope mechanism.",
        "",
        "## Thermodynamic response sensitivity",
        "",
        "Sensitivities are closed-simplex directional derivatives: increasing component j removes "
        "the same differential amount from all other components in proportion to their current fractions. "
        "This avoids reporting unconstrained derivatives that violate Σx=1.",
        "",
        f"The largest absolute response in the retained binary/ternary cases is "
        f"**{_fmt(abs(float(largest_response['d_log_gamma_i_d_closed_x_j'])))}** for "
        f"affected component {int(largest_response['affected_component'])} when component "
        f"{int(largest_response['increased_component'])} is increased in "
        f"`{largest_response['category']}`. For the representative ternary, the Frobenius norm "
        f"between Full and Pairwise-only sensitivity matrices is **{_fmt(matrix_difference)}**, "
        "quantifying how multicomponent context changes cross-component response.",
        "",
        f"For the representative ternary ({' / '.join(component_names)}), increasing component 3 "
        f"gives Full responses ({', '.join(_fmt(float(value)) for value in full_third_response)}) "
        f"for lnγ1–3, compared with Pairwise-only ({', '.join(_fmt(float(value)) for value in pair_third_response)}). "
        "The full multicomponent context mainly damps the pairwise-only response of components 2 and 3 "
        "in this case; this is a model response, not proof of a specific complex.",
        "",
        "## Binary-to-ternary many-body interaction effects",
        "",
        f"The analysis contains **{experimental['system_id'].nunique()}** distinct held-out ternary "
        "systems for which A-B, A-C, and B-C experimental systems all exist. Every eligible test row "
        "and every seed is retained.",
        "",
        f"Across {aggregate_count} seed/system/direction aggregates, Pairwise−Full vapor-composition MAE "
        f"has mean **{_fmt(float(paired['delta_y'].mean()))}**, median "
        f"**{_fmt(float(paired['delta_y'].median()))}**, and is positive in "
        f"**{positive_rate:.1f}%** of aggregates "
        f"(paired Wilcoxon p=**{wilcoxon_y:.3g}**). Positive means the full model is better; negative "
        "cases remain in the CSV and figure.",
        "",
        f"Only **{paired['seed'].nunique()}** seeds contain at least one eligible held-out ternary, and "
        f"the {aggregate_count} aggregate comparisons are low-powered. With p far above 0.05 and only "
        f"{positive_rate:.1f}% positive "
        "deltas, the current experiment does **not** demonstrate a stable Full-model advantage over "
        "Pairwise-only. It demonstrates composition-dependent corrections whose benefits are system specific.",
        "",
        "| Chemical-family stratum | Systems | Mean Δy error (Pair−Full) | Mean Δstate error (Pair−Full) |",
        "|---|---:|---:|---:|",
    ]
    for _, row in family.iterrows():
        lines.append(
            f"| {row['chemical_family']} | {int(row['systems'])} | {_fmt(row['delta_y'])} | "
            f"{_fmt(row['delta_state'])} |"
        )
    lines += [
        "",
        "The simplex panel uses the eligible held-out ternary with the richest measured composition "
        "coverage, not the largest Full-model improvement. Its strongest computed vapor correction is "
        f"Σ|Δy_i|=**{_fmt(float(strongest['manybody_y_l1']))}** at composition "
        f"({float(strongest['x_1']):.2f}, {float(strongest['x_2']):.2f}, "
        f"{float(strongest['x_3']):.2f}). Activity-coefficient and relative-volatility corrections "
        "for every simplex point are stored alongside the vapor correction.",
        "",
        "A separate path compares a true two-token A-B input with the three-token ternary boundary "
        "at x3=0, then raises the third-component fraction to "
        f"{float(third_endpoint['third_component_fraction']):.2f} while preserving the median measured "
        "A:B ratio. For the Full model, the ternary x3=0 context differs from the true binary input in "
        f"lnγ1, lnγ2, and lnα12 by "
        f"{_fmt(float(third_boundary['ternary_x3_zero_minus_binary_log_gamma_1_full']))}, "
        f"{_fmt(float(third_boundary['ternary_x3_zero_minus_binary_log_gamma_2_full']))}, and "
        f"{_fmt(float(third_boundary['ternary_x3_zero_minus_binary_log_alpha_12_full']))}, respectively. "
        "At the endpoint, the Full model changes lnγ1 and lnγ2 relative to the true binary "
        f"values by {_fmt(float(third_endpoint['delta_log_gamma_1_from_true_binary_full']))} and "
        f"{_fmt(float(third_endpoint['delta_log_gamma_2_from_true_binary_full']))}; its lnα12 change is "
        f"{_fmt(float(third_endpoint['delta_log_alpha_12_from_true_binary_full']))}. The table also "
        "contains the corresponding Pairwise-only path and all α12, α13, and α23 corrections.",
        "",
        "## Optional methyl acetate + methanol + DMSO case",
        "",
        (
            "The exact ternary is present and can be interpreted without adding it to model training."
            if dmso_present
            else "The exact methyl acetate + methanol + DMSO ternary is absent from the current retained dataset; no mechanism result is fabricated."
        ),
        "",
        "## Answers to the manuscript questions",
        "",
        "1. **Different interaction patterns:** chemistry-stratified pair potentials differ, but weak "
        "masking agreement prevents treating those differences as validated causal interaction attributions.",
        "2. **Continuous latent nonideality:** all selected x scans yield continuous latent and decoded "
        "trajectories, with no discrete state jumps.",
        "3. **Thermodynamic correspondence:** latent gE/RT is associated with activity and volatility "
        "responses, but the direction and monotonicity are chemistry dependent.",
        "4. **Third-component response:** the closed-simplex sensitivity matrix and true-binary-to-"
        "ternary path quantify both the context discontinuity at x3=0 and subsequent changes in "
        "lnγ1, lnγ2, and α12 as component 3 is added.",
        f"5. **Stable Full-model advantage:** not supported by the present {aggregate_count} eligible "
        f"aggregate comparisons ({positive_rate:.1f}% positive; Wilcoxon p reported above).",
        "6. **Mechanistic interpretation:** the evidence supports model-level interaction hypotheses that "
        "can motivate experiments. It does not identify hydrogen bonds, complexes, or azeotrope mechanisms uniquely.",
        "",
        "## Reproducibility",
        "",
        "- Full table: `analysis/interpretability/results/interaction_attribution.csv`",
        "- Composition scans: `analysis/interpretability/results/composition_nonideality.csv`",
        "- Sensitivities: `analysis/interpretability/results/thermodynamic_sensitivity.csv`",
        "- Many-body comparisons: `analysis/interpretability/results/manybody_effects.csv`",
        "- Main figure: `analysis/interpretability/figures/Figure_interpretability.{pdf,svg,png}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
