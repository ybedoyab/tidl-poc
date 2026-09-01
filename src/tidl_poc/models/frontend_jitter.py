"""Analytical front-end timing jitter model.

sigma_t ~= sigma_v / slew_rate, with additional RSS terms.

Classification: model-based simulation. No comparator part is selected.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure

BUDGETS_PS = (5.0, 10.0, 15.0)


def threshold_crossing_jitter_s(sigma_v: float, slew_rate_v_per_s: float) -> float:
    """sigma_t = sigma_v / |slew|. Units: seconds. sigma_v in volts, slew in V/s."""
    slew = np.abs(np.asarray(slew_rate_v_per_s, dtype=float))
    if np.any(slew <= 0):
        raise ValueError("slew_rate must be > 0")
    return np.asarray(sigma_v, dtype=float) / slew


def combined_jitter_ps(
    sigma_v: np.ndarray | float,
    slew_v_per_s: np.ndarray | float,
    threshold_uncertainty_v: float = 0.0,
    comparator_additive_ps: float = 0.0,
    timewalk_residual_ps: float = 0.0,
) -> np.ndarray:
    crossing = threshold_crossing_jitter_s(sigma_v, slew_v_per_s) * 1e12
    thresh = threshold_crossing_jitter_s(threshold_uncertainty_v, slew_v_per_s) * 1e12
    return np.sqrt(crossing**2 + thresh**2 + comparator_additive_ps**2 + timewalk_residual_ps**2)


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    del seed
    out = outputs_dir("frontend_jitter")
    n = 41 if fast else 81
    sigma_v = np.geomspace(1e-4, 2e-2, n)  # 0.1 mV to 20 mV RMS
    # Rise 200 ps to 10 ns over a 0.8 V illustrative swing (not a selected logic family).
    swing_v = 0.8
    rise_s = np.geomspace(200e-12, 10e-9, n)
    slew = swing_v / rise_s

    sv, sl = np.meshgrid(sigma_v, slew, indexing="xy")
    jitter = combined_jitter_ps(
        sv,
        sl,
        threshold_uncertainty_v=0.5e-3,  # assumption: 0.5 mV threshold uncertainty
        comparator_additive_ps=2.0,  # assumption
        timewalk_residual_ps=3.0,  # assumption
    )

    rows = []
    for i, s_v in enumerate(sigma_v[:: max(len(sigma_v) // 12, 1)]):
        for j, slew_i in enumerate(slew[:: max(len(slew) // 12, 1)]):
            jt = float(
                combined_jitter_ps(s_v, slew_i, 0.5e-3, 2.0, 3.0)
            )
            rows.append(
                {
                    "sigma_v_rms": float(s_v),
                    "slew_v_per_s": float(slew_i),
                    "rise_time_s": float(swing_v / slew_i),
                    "frontend_jitter_ps_rms": jt,
                    "result_classification": "model-based simulation",
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(out / "frontend_grid.csv", index=False)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    cs = ax.contour(
        sigma_v * 1e3,
        slew / 1e9,
        jitter,
        levels=BUDGETS_PS,
        colors=["0.1", "0.35", "0.6"],
    )
    ax.clabel(cs, inline=True, fmt="%1.0f ps")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Input-referred voltage noise (mV RMS)")
    ax.set_ylabel("Edge slew rate (V/ns)")
    ax.set_title("Front-end allocation contours (analytical; no comparator selected)")
    save_figure(fig, out / "design_space")

    # 1-D slew sweep at 1 mV RMS.
    slew_1d = np.geomspace(0.05e9, 8e9, 60)
    j_1d = combined_jitter_ps(1e-3, slew_1d, 0.5e-3, 2.0, 3.0)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.loglog(slew_1d / 1e9, j_1d, color="0.1")
    for b in BUDGETS_PS:
        ax.axhline(b, color="0.5", linestyle="--")
    ax.set_xlabel("Slew rate (V/ns)")
    ax.set_ylabel("Front-end jitter (ps RMS)")
    ax.set_title("1 mV RMS noise, 0.5 mV threshold unc., 2 ps comparator, 3 ps walk")
    save_figure(fig, out / "slew_sweep")

    params = {
        "model": "sigma_t = sigma_v / slew_rate plus RSS of threshold, comparator, time-walk",
        "swing_v": swing_v,
        "threshold_uncertainty_v": 5e-4,
        "comparator_additive_ps": 2.0,
        "timewalk_residual_ps": 3.0,
        "budgets_ps": list(BUDGETS_PS),
        "parameter_provenance": "all analog coefficients are engineering assumptions; no datasheet part",
        "fast": fast,
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.frontend_jitter",
        random_seed=DEFAULT_SEED,
        input_parameters=params,
    )
    compatible = {str(int(b)): float(np.min(slew_1d[j_1d <= b] / 1e9)) if np.any(j_1d <= b) else None for b in BUDGETS_PS}
    write_json(out / "summary.json", {"min_slew_v_per_ns_at_1mV_for_budget": compatible})
    (out / "interpretation.md").write_text(
        f"""# Front-end timing jitter

**Classification:** model-based simulation. No comparator has been selected.

sigma_t (s) ~= sigma_v (V) / slew_rate (V/s).
Additional RSS terms: threshold uncertainty, comparator additive jitter, time-walk residual.

Minimum slew at 1 mV RMS to stay under each allocation (V/ns): {compatible}

A 50 ohm SMA front-end must still be designed and SPICE-simulated before these
allocations can be treated as hardware evidence.

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "table": df, "compatible": compatible}
