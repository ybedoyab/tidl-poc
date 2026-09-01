"""Temperature / PVT residual timing model for 10-40 C.

Classification: model-based simulation.

Calibration is a time-domain state: at each calibration epoch the modelled
drift is stored, and the residual is current_drift minus that stored value
(zero at the epoch). Mao et al. 2022 quote 0.0002 ps/C as a *resolution*
temperature coefficient; that coefficient is not a residual timestamp-error
coefficient and is not used as the residual model here.
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
STEP_TIME_S = 100.0
# Kwiatkowski et al. 2023: 21 ps channel offset over 0-40 C => 0.525 ps/C.
# Literature evidence only; not this board.
KWIATKOWSKI_OFFSET_TC_PS_PER_C = 0.525
KWIATKOWSKI_OFFSET_SPAN_0_40C_PS = 21.0


def modeled_drift_ps(
    temp_c: np.ndarray | float,
    offset_tc_ps_per_c: float,
    bin_scale_tc_per_c: float,
    t_ref_c: float = T_REF_C,
) -> np.ndarray:
    """Open-loop drift relative to t_ref_c. Units: ps."""
    delta_t_c = np.asarray(temp_c, dtype=float) - float(t_ref_c)
    offset = offset_tc_ps_per_c * delta_t_c
    bin_term = NOMINAL_BIN_PS * bin_scale_tc_per_c * delta_t_c
    return offset + bin_term


def residual_no_cal(
    delta_t_c: np.ndarray,
    offset_tc: float,
    bin_scale_tc: float,
) -> np.ndarray:
    """Open-loop residual vs T_ref (no updates). Units: ps."""
    return modeled_drift_ps(np.asarray(delta_t_c) + T_REF_C, offset_tc, bin_scale_tc)


def residual_periodic_series(
    t_s: np.ndarray,
    temp_c: np.ndarray,
    offset_tc: float,
    bin_scale_tc: float,
    interval_s: float,
) -> np.ndarray:
    """Periodic calibration state.

    At t0 and every interval_s thereafter the LUT stores the current modelled
    drift, so the residual at those samples is identically zero. Between epochs
    residual = drift(T(t)) - drift(T(t_last_cal)).
    """
    if interval_s <= 0:
        raise ValueError("interval_s must be > 0")
    t_s = np.asarray(t_s, dtype=float)
    drift = modeled_drift_ps(temp_c, offset_tc, bin_scale_tc)
    t0 = float(t_s[0])
    epoch = np.floor((t_s - t0) / float(interval_s)).astype(int)
    residual = np.empty_like(drift)
    last_epoch = epoch[0] - 1
    stored = 0.0
    for i in range(t_s.size):
        if epoch[i] != last_epoch:
            stored = float(drift[i])
            last_epoch = int(epoch[i])
            residual[i] = 0.0
        else:
            residual[i] = drift[i] - stored
    return residual


def residual_continuous_series(
    t_s: np.ndarray,
    temp_c: np.ndarray,
    offset_tc: float,
    bin_scale_tc: float,
    lag_s: float,
) -> np.ndarray:
    """Online calibration with a causal lag. Residual is zero at t0 (immediate first cal)."""
    t_s = np.asarray(t_s, dtype=float)
    drift = modeled_drift_ps(temp_c, offset_tc, bin_scale_tc)
    lagged_t = t_s - float(lag_s)
    stored = np.interp(lagged_t, t_s, drift, left=float(drift[0]))
    residual = drift - stored
    residual[0] = 0.0
    return residual


def residual_no_cal_series(
    t_s: np.ndarray,
    temp_c: np.ndarray,
    offset_tc: float,
    bin_scale_tc: float,
) -> np.ndarray:
    """Single calibration at T_ref (LUT frozen). Not a time-domain update."""
    del t_s
    return modeled_drift_ps(temp_c, offset_tc, bin_scale_tc)


def residual_continuous(
    delta_t_c: np.ndarray,
    offset_tc: float,
    bin_scale_tc: float,
    lag_s: float,
    ramp_c_per_s: float,
) -> np.ndarray:
    """Lag-limited residual for a constant ramp rate. Kept for simple unit tests."""
    lag_c = lag_s * ramp_c_per_s
    return residual_no_cal(np.full_like(np.asarray(delta_t_c, dtype=float), lag_c), offset_tc, bin_scale_tc)


def profile_static(t_s: np.ndarray, t_hold_c: float) -> np.ndarray:
    return np.full_like(np.asarray(t_s, dtype=float), float(t_hold_c))


def profile_ramp(t_s: np.ndarray, t_start_c: float, rate_c_per_s: float) -> np.ndarray:
    t_s = np.asarray(t_s, dtype=float)
    return np.clip(float(t_start_c) + float(rate_c_per_s) * t_s, T_MIN_C, T_MAX_C)


def profile_step(t_s: np.ndarray, t_before_c: float, t_after_c: float, t_step_s: float) -> np.ndarray:
    t_s = np.asarray(t_s, dtype=float)
    return np.where(t_s < float(t_step_s), float(t_before_c), float(t_after_c))


def _metrics(residual_ps: np.ndarray) -> tuple[float, float]:
    return float(np.max(np.abs(residual_ps))), float(np.sqrt(np.mean(residual_ps**2)))


def _time_axis(fast: bool) -> np.ndarray:
    duration_s = 600.0 if fast else 1800.0
    dt_s = 0.5 if fast else 0.2
    n = int(round(duration_s / dt_s)) + 1
    return np.linspace(0.0, duration_s, n)


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    del seed
    out = outputs_dir("pvt")
    t_s = _time_axis(fast)
    profiles = {
        "static": profile_static(t_s, T_MAX_C),
        "ramp": profile_ramp(t_s, T_MIN_C, RAMP_RATE_C_PER_S),
        "step": profile_step(t_s, T_REF_C, T_MAX_C, STEP_TIME_S),
    }

    rows = []
    for offset_tc in OFFSET_TC_SWEEP_PS_PER_C:
        for bin_tc in BIN_SCALE_TC_SWEEP_PER_C:
            for profile_name, temp_c in profiles.items():
                none = residual_no_cal_series(t_s, temp_c, offset_tc, bin_tc)
                w, r = _metrics(none)
                rows.append(
                    {
                        "mode": "no_calibration",
                        "profile": profile_name,
                        "offset_tc_ps_per_c": offset_tc,
                        "bin_scale_tc_per_c": bin_tc,
                        "cal_interval_s": np.nan,
                        "worst_abs_ps": w,
                        "rms_ps": r,
                        "result_classification": "model-based simulation",
                    }
                )
                for interval in CAL_INTERVALS_S:
                    periodic = residual_periodic_series(t_s, temp_c, offset_tc, bin_tc, interval)
                    w, r = _metrics(periodic)
                    rows.append(
                        {
                            "mode": "periodic_calibration",
                            "profile": profile_name,
                            "offset_tc_ps_per_c": offset_tc,
                            "bin_scale_tc_per_c": bin_tc,
                            "cal_interval_s": interval,
                            "worst_abs_ps": w,
                            "rms_ps": r,
                            "result_classification": "model-based simulation",
                        }
                    )
                cont = residual_continuous_series(t_s, temp_c, offset_tc, bin_tc, CONTINUOUS_LAG_S)
                w, r = _metrics(cont)
                rows.append(
                    {
                        "mode": "continuous_online",
                        "profile": profile_name,
                        "offset_tc_ps_per_c": offset_tc,
                        "bin_scale_tc_per_c": bin_tc,
                        "cal_interval_s": CONTINUOUS_LAG_S,
                        "worst_abs_ps": w,
                        "rms_ps": r,
                        "result_classification": "model-based simulation",
                    }
                )

    df = pd.DataFrame(rows)
    df.to_csv(out / "pvt_residuals.csv", index=False)

    off, btc = 1.0, 3e-4
    temp_ramp = profiles["ramp"]
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(t_s, residual_no_cal_series(t_s, temp_ramp, off, btc), label="no calibration (LUT frozen at T_ref)")
    for interval in (10.0, 60.0, 600.0):
        ax.plot(
            t_s,
            residual_periodic_series(t_s, temp_ramp, off, btc, interval),
            label=f"periodic {interval:.0f} s",
        )
    ax.plot(
        t_s,
        residual_continuous_series(t_s, temp_ramp, off, btc, CONTINUOUS_LAG_S),
        label="continuous (0.2 s lag)",
    )
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Model residual (ps)")
    ax.set_title("Ramp profile: time-domain calibration state (assumption coefficients)")
    ax.legend()
    save_figure(fig, out / "pvt_modes")

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    for profile_name, style in (("ramp", "o-"), ("step", "s--"), ("static", "^:")):
        subset = df[
            (df["mode"] == "periodic_calibration")
            & (df["profile"] == profile_name)
            & (df["offset_tc_ps_per_c"] == 1.0)
            & (df["bin_scale_tc_per_c"] == 3e-4)
        ]
        ax.semilogx(subset["cal_interval_s"], subset["worst_abs_ps"], style, label=f"{profile_name} worst |r|")
        ax.semilogx(subset["cal_interval_s"], subset["rms_ps"], style, alpha=0.6, label=f"{profile_name} RMS")
    ax.set_xlabel("Calibration interval (s)")
    ax.set_ylabel("Residual (ps)")
    ax.set_title("Periodic-cal interval sensitivity (time-domain state)")
    ax.legend(fontsize=8)
    save_figure(fig, out / "cal_interval_sensitivity")

    # Static + periodic must collapse: after the first epoch residual is ~0.
    static_periodic = df[
        (df["mode"] == "periodic_calibration") & (df["profile"] == "static")
    ]
    ramp_periodic = df[
        (df["mode"] == "periodic_calibration")
        & (df["profile"] == "ramp")
        & (df["offset_tc_ps_per_c"] == 1.0)
        & (df["bin_scale_tc_per_c"] == 3e-4)
    ]

    worst = float(df["worst_abs_ps"].max())
    kwiat_uncomp_10_40 = KWIATKOWSKI_OFFSET_TC_PS_PER_C * (T_MAX_C - T_MIN_C)
    kwiat_rows = pd.DataFrame(
        [
            {
                "temp_c": t,
                "uncompensated_offset_vs_tref_ps": KWIATKOWSKI_OFFSET_TC_PS_PER_C * (t - T_REF_C),
                "after_temperature_specific_recalibration_ps": 0.0,
                "source": (
                    "literature evidence — Kwiatkowski et al. 2023, "
                    "DOI 10.1016/j.measurement.2023.112510"
                ),
                "result_classification": "model-based simulation",
            }
            for t in (T_MIN_C, T_REF_C, T_MAX_C)
        ]
    )
    kwiat_rows.to_csv(out / "kwiatkowski_offset_anchor.csv", index=False)

    extra = {
        "worst_abs_residual_ps_over_sweep": worst,
        "static_periodic_max_worst_abs_ps": float(static_periodic["worst_abs_ps"].max()),
        "ramp_periodic_worst_by_interval_ps": {
            str(int(row.cal_interval_s)): {"worst_abs_ps": row.worst_abs_ps, "rms_ps": row.rms_ps}
            for row in ramp_periodic.itertuples(index=False)
        },
        "kwiatkowski_offset_tc_ps_per_c": KWIATKOWSKI_OFFSET_TC_PS_PER_C,
        "kwiatkowski_uncompensated_10_to_40C_ps": kwiat_uncomp_10_40,
        "kwiatkowski_temp_specific_recal_residual_ps": 0.0,
        "kwiatkowski_temp_specific_recal_note": (
            "paper: temperature-specific recalibration kept split-signal interval "
            "precision <3 ps over 0-40 C; no interpolation invented here"
        ),
    }
    params = {
        "t_min_c": T_MIN_C,
        "t_max_c": T_MAX_C,
        "t_ref_c": T_REF_C,
        "mao_resolution_tc_ps_per_c": MAO_RESOLUTION_TC_PS_PER_C,
        "mao_resolution_tc_note": "literature resolution TC; not used as residual error coefficient",
        "kwiatkowski_offset_tc_ps_per_c": KWIATKOWSKI_OFFSET_TC_PS_PER_C,
        "kwiatkowski_offset_tc_note": "literature channel-offset TC; additional scenario, not our board",
        "offset_tc_sweep_ps_per_c": list(OFFSET_TC_SWEEP_PS_PER_C),
        "bin_scale_tc_sweep_per_c": list(BIN_SCALE_TC_SWEEP_PER_C),
        "ramp_rate_c_per_s": RAMP_RATE_C_PER_S,
        "continuous_lag_s": CONTINUOUS_LAG_S,
        "profiles": ["static", "ramp", "step"],
        "model": "time-domain calibration state; residual zero at each epoch",
        "parameter_provenance": {
            "operating_range": "requirement 10-40 C",
            "mao_resolution_tc": "literature (resolution only)",
            "kwiatkowski_offset_tc": "literature (channel offset 0-40 C)",
            "offset_and_bin_sweeps": "engineering allocation / assumption sweep",
            "ramp_rate": "engineering allocation",
        },
        "fast": fast,
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.pvt",
        random_seed=DEFAULT_SEED,
        input_parameters=params,
        extra=extra,
    )
    write_json(out / "summary.json", extra)
    (out / "interpretation.md").write_text(
        f"""# PVT / temperature model

**Classification:** model-based simulation.

Operating range: {T_MIN_C:.0f} to {T_MAX_C:.0f} C.
Calibration is a stored drift state. Periodic updates zero the residual at each
epoch. A static soak after that first epoch has ~0 residual; ramps and steps
do not.

Mao 2022 resolution TC = {MAO_RESOLUTION_TC_PS_PER_C} ps/C is literature and is
**not** the residual used here.

Kwiatkowski 2023 channel-offset TC = {KWIATKOWSKI_OFFSET_TC_PS_PER_C} ps/C
(literature; 21 ps over 0-40 C). Uncompensated 10-40 C movement =
{kwiat_uncomp_10_40:.3f} ps. Temperature-specific recalibration residual in this
file is 0 ps at each static temperature (no interpolation).

Worst |residual| over the assumption sweep: {worst:.3f} ps.
Static + periodic max worst-|r| (should be ~0): {extra["static_periodic_max_worst_abs_ps"]:.6f} ps.

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "table": df}
