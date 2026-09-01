"""Configurable error-budget model with precision vs accuracy split.

Classification: model-based simulation.
Non-literature numbers are engineering allocations, not evidence.
No silent favourable defaults: conservative and stress are intended to miss
the 20 ps precision target when all random terms are RSS-combined.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure
from tidl_poc.common.rng import rng as make_rng
from tidl_poc.models.parallel_chains import default_fit, sigma_total_ps

PRECISION_TARGET_PS = 20.0
ACCURACY_TARGET_PS = 20.0
MC_FAST = 20_000
MC_FULL = 200_000

KIND_RANDOM = "random_precision"
KIND_BIAS = "deterministic_calibratable_bias"
KIND_COMMON = "correlated_common_mode"

PROVENANCE_LITERATURE = "literature"
PROVENANCE_ALLOCATION = "engineering_allocation"


@dataclass(frozen=True)
class BudgetTerm:
    name: str
    sigma_ps: float
    provenance: str
    source: str
    kind: str = KIND_RANDOM

    @property
    def correlated(self) -> bool:
        return self.kind == KIND_COMMON


def rss(sigmas_ps: np.ndarray) -> float:
    """Root-sum-square of independent RMS terms. Units: ps RMS."""
    arr = np.asarray(sigmas_ps, dtype=float)
    return float(np.sqrt(np.sum(arr**2)))


def literature_tdc_ssp_ps(n_chains: int = 10) -> float:
    return float(sigma_total_ps(n_chains, default_fit()))


def _term(name: str, sigma: float, provenance: str, source: str, kind: str = KIND_RANDOM) -> BudgetTerm:
    return BudgetTerm(name, sigma, provenance, source, kind)


def scenarios() -> dict[str, list[BudgetTerm]]:
    tdc_n10 = literature_tdc_ssp_ps(10)
    tdc_n8 = literature_tdc_ssp_ps(8)
    tdc_n1 = literature_tdc_ssp_ps(1)
    lit_tdc = "Mao 2022 literature-fitted multi-chain SSP model; not this FPGA"
    return {
        "literature_informed_illustrative": [
            _term("frontend_threshold_jitter_ps", 8.0, PROVENANCE_ALLOCATION, "unselected comparator; engineering allocation"),
            _term("time_walk_residual_ps", 5.0, PROVENANCE_ALLOCATION, "amplitude leftover; calibratable bias allocation", KIND_BIAS),
            _term("fpga_fine_tdc_ssp_ps", tdc_n10, PROVENANCE_LITERATURE, lit_tdc + " (N=10)"),
            _term("coarse_reference_jitter_ps", 5.0, PROVENANCE_ALLOCATION, "10 MHz quality not specified"),
            _term("channel_random_residual_ps", 5.0, PROVENANCE_ALLOCATION, "16-channel random leftover allocation"),
            _term("calibration_random_residual_ps", 3.0, PROVENANCE_ALLOCATION, "code-density random leftover"),
            _term("pvt_random_residual_ps", 5.0, PROVENANCE_ALLOCATION, "10-40 C random leftover after cal"),
            _term("supply_noise_ps", 3.0, PROVENANCE_ALLOCATION, "rail allocation"),
            _term("clock_distribution_ps", 4.0, PROVENANCE_ALLOCATION, "on-board/on-chip allocation"),
            _term("common_correlated_ps", 2.0, PROVENANCE_ALLOCATION, "shared supply/clock", KIND_COMMON),
        ],
        "conservative": [
            _term("frontend_threshold_jitter_ps", 12.0, PROVENANCE_ALLOCATION, "unselected comparator, conservative"),
            _term("time_walk_residual_ps", 8.0, PROVENANCE_ALLOCATION, "conservative walk bias", KIND_BIAS),
            _term("fpga_fine_tdc_ssp_ps", tdc_n1, PROVENANCE_LITERATURE, lit_tdc + " (N=1)"),
            _term("coarse_reference_jitter_ps", 8.0, PROVENANCE_ALLOCATION, "unqualified 10 MHz"),
            _term("channel_random_residual_ps", 8.0, PROVENANCE_ALLOCATION, "conservative 16-channel random leftover"),
            _term("calibration_random_residual_ps", 6.0, PROVENANCE_ALLOCATION, "sparse or stale calibration"),
            _term("pvt_random_residual_ps", 10.0, PROVENANCE_ALLOCATION, "slow/no online calibration leftover"),
            _term("supply_noise_ps", 6.0, PROVENANCE_ALLOCATION, "conservative"),
            _term("clock_distribution_ps", 8.0, PROVENANCE_ALLOCATION, "conservative"),
            _term("common_correlated_ps", 5.0, PROVENANCE_ALLOCATION, "larger common-mode", KIND_COMMON),
        ],
        "stress": [
            _term("frontend_threshold_jitter_ps", 20.0, PROVENANCE_ALLOCATION, "slow edge / noisy threshold"),
            _term("time_walk_residual_ps", 12.0, PROVENANCE_ALLOCATION, "uncorrected walk bias", KIND_BIAS),
            _term("fpga_fine_tdc_ssp_ps", 15.0, PROVENANCE_ALLOCATION, "worse than Mao 1-chain; not literature"),
            _term("coarse_reference_jitter_ps", 12.0, PROVENANCE_ALLOCATION, "poor short-term 10 MHz"),
            _term("channel_random_residual_ps", 12.0, PROVENANCE_ALLOCATION, "uncalibrated channel random leftover"),
            _term("calibration_random_residual_ps", 10.0, PROVENANCE_ALLOCATION, "inadequate code density"),
            _term("pvt_random_residual_ps", 15.0, PROVENANCE_ALLOCATION, "no temperature tracking leftover"),
            _term("supply_noise_ps", 10.0, PROVENANCE_ALLOCATION, "stressed rails"),
            _term("clock_distribution_ps", 12.0, PROVENANCE_ALLOCATION, "skewed clock tree"),
            _term("common_correlated_ps", 8.0, PROVENANCE_ALLOCATION, "shared supply/clock", KIND_COMMON),
        ],
        "target_allocation": [
            _term("frontend_threshold_jitter_ps", 5.0, PROVENANCE_ALLOCATION, "design allocation; not evidence"),
            _term("time_walk_residual_ps", 3.0, PROVENANCE_ALLOCATION, "design allocation; calibratable bias", KIND_BIAS),
            _term("fpga_fine_tdc_ssp_ps", tdc_n8, PROVENANCE_LITERATURE, lit_tdc + " (N=8, first Vivado baseline)"),
            _term("coarse_reference_jitter_ps", 4.0, PROVENANCE_ALLOCATION, "design allocation; not evidence"),
            _term("channel_random_residual_ps", 4.0, PROVENANCE_ALLOCATION, "design allocation; not evidence"),
            _term("calibration_random_residual_ps", 3.0, PROVENANCE_ALLOCATION, "design allocation; not evidence"),
            _term("pvt_random_residual_ps", 4.0, PROVENANCE_ALLOCATION, "design allocation; not evidence"),
            _term("supply_noise_ps", 2.0, PROVENANCE_ALLOCATION, "design allocation; not evidence"),
            _term("clock_distribution_ps", 3.0, PROVENANCE_ALLOCATION, "design allocation; not evidence"),
            _term("common_correlated_ps", 2.0, PROVENANCE_ALLOCATION, "design allocation; not evidence", KIND_COMMON),
        ],
    }


def combine_terms(terms: list[BudgetTerm]) -> dict[str, float]:
    """RSS treating every sigma as a random contribution (legacy combined view)."""
    independent = [t.sigma_ps for t in terms if t.kind != KIND_COMMON]
    common = [t.sigma_ps for t in terms if t.kind == KIND_COMMON]
    rss_ind = rss(np.array(independent)) if independent else 0.0
    rss_all = rss(np.array([t.sigma_ps for t in terms]))
    return {
        "rss_independent_ps": rss_ind,
        "rss_including_common_ps": rss_all,
        "common_ps": float(common[0]) if common else 0.0,
    }


def classify_budget(terms: list[BudgetTerm]) -> dict[str, float]:
    random = [t.sigma_ps for t in terms if t.kind == KIND_RANDOM]
    bias = [t.sigma_ps for t in terms if t.kind == KIND_BIAS]
    common = [t.sigma_ps for t in terms if t.kind == KIND_COMMON]
    precision_rss = rss(np.array(random)) if random else 0.0
    common_ps = float(common[0]) if common else 0.0
    precision_with_common = rss(np.array(random + common)) if (random or common) else 0.0
    bias_sum = float(np.sum(np.abs(bias))) if bias else 0.0
    return {
        "precision_rss_ps": precision_rss,
        "precision_rss_with_common_ps": precision_with_common,
        "accuracy_bias_sum_ps": bias_sum,
        "accuracy_worst_case_ps": bias_sum + precision_with_common,
        "common_ps": common_ps,
        "passes_20ps_precision": precision_with_common <= PRECISION_TARGET_PS,
        "passes_20ps_accuracy_worst_case": (bias_sum + precision_with_common) <= ACCURACY_TARGET_PS,
    }


def tornado(terms: list[BudgetTerm]) -> pd.DataFrame:
    baseline = classify_budget(terms)["precision_rss_with_common_ps"]
    rows = []
    for term in terms:
        reduced = [t for t in terms if t.name != term.name]
        without = classify_budget(reduced)["precision_rss_with_common_ps"] if reduced else 0.0
        rows.append(
            {
                "term": term.name,
                "sigma_ps": term.sigma_ps,
                "kind": term.kind,
                "provenance": term.provenance,
                "source": term.source,
                "baseline_precision_rss_ps": baseline,
                "rss_without_term_ps": without,
                "contribution_ps": math_contrib(baseline, without),
            }
        )
    return pd.DataFrame(rows).sort_values("contribution_ps", ascending=False)


def math_contrib(baseline: float, without: float) -> float:
    return float(np.sqrt(max(baseline**2 - without**2, 0.0)))


def monte_carlo(terms: list[BudgetTerm], n: int, seed: int) -> np.ndarray:
    """Gaussian draw of random + common terms only. Bias is not randomised here."""
    gen = make_rng(seed)
    acc = np.zeros(n)
    for term in terms:
        if term.kind == KIND_BIAS:
            continue
        samples = gen.normal(0.0, term.sigma_ps, size=n)
        acc = acc + samples
    return acc


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    out = outputs_dir("error_budget")
    n_mc = MC_FAST if fast else MC_FULL
    all_rows = []
    tornado_frames = []
    mc_summary = []
    sc = scenarios()
    fig = plt.figure(figsize=(7.2, 11.5))
    axes = fig.subplots(len(sc), 1, sharex=False)

    for ax, (name, terms) in zip(np.atleast_1d(axes), sc.items(), strict=True):
        combo = combine_terms(terms)
        classified = classify_budget(terms)
        for term in terms:
            all_rows.append(
                {
                    "scenario": name,
                    "term": term.name,
                    "sigma_ps": term.sigma_ps,
                    "kind": term.kind,
                    "provenance": term.provenance,
                    "source": term.source,
                    "correlated": term.correlated,
                    "is_evidence": term.provenance == PROVENANCE_LITERATURE,
                    "result_classification": "model-based simulation",
                }
            )
        torn = tornado(terms)
        torn["scenario"] = name
        tornado_frames.append(torn)
        samples = monte_carlo(terms, n_mc, seed)
        mc_rms = float(np.std(samples, ddof=1))
        mc_summary.append(
            {
                "scenario": name,
                "precision_rss_ps": classified["precision_rss_ps"],
                "precision_rss_with_common_ps": classified["precision_rss_with_common_ps"],
                "accuracy_bias_sum_ps": classified["accuracy_bias_sum_ps"],
                "accuracy_worst_case_ps": classified["accuracy_worst_case_ps"],
                "legacy_rss_all_terms_ps": combo["rss_including_common_ps"],
                "monte_carlo_precision_rms_ps": mc_rms,
                "precision_target_ps": PRECISION_TARGET_PS,
                "passes_20ps_precision": classified["passes_20ps_precision"],
                "passes_20ps_accuracy_worst_case": classified["passes_20ps_accuracy_worst_case"],
                "n_monte_carlo": n_mc,
                "result_classification": "model-based simulation",
            }
        )
        torn_plot = torn.sort_values("contribution_ps")
        ax.barh(torn_plot["term"], torn_plot["contribution_ps"], color="0.45")
        ax.axvline(PRECISION_TARGET_PS, color="0.2", linestyle="--")
        ax.set_title(
            f"{name}: precision RSS={classified['precision_rss_with_common_ps']:.2f} ps, "
            f"acc WC={classified['accuracy_worst_case_ps']:.2f} ps"
        )
        ax.set_xlabel("Precision RSS contribution (ps)")

    save_figure(fig, out / "tornado")
    terms_df = pd.DataFrame(all_rows)
    terms_df.to_csv(out / "terms.csv", index=False)
    torn_df = pd.concat(tornado_frames, ignore_index=True)
    torn_df.to_csv(out / "tornado.csv", index=False)
    summary_df = pd.DataFrame(mc_summary)
    summary_df.to_csv(out / "scenario_summary.csv", index=False)
    precision_table = summary_df[
        [
            "scenario",
            "precision_rss_ps",
            "precision_rss_with_common_ps",
            "passes_20ps_precision",
            "result_classification",
        ]
    ]
    accuracy_table = summary_df[
        [
            "scenario",
            "accuracy_bias_sum_ps",
            "accuracy_worst_case_ps",
            "passes_20ps_accuracy_worst_case",
            "result_classification",
        ]
    ]
    precision_table.to_csv(out / "precision_rss.csv", index=False)
    accuracy_table.to_csv(out / "accuracy_worst_case.csv", index=False)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    x = np.arange(len(summary_df))
    w = 0.35
    ax.bar(x - w / 2, summary_df["precision_rss_with_common_ps"], w, color="0.4", label="precision RSS + common")
    ax.bar(x + w / 2, summary_df["accuracy_worst_case_ps"], w, color="0.7", label="accuracy worst-case bound")
    ax.axhline(PRECISION_TARGET_PS, color="0.1", linestyle="--", label="20 ps S14 target")
    ax.set_xticks(x, summary_df["scenario"], rotation=20)
    ax.set_ylabel("ps")
    ax.set_title("Precision RSS vs accuracy worst-case (allocations, not measured)")
    ax.legend()
    save_figure(fig, out / "scenario_rss")

    params = {
        "precision_target_ps": PRECISION_TARGET_PS,
        "accuracy_target_ps": ACCURACY_TARGET_PS,
        "n_monte_carlo": n_mc,
        "fast": fast,
        "kinds": [KIND_RANDOM, KIND_BIAS, KIND_COMMON],
        "combination": (
            "precision = RSS(random_precision [+ common-mode]); "
            "accuracy worst-case = sum(|bias|) + precision_RSS_with_common. "
            "Non-literature values are engineering allocations, not evidence."
        ),
        "tdc_n8_literature_fitted_ps": literature_tdc_ssp_ps(8),
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.error_budget",
        random_seed=seed,
        input_parameters=params,
        extra={"scenarios": mc_summary},
    )
    write_json(out / "summary.json", {"scenarios": mc_summary})
    (out / "interpretation.md").write_text(
        f"""# Error budget

**Classification:** model-based simulation.

S14 precision 20 ps RMS and accuracy 20 ps are distinct. Resolution 1 ps is not
this budget. `target_allocation` is a labelled engineering allocation, not
evidence. FPGA TDC SSP uses a literature-fitted Mao 2022 model (not this FPGA).

Precision RSS table:
{precision_table.to_string(index=False)}

Accuracy / worst-case table (bias sum + precision with common; 1-sigma style bound):
{accuracy_table.to_string(index=False)}

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {
        "output_dir": str(out),
        "summary": summary_df,
        "terms": terms_df,
        "precision": precision_table,
        "accuracy": accuracy_table,
    }
