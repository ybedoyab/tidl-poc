"""First-order reference-clock stability allocation.

Classification: model-based simulation of the relation delta_t = y * tau.
This is not an Allan-deviation measurement and not NIST SP 1065 analysis of data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure

TAU_S = 1.0
INTERVAL_ERRORS_PS = (5.0, 10.0, 20.0)


def fractional_frequency_from_interval_error(delta_t_s: float, tau_s: float) -> float:
    """y = delta_t / tau. Dimensionless fractional-frequency error.

    First-order accumulated-interval relation, not ADEV/MDEV/TDEV.
    """
    if tau_s <= 0:
        raise ValueError("tau_s must be > 0")
    return float(delta_t_s) / float(tau_s)


def interval_error_from_y(y: float, tau_s: float) -> float:
    """delta_t = y * tau. Units: seconds if tau is seconds."""
    return float(y) * float(tau_s)


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    del seed, fast
    out = outputs_dir("reference_stability")
    rows = []
    for err_ps in INTERVAL_ERRORS_PS:
        delta_t_s = err_ps * 1e-12
        y = fractional_frequency_from_interval_error(delta_t_s, TAU_S)
        rows.append(
            {
                "tau_s": TAU_S,
                "interval_error_ps": err_ps,
                "interval_error_s": delta_t_s,
                "fractional_frequency_y": y,
                "model": "delta_t = y * tau",
                "is_allan_deviation": False,
                "result_classification": "model-based simulation",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(out / "fractional_frequency_allocation.csv", index=False)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(df["interval_error_ps"], df["fractional_frequency_y"], marker="o", color="0.1")
    ax.set_xlabel("Allowed interval error at tau = 1 s (ps)")
    ax.set_ylabel("First-order |y| = |delta_t| / tau")
    ax.set_title("Reference-clock allocation (not ADEV proof)")
    save_figure(fig, out / "fractional_frequency_allocation")

    tau_grid = np.array([1e-3, 1e-2, 1e-1, 1.0, 10.0])
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    for err_ps in INTERVAL_ERRORS_PS:
        y = (err_ps * 1e-12) / TAU_S
        ax.loglog(tau_grid, np.abs(y) * tau_grid * 1e12, marker="o", label=f"|y| for {err_ps:.0f} ps @ 1 s")
    ax.set_xlabel("tau (s)")
    ax.set_ylabel("|delta_t| = |y| * tau (ps)")
    ax.set_title("Linear accumulation of a constant fractional-frequency offset")
    ax.legend()
    save_figure(fig, out / "linear_accumulation")

    extra = {
        "tau_s": TAU_S,
        "y_for_5ps_at_1s": fractional_frequency_from_interval_error(5e-12, 1.0),
        "y_for_10ps_at_1s": fractional_frequency_from_interval_error(10e-12, 1.0),
        "y_for_20ps_at_1s": fractional_frequency_from_interval_error(20e-12, 1.0),
        "is_allan_deviation_proof": False,
    }
    params = {
        "model": "delta_t = y * tau",
        "tau_s": TAU_S,
        "interval_errors_ps": list(INTERVAL_ERRORS_PS),
        "parameter_provenance": "S14-driven first-order allocation; not measured ADEV",
        "standards": "NIST SP 1065 and IEEE 1139 apply once a dataset exists",
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.reference_stability",
        random_seed=DEFAULT_SEED,
        input_parameters=params,
        extra=extra,
    )
    write_json(out / "summary.json", extra)
    (out / "interpretation.md").write_text(
        f"""# Reference stability (first-order allocation)

**Classification:** model-based simulation of `delta_t = y * tau`.
This is **not** Allan-deviation proof and not a substitute for NIST SP 1065
analysis of a measured 10 MHz record.

At tau = 1 s:
- 5 ps  -> |y| = {extra["y_for_5ps_at_1s"]:.2e}
- 10 ps -> |y| = {extra["y_for_10ps_at_1s"]:.2e}
- 20 ps -> |y| = {extra["y_for_20ps_at_1s"]:.2e}

S14 20 ps over 1 s therefore allocates about 2e-11 fractional frequency if the
error is modelled as a constant offset accumulating linearly. Real clocks need
ADEV/MDEV/TDEV once hardware exists.

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "table": df}
