"""Configurable RMS error-budget model.

Classification: model-based simulation. Parameters are tagged literature or assumption.
No silent favourable defaults: the stress scenario is intended to miss the 20 ps target.
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
MC_FAST = 20_000
MC_FULL = 200_000

TERM_ORDER = (
    "frontend_threshold_jitter_ps",
    "time_walk_residual_ps",
    "fpga_fine_tdc_ssp_ps",
    "coarse_reference_jitter_ps",
    "channel_skew_residual_ps",
    "calibration_residual_ps",
    "pvt_residual_ps",
    "supply_noise_ps",
    "clock_distribution_ps",
    "common_correlated_ps",
)


@dataclass(frozen=True)
class BudgetTerm:
    name: str
    sigma_ps: float
    provenance: str  # "literature" or "assumption"
    source: str
    correlated: bool = False


def rss(sigmas_ps: np.ndarray) -> float:
    """Root-sum-square of independent RMS terms. Units: ps RMS."""
    arr = np.asarray(sigmas_ps, dtype=float)
    return float(np.sqrt(np.sum(arr**2)))


def literature_tdc_ssp_ps(n_chains: int = 10) -> float:
    return float(sigma_total_ps(n_chains, default_fit()))


def scenarios() -> dict[str, list[BudgetTerm]]:
    tdc_n10 = literature_tdc_ssp_ps(10)
    tdc_n1 = literature_tdc_ssp_ps(1)
    return {
        "literature_informed_illustrative": [
            BudgetTerm("frontend_threshold_jitter_ps", 8.0, "assumption", "unselected comparator; placeholder allocation"),
            BudgetTerm("time_walk_residual_ps", 5.0, "assumption", "placeholder residual after walk compensation"),
            BudgetTerm("fpga_fine_tdc_ssp_ps", tdc_n10, "literature", "Mao 2022 10-chain SSP fitted model; not this FPGA"),
            BudgetTerm("coarse_reference_jitter_ps", 5.0, "assumption", "10 MHz quality not yet specified"),
            BudgetTerm("channel_skew_residual_ps", 5.0, "assumption", "16-channel distribution residual placeholder"),
            BudgetTerm("calibration_residual_ps", 3.0, "assumption", "code-density residual placeholder"),
            BudgetTerm("pvt_residual_ps", 5.0, "assumption", "10-40 C residual placeholder; Mao TC is resolution not residual"),
            BudgetTerm("supply_noise_ps", 3.0, "assumption", "placeholder"),
            BudgetTerm("clock_distribution_ps", 4.0, "assumption", "placeholder"),
            BudgetTerm("common_correlated_ps", 2.0, "assumption", "optional common-mode term", True),
        ],
        "conservative": [
            BudgetTerm("frontend_threshold_jitter_ps", 12.0, "assumption", "unselected comparator, conservative"),
            BudgetTerm("time_walk_residual_ps", 8.0, "assumption", "conservative walk residual"),
            BudgetTerm("fpga_fine_tdc_ssp_ps", tdc_n1, "literature", "Mao 2022 1-chain SSP fitted model; not this FPGA"),
            BudgetTerm("coarse_reference_jitter_ps", 8.0, "assumption", "unqualified 10 MHz"),
            BudgetTerm("channel_skew_residual_ps", 8.0, "assumption", "conservative 16-channel residual"),
            BudgetTerm("calibration_residual_ps", 6.0, "assumption", "sparse or stale calibration"),
            BudgetTerm("pvt_residual_ps", 10.0, "assumption", "slow/no online calibration"),
            BudgetTerm("supply_noise_ps", 6.0, "assumption", "conservative"),
            BudgetTerm("clock_distribution_ps", 8.0, "assumption", "conservative"),
            BudgetTerm("common_correlated_ps", 5.0, "assumption", "larger common-mode", True),
        ],
        "stress": [
            BudgetTerm("frontend_threshold_jitter_ps", 20.0, "assumption", "slow edge / noisy threshold"),
            BudgetTerm("time_walk_residual_ps", 12.0, "assumption", "uncorrected walk"),
            BudgetTerm("fpga_fine_tdc_ssp_ps", 15.0, "assumption", "worse than Mao 1-chain; placement/PVT stress"),
            BudgetTerm("coarse_reference_jitter_ps", 12.0, "assumption", "poor short-term 10 MHz"),
            BudgetTerm("channel_skew_residual_ps", 12.0, "assumption", "uncalibrated channel distribution"),
            BudgetTerm("calibration_residual_ps", 10.0, "assumption", "inadequate code density"),
            BudgetTerm("pvt_residual_ps", 15.0, "assumption", "no temperature tracking"),
            BudgetTerm("supply_noise_ps", 10.0, "assumption", "stressed rails"),
            BudgetTerm("clock_distribution_ps", 12.0, "assumption", "skewed clock tree"),
            BudgetTerm("common_correlated_ps", 8.0, "assumption", "shared supply/clock", True),
        ],
    }


def combine_terms(terms: list[BudgetTerm]) -> dict[str, float]:
    independent = [t.sigma_ps for t in terms if not t.correlated]
    common = [t.sigma_ps for t in terms if t.correlated]
    rss_ind = rss(np.array(independent))
    rss_all = rss(np.array([t.sigma_ps for t in terms]))
    return {
        "rss_independent_ps": rss_ind,
        "rss_including_common_ps": rss_all,
        "common_ps": float(common[0]) if common else 0.0,
    }


def tornado(terms: list[BudgetTerm]) -> pd.DataFrame:
    baseline = combine_terms(terms)["rss_including_common_ps"]
    rows = []
    for term in terms:
        reduced = [t for t in terms if t.name != term.name]
        without = combine_terms(reduced)["rss_including_common_ps"] if reduced else 0.0
        rows.append(
            {
                "term": term.name,
                "sigma_ps": term.sigma_ps,
                "provenance": term.provenance,
                "source": term.source,
                "baseline_rss_ps": baseline,
                "rss_without_term_ps": without,
                "contribution_ps": math_contrib(baseline, without),
            }
        )
    return pd.DataFrame(rows).sort_values("contribution_ps", ascending=False)


def math_contrib(baseline: float, without: float) -> float:
    return float(np.sqrt(max(baseline**2 - without**2, 0.0)))


def monte_carlo(terms: list[BudgetTerm], n: int, seed: int) -> np.ndarray:
    gen = make_rng(seed)
    common = 0.0
    acc = np.zeros(n)
    for term in terms:
        samples = gen.normal(0.0, term.sigma_ps, size=n)
        if term.correlated:
            common = gen.normal(0.0, term.sigma_ps, size=n)
            acc = acc + common
        else:
            acc = acc + samples
    return acc


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    out = outputs_dir("error_budget")
    n_mc = MC_FAST if fast else MC_FULL
    all_rows = []
    tornado_frames = []
    mc_summary = []
    fig = plt.figure(figsize=(7.2, 8.8))
    axes = fig.subplots(3, 1, sharex=False)

    for ax, (name, terms) in zip(axes, scenarios().items(), strict=True):
        combo = combine_terms(terms)
        passed = combo["rss_including_common_ps"] <= PRECISION_TARGET_PS
        for term in terms:
            all_rows.append(
                {
                    "scenario": name,
                    "term": term.name,
                    "sigma_ps": term.sigma_ps,
                    "provenance": term.provenance,
                    "source": term.source,
                    "correlated": term.correlated,
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
                "rss_independent_ps": combo["rss_independent_ps"],
                "rss_including_common_ps": combo["rss_including_common_ps"],
                "monte_carlo_rms_ps": mc_rms,
                "precision_target_ps": PRECISION_TARGET_PS,
                "passes_20ps_rss": passed,
                "n_monte_carlo": n_mc,
                "result_classification": "model-based simulation",
            }
        )
        torn_plot = torn.sort_values("contribution_ps")
        ax.barh(torn_plot["term"], torn_plot["contribution_ps"], color="0.45")
        ax.axvline(PRECISION_TARGET_PS, color="0.2", linestyle="--")
        ax.set_title(f"{name}: RSS={combo['rss_including_common_ps']:.2f} ps, pass={passed}")
        ax.set_xlabel("RSS contribution (ps)")

    save_figure(fig, out / "tornado")
    terms_df = pd.DataFrame(all_rows)
    terms_df.to_csv(out / "terms.csv", index=False)
    torn_df = pd.concat(tornado_frames, ignore_index=True)
    torn_df.to_csv(out / "tornado.csv", index=False)
    summary_df = pd.DataFrame(mc_summary)
    summary_df.to_csv(out / "scenario_summary.csv", index=False)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(summary_df["scenario"], summary_df["rss_including_common_ps"], color="0.5")
    ax.axhline(PRECISION_TARGET_PS, color="0.1", linestyle="--", label="20 ps precision target")
    ax.set_ylabel("Combined RMS (ps)")
    ax.set_title("Error-budget scenarios (model-based; not measured)")
    ax.tick_params(axis="x", labelrotation=15)
    ax.legend()
    save_figure(fig, out / "scenario_rss")

    params = {
        "precision_target_ps": PRECISION_TARGET_PS,
        "n_monte_carlo": n_mc,
        "fast": fast,
        "combination": "RSS independent terms plus optional common/correlated term",
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

S14 precision target is 20 ps RMS. Resolution (1 ps) and accuracy (20 ps) are distinct.
Most terms are engineering assumptions. The FPGA TDC SSP in the illustrative scenario
uses a literature-fitted Mao 2022 model and is not a result from this repository.

{summary_df.to_string(index=False)}

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "summary": summary_df, "terms": terms_df}
