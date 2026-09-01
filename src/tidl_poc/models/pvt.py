"""Temperature / PVT residual timing model for 10-40 C.

Classification: model-based simulation.
Mao et al. 2022 quote 0.0002 ps/C as a *resolution* temperature coefficient on a
Kintex-7 MCS TDC. That coefficient is not a residual timestamp-error coefficient
and is not used as the residual model here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure

T_MIN_C = 10.0
T_MAX_C = 40.0
T_REF_C = 21.5  # nominal laboratory mid-band
MAO_RESOLUTION_TC_PS_PER_C = 0.0002  # literature, resolution only

# Residual model coefficients are engineering sweeps, not datasheet values.
# Units: ps / C for offset; fractional per C for bin delay scale.
OFFSET_TC_SWEEP_PS_PER_C = (0.2, 0.5, 1.0, 2.0)
BIN_SCALE_TC_SWEEP_PER_C = (1e-4, 3e-4, 1e-3)
CAL_INTERVALS_S = (1.0, 10.0, 60.0, 600.0)
RAMP_RATE_C_PER_S = 0.05  # assumption: 0.05 C/s enclosure ramp
CONTINUOUS_LAG_S = 0.2  # assumption: online cal lag
NOMINAL_BIN_PS = 10.0  # illustrative uncalibrated mean bin; not FPGA LSB


def residual_no_cal(delta_t_c: np.ndarray, offset_tc: float, bin_scale_tc: float) -> np.ndarray:
    """Worst-case-ish residual: offset drift + one-bin scale error. Units: ps."""
    offset = offset_tc * delta_t_c
    bin_term = NOMINAL_BIN_PS * bin_scale_tc * delta_t_c
    return offset + bin_term


def residual_periodic(
    delta_t_c: np.ndarray,
    offset_tc: float,
    bin_scale_tc: float,
    interval_s: float,
    ramp_c_per_s: float,
) -> np.ndarray:
    """Periodic cal zeros error at each interval; residual tracks intra-interval drift."""
    delta_since_cal_c = (delta_t_c * 0.0) + min(interval_s * ramp_c_per_s, abs(float(np.max(np.abs(delta_t_c)))))
    # For a time series, fold temperature change since last calibration epoch.
    return residual_no_cal(np.full_like(delta_t_c, delta_since_cal_c, dtype=float), offset_tc, bin_scale_tc)


def residual_continuous(delta_t_c: np.ndarray, offset_tc: float, bin_scale_tc: float, lag_s: float, ramp_c_per_s: float) -> np.ndarray:
    lag_c = lag_s * ramp_c_per_s
    return residual_no_cal(np.full_like(delta_t_c, lag_c), offset_tc, bin_scale_tc)


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    del seed
    out = outputs_dir("pvt")
    temps = np.linspace(T_MIN_C, T_MAX_C, 7 if fast else 31)
    t_series_s = np.linspace(0.0, 1800.0, 181 if fast else 1801)
    t_ramp_c = T_MIN_C + RAMP_RATE_C_PER_S * t_series_s
    t_ramp_c = np.clip(t_ramp_c, T_MIN_C, T_MAX_C)
    step = np.where(t_series_s < 100.0, T_REF_C, T_MAX_C)

    rows = []
    for offset_tc in OFFSET_TC_SWEEP_PS_PER_C:
        for bin_tc in BIN_SCALE_TC_SWEEP_PER_C:
            static = residual_no_cal(temps - T_REF_C, offset_tc, bin_tc)
            rows.append(
                {
                    "mode": "no_calibration",
                    "profile": "static",
                    "offset_tc_ps_per_c": offset_tc,
                    "bin_scale_tc_per_c": bin_tc,
                    "worst_abs_ps": float(np.max(np.abs(static))),
                    "result_classification": "model-based simulation",
                }
            )
            for interval in CAL_INTERVALS_S:
                periodic = residual_periodic(temps - T_REF_C, offset_tc, bin_tc, interval, RAMP_RATE_C_PER_S)
                rows.append(
                    {
                        "mode": "periodic_calibration",
                        "profile": f"interval_{interval:.0f}s",
                        "offset_tc_ps_per_c": offset_tc,
                        "bin_scale_tc_per_c": bin_tc,
                        "cal_interval_s": interval,
                        "worst_abs_ps": float(np.max(np.abs(periodic))),
                        "result_classification": "model-based simulation",
                    }
                )
            cont = residual_continuous(temps - T_REF_C, offset_tc, bin_tc, CONTINUOUS_LAG_S, RAMP_RATE_C_PER_S)
            rows.append(
                {
                    "mode": "continuous_online",
                    "profile": "lag_0.2s",
                    "offset_tc_ps_per_c": offset_tc,
                    "bin_scale_tc_per_c": bin_tc,
                    "worst_abs_ps": float(np.max(np.abs(cont))),
                    "result_classification": "model-based simulation",
                }
            )

            ramp_no = residual_no_cal(t_ramp_c - T_REF_C, offset_tc, bin_tc)
            step_no = residual_no_cal(step - T_REF_C, offset_tc, bin_tc)
            rows.append(
                {
                    "mode": "no_calibration",
                    "profile": "ramp",
                    "offset_tc_ps_per_c": offset_tc,
                    "bin_scale_tc_per_c": bin_tc,
                    "worst_abs_ps": float(np.max(np.abs(ramp_no))),
                    "result_classification": "model-based simulation",
                }
            )
            rows.append(
                {
                    "mode": "no_calibration",
                    "profile": "step",
                    "offset_tc_ps_per_c": offset_tc,
                    "bin_scale_tc_per_c": bin_tc,
                    "worst_abs_ps": float(np.max(np.abs(step_no))),
                    "result_classification": "model-based simulation",
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(out / "pvt_residuals.csv", index=False)

    # Representative plot at mid sweep coefficients.
    off = 1.0
    btc = 3e-4
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(temps, residual_no_cal(temps - T_REF_C, off, btc), label="no calibration")
    for interval in (10.0, 60.0, 600.0):
        ax.plot(
            temps,
            residual_periodic(temps - T_REF_C, off, btc, interval, RAMP_RATE_C_PER_S),
            label=f"periodic {interval:.0f} s (ramp-rate limited)",
        )
    ax.plot(
        temps,
        residual_continuous(temps - T_REF_C, off, btc, CONTINUOUS_LAG_S, RAMP_RATE_C_PER_S),
        label="continuous (0.2 s lag)",
    )
    ax.set_xlabel("Static temperature (C)")
    ax.set_ylabel("Model residual (ps)")
    ax.set_title("PVT residual vs calibration policy (assumption sweep, not Mao TC)")
    ax.legend()
    save_figure(fig, out / "pvt_modes")

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    subset = df[(df["mode"] == "periodic_calibration") & (df["offset_tc_ps_per_c"] == 1.0) & (df["bin_scale_tc_per_c"] == 3e-4)]
    ax.semilogx(subset["cal_interval_s"], subset["worst_abs_ps"], marker="o")
    ax.set_xlabel("Calibration interval (s)")
    ax.set_ylabel("Worst-case model residual (ps)")
    ax.set_title("Periodic-cal interval sensitivity (assumption coefficients)")
    save_figure(fig, out / "cal_interval_sensitivity")

    worst = float(df["worst_abs_ps"].max())
    params = {
        "t_min_c": T_MIN_C,
        "t_max_c": T_MAX_C,
        "t_ref_c": T_REF_C,
        "mao_resolution_tc_ps_per_c": MAO_RESOLUTION_TC_PS_PER_C,
        "mao_resolution_tc_note": "literature resolution TC; not used as residual error coefficient",
        "offset_tc_sweep_ps_per_c": list(OFFSET_TC_SWEEP_PS_PER_C),
        "bin_scale_tc_sweep_per_c": list(BIN_SCALE_TC_SWEEP_PER_C),
        "ramp_rate_c_per_s": RAMP_RATE_C_PER_S,
        "continuous_lag_s": CONTINUOUS_LAG_S,
        "parameter_provenance": {
            "operating_range": "requirement 10-40 C",
            "mao_resolution_tc": "literature (resolution only)",
            "offset_and_bin_sweeps": "engineering assumption",
            "ramp_rate": "engineering assumption",
        },
        "fast": fast,
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.pvt",
        random_seed=DEFAULT_SEED,
        input_parameters=params,
        extra={"worst_abs_residual_ps_over_sweep": worst},
    )
    write_json(out / "summary.json", {"worst_abs_residual_ps_over_sweep": worst})
    (out / "interpretation.md").write_text(
        f"""# PVT / temperature model

**Classification:** model-based simulation.

Operating range exercised: {T_MIN_C:.0f} to {T_MAX_C:.0f} C.
Mao 2022 resolution TC = {MAO_RESOLUTION_TC_PS_PER_C} ps/C is cited as literature and is
**not** the residual used here. Residual coefficients are swept assumptions.

Worst |residual| over the assumption sweep: {worst:.3f} ps.
Continuous/online calibration is limited by modelled lag and ramp rate, not by Mao's LSB TC.

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "table": df}
