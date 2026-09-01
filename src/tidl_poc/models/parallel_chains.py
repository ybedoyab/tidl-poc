"""Literature-fitted parallel-chain RMS model.

Classification: model-based simulation fitted to literature anchors.

Anchors (Mao et al., Sensors 2022, DOI 10.3390/s22062306; literature evidence,
not reproduced here):
    1-chain single-shot precision (SSP) = 8.7 ps RMS
    10-chain SSP = 4.6 ps RMS

Model (engineering hypothesis, not identical to Mao's MCS architecture):
    sigma_total(N)^2 = sigma_common^2 + sigma_independent^2 / N

Mao's 10-chain result used parallel multichain cross-segmentation, not simple
1/N averaging of independent chains. Transferring Kintex-7 28 nm numbers to
another FPGA family is not justified. SSP is not system precision.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure

MAO_SSP_1_CHAIN_PS = 8.7
MAO_SSP_10_CHAIN_PS = 4.6
MAO_N_ANCHOR = 10
CHAIN_COUNTS = (1, 2, 4, 6, 8, 10, 12, 16)
SENSITIVITY_FRACTIONS = (0.10, 0.20)


@dataclass(frozen=True)
class ChainNoiseFit:
    sigma_common_ps: float
    sigma_independent_ps: float
    sigma_n1_ps: float
    sigma_n_anchor_ps: float
    n_anchor: int


def fit_common_independent(
    sigma_n1_ps: float,
    sigma_n_anchor_ps: float,
    n_anchor: int = MAO_N_ANCHOR,
) -> ChainNoiseFit:
    """Solve the two-parameter RMS model from two chain-count anchors.

    Units: picoseconds RMS. Requires sigma_n1 > sigma_n_anchor > 0 and
    n_anchor > 1 so that both variance components are positive.
    """
    if n_anchor <= 1:
        raise ValueError("n_anchor must be > 1")
    var1 = float(sigma_n1_ps) ** 2
    var_n = float(sigma_n_anchor_ps) ** 2
    denom = 1.0 - 1.0 / float(n_anchor)
    var_independent = (var1 - var_n) / denom
    var_common = var1 - var_independent
    if var_independent <= 0.0 or var_common <= 0.0:
        raise ValueError(
            "Anchors do not yield positive common and independent variances. "
            f"got var_common={var_common}, var_independent={var_independent}"
        )
    return ChainNoiseFit(
        sigma_common_ps=float(np.sqrt(var_common)),
        sigma_independent_ps=float(np.sqrt(var_independent)),
        sigma_n1_ps=float(sigma_n1_ps),
        sigma_n_anchor_ps=float(sigma_n_anchor_ps),
        n_anchor=int(n_anchor),
    )


def sigma_total_ps(n_chains: np.ndarray | float, fit: ChainNoiseFit) -> np.ndarray | float:
    """Total RMS versus chain count N. Units: ps RMS."""
    n = np.asarray(n_chains, dtype=float)
    if np.any(n <= 0):
        raise ValueError("n_chains must be positive")
    out = np.sqrt(fit.sigma_common_ps**2 + fit.sigma_independent_ps**2 / n)
    if np.ndim(out) == 0:
        return float(out)
    return out


def default_fit() -> ChainNoiseFit:
    return fit_common_independent(MAO_SSP_1_CHAIN_PS, MAO_SSP_10_CHAIN_PS, MAO_N_ANCHOR)


def sensitivity_envelope(
    n_values: np.ndarray,
    fractions: tuple[float, ...] = SENSITIVITY_FRACTIONS,
) -> dict[str, np.ndarray]:
    """Refit after perturbing literature anchors; return min/max envelopes."""
    base = default_fit()
    curves = [sigma_total_ps(n_values, base)]
    for frac in fractions:
        for s1_sign in (-1.0, 1.0):
            for s10_sign in (-1.0, 1.0):
                s1 = MAO_SSP_1_CHAIN_PS * (1.0 + s1_sign * frac)
                s10 = MAO_SSP_10_CHAIN_PS * (1.0 + s10_sign * frac)
                if s1 <= s10:
                    continue
                try:
                    fit = fit_common_independent(s1, s10, MAO_N_ANCHOR)
                except ValueError:
                    continue
                curves.append(sigma_total_ps(n_values, fit))
    stacked = np.vstack(curves)
    return {
        "nominal_ps": stacked[0],
        "min_ps": stacked.min(axis=0),
        "max_ps": stacked.max(axis=0),
        "n": n_values,
    }


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    """Write CSV, figures, metadata, and a short interpretation markdown."""
    out = outputs_dir("parallel_chains")
    fit = default_fit()
    n = np.array(CHAIN_COUNTS, dtype=float)
    env = sensitivity_envelope(n)
    rows = []
    for n_i, nom, lo, hi in zip(n, env["nominal_ps"], env["min_ps"], env["max_ps"], strict=True):
        rows.append(
            {
                "n_chains": int(n_i),
                "sigma_total_ps_rms": float(nom),
                "sensitivity_min_ps_rms": float(lo),
                "sensitivity_max_ps_rms": float(hi),
                "sigma_common_ps_rms": fit.sigma_common_ps,
                "sigma_independent_ps_rms": fit.sigma_independent_ps,
                "result_classification": "model-based simulation",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(out / "parallel_chain_ssp.csv", index=False)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.fill_between(
        n,
        env["min_ps"],
        env["max_ps"],
        color="0.8",
        label="anchor sensitivity band (±10% and ±20%)",
    )
    ax.plot(n, env["nominal_ps"], color="0.1", marker="o", label="nominal literature-fitted model")
    ax.scatter(
        [1, 10],
        [MAO_SSP_1_CHAIN_PS, MAO_SSP_10_CHAIN_PS],
        color="0.1",
        zorder=5,
        label="Mao 2022 anchors (literature, not reproduced)",
    )
    ax.axhline(
        20.0,
        color="0.4",
        linestyle="--",
        label="S14 precision target 20 ps RMS (system, not TDC-only)",
    )
    ax.set_xlabel("Number of parallel chains N")
    ax.set_ylabel("Modelled single-shot precision (ps RMS)")
    ax.set_title("Literature-fitted common + independent chain noise (not FPGA data)")
    ax.legend(loc="upper right")
    save_figure(fig, out / "parallel_chain_ssp")

    below = n[env["nominal_ps"] <= 20.0]
    n_at_20 = int(below[0]) if len(below) else None
    interpretation = f"""# Parallel-chain RMS model interpretation

**Classification:** model-based simulation fitted to literature anchors.
**Not** a physical measurement and **not** an FPGA result from this repository.

## Fitted parameters

From Mao et al. 2022 anchors (1-chain SSP = {MAO_SSP_1_CHAIN_PS} ps RMS,
10-chain SSP = {MAO_SSP_10_CHAIN_PS} ps RMS):

- sigma_common = {fit.sigma_common_ps:.4f} ps RMS
- sigma_independent = {fit.sigma_independent_ps:.4f} ps RMS
- N -> inf limit = sigma_common (common-mode floor)

Nominal N=16 total = {float(env["nominal_ps"][-1]):.4f} ps RMS
Sensitivity band at N=16: {float(env["min_ps"][-1]):.4f} to {float(env["max_ps"][-1]):.4f} ps RMS

First tabulated N with nominal model <= 20 ps RMS: {n_at_20}

## Caveats

1. Mao implemented multichain cross-segmentation (MCS), not independent-chain averaging.
2. Digital 1 ps quantization does not prove 1 ps physical resolution.
3. Fine TDC SSP is only one term in the system error budget.
4. Kintex-7 28 nm numbers do not transfer to UltraScale / UltraScale+ without measurement.
5. Sensitivity bands show dependence on the two literature anchors, not a confidence interval
   from a local experiment.

{MEASUREMENT_DISCLAIMER}
"""
    (out / "interpretation.md").write_text(interpretation, encoding="utf-8")

    params = {
        "literature_anchor_1_chain_ssp_ps": MAO_SSP_1_CHAIN_PS,
        "literature_anchor_10_chain_ssp_ps": MAO_SSP_10_CHAIN_PS,
        "literature_source": "Mao et al. Sensors 2022 DOI 10.3390/s22062306",
        "chain_counts": list(CHAIN_COUNTS),
        "sensitivity_fractions": list(SENSITIVITY_FRACTIONS),
        "fast": fast,
        "model": "sigma_total(N)^2 = sigma_common^2 + sigma_independent^2 / N",
        "parameter_provenance": {
            "anchors": "literature",
            "functional_form": "engineering assumption (not identical to MCS)",
        },
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.parallel_chains",
        random_seed=seed,
        input_parameters=params,
        extra={
            "sigma_common_ps": fit.sigma_common_ps,
            "sigma_independent_ps": fit.sigma_independent_ps,
        },
    )
    write_json(
        out / "summary.json",
        {
            "n16_nominal_ps_rms": float(env["nominal_ps"][-1]),
            "sigma_common_ps_rms": fit.sigma_common_ps,
            "sigma_independent_ps_rms": fit.sigma_independent_ps,
        },
    )
    return {"output_dir": str(out), "fit": fit, "table": df}
