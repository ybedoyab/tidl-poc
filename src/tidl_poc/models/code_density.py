"""Synthetic tapped-delay-line code-density calibration.

Classification: model-based simulation of an illustrative 512-bin TDL.
This is not an FPGA carry-chain measurement.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure
from tidl_poc.common.rng import rng as make_rng

# Illustrative coarse period. Not a claimed FPGA clock period.
DEFAULT_N_BINS = 512
DEFAULT_T_COARSE_S = 4.0e-9  # 4 ns, corresponding to an illustrative 250 MHz coarse clock
DEFAULT_SYSTEMATIC_AMPLITUDE = 0.25
DEFAULT_RANDOM_CV = 0.20
FAST_CAL_COUNTS = (10_000, 100_000, 1_000_000)
FULL_CAL_COUNTS = FAST_CAL_COUNTS + (10_000_000,)
N_VALIDATION = 50_000


def make_bin_widths(
    n_bins: int,
    t_coarse_s: float,
    rng: np.random.Generator,
    systematic_amplitude: float = DEFAULT_SYSTEMATIC_AMPLITUDE,
    random_cv: float = DEFAULT_RANDOM_CV,
) -> np.ndarray:
    """Positive bin widths summing to t_coarse_s. Units: seconds."""
    idx = np.arange(n_bins, dtype=float)
    systematic = 1.0 + systematic_amplitude * np.sin(2.0 * np.pi * idx / n_bins)
    random = 1.0 + random_cv * rng.normal(size=n_bins)
    raw = np.clip(systematic * random, 0.05, None)
    widths = raw * (t_coarse_s / raw.sum())
    if np.any(widths <= 0):
        raise RuntimeError("bin widths must be strictly positive")
    return widths


def edges_from_widths(widths_s: np.ndarray) -> np.ndarray:
    return np.concatenate(([0.0], np.cumsum(widths_s)))


def dnl_inl(widths_s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """DNL and INL in LSB relative to the mean bin width."""
    lsb = widths_s.mean()
    dnl = (widths_s / lsb) - 1.0
    inl = np.cumsum(dnl)
    return dnl, inl


def calibrate_widths(counts: np.ndarray, t_coarse_s: float) -> np.ndarray:
    """Code-density estimated widths. Zero-count bins get a tiny positive floor."""
    n = counts.sum()
    if n <= 0:
        raise ValueError("calibration sample count must be positive")
    occupancy = np.maximum(counts.astype(float), 0.5)
    occupancy *= n / occupancy.sum()
    return occupancy * (t_coarse_s / n)


def reconstruct(times_s: np.ndarray, true_edges_s: np.ndarray, cal_edges_s: np.ndarray) -> np.ndarray:
    """Map true event times through the TDL onto calibrated bin centres."""
    # Bin index for t in [edge_k, edge_{k+1}).
    bins = np.searchsorted(true_edges_s, times_s, side="right") - 1
    bins = np.clip(bins, 0, len(cal_edges_s) - 2)
    return 0.5 * (cal_edges_s[bins] + cal_edges_s[bins + 1])


def error_metrics(error_s: np.ndarray) -> dict[str, float]:
    abs_e = np.abs(error_s)
    return {
        "rms_ps": float(np.sqrt(np.mean(error_s**2)) * 1e12),
        "mae_ps": float(np.mean(abs_e) * 1e12),
        "p95_abs_ps": float(np.percentile(abs_e, 95) * 1e12),
        "p99_abs_ps": float(np.percentile(abs_e, 99) * 1e12),
        "max_abs_ps": float(np.max(abs_e) * 1e12),
    }


def run_once(
    n_cal: int,
    widths_s: np.ndarray,
    t_coarse_s: float,
    rng: np.random.Generator,
    n_validation: int = N_VALIDATION,
) -> dict:
    true_edges = edges_from_widths(widths_s)
    hits = rng.uniform(0.0, t_coarse_s, size=n_cal)
    counts, _ = np.histogram(hits, bins=true_edges)
    cal_widths = calibrate_widths(counts, t_coarse_s)
    cal_edges = edges_from_widths(cal_widths)
    val = rng.uniform(0.0, t_coarse_s, size=n_validation)
    recon = reconstruct(val, true_edges, cal_edges)
    metrics = error_metrics(recon - val)
    dnl_true, inl_true = dnl_inl(widths_s)
    dnl_cal, inl_cal = dnl_inl(cal_widths)
    dnl_resid = cal_widths / widths_s.mean() - widths_s / widths_s.mean()
    metrics.update(
        {
            "n_cal": n_cal,
            "dnl_true_peak_lsb": float(np.max(np.abs(dnl_true))),
            "inl_true_peak_lsb": float(np.max(np.abs(inl_true))),
            "dnl_cal_peak_lsb": float(np.max(np.abs(dnl_cal))),
            "inl_cal_peak_lsb": float(np.max(np.abs(inl_cal))),
            "dnl_width_residual_peak_lsb": float(np.max(np.abs(dnl_resid))),
        }
    )
    return {
        "metrics": metrics,
        "true_widths_s": widths_s,
        "cal_widths_s": cal_widths,
        "dnl_true": dnl_true,
        "inl_true": inl_true,
        "dnl_cal": dnl_cal,
        "inl_cal": inl_cal,
    }


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    out = outputs_dir("calibration")
    gen = make_rng(seed)
    n_bins = DEFAULT_N_BINS
    t_coarse = DEFAULT_T_COARSE_S
    widths = make_bin_widths(n_bins, t_coarse, gen)
    counts_list = FAST_CAL_COUNTS if fast else FULL_CAL_COUNTS

    # Independent RNG streams per sample-count so adding 1e7 does not reshuffle smaller runs.
    rows = []
    last = None
    for n_cal in counts_list:
        trial_rng = make_rng(seed + n_cal)
        last = run_once(n_cal, widths, t_coarse, trial_rng)
        rows.append(last["metrics"])
    df = pd.DataFrame(rows)
    df["result_classification"] = "model-based simulation"
    df.to_csv(out / "calibration_convergence.csv", index=False)

    pd.DataFrame(
        {
            "bin_index": np.arange(n_bins),
            "true_width_ps": widths * 1e12,
            "result_classification": "model-based simulation",
        }
    ).to_csv(out / "true_bin_widths.csv", index=False)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.semilogx(df["n_cal"], df["rms_ps"], marker="o", label="RMS")
    ax.semilogx(df["n_cal"], df["mae_ps"], marker="s", label="MAE")
    ax.semilogx(df["n_cal"], df["p95_abs_ps"], marker="^", label="P95 |error|")
    ax.set_xlabel("Calibration sample count")
    ax.set_ylabel("Validation timestamp error (ps)")
    ax.set_title("Synthetic code-density calibration convergence (not FPGA data)")
    ax.legend()
    save_figure(fig, out / "calibration_convergence")

    assert last is not None
    fig = plt.figure(figsize=(7.2, 6.2))
    ax1 = fig.add_subplot(2, 1, 1)
    ax1.plot(last["dnl_true"], label="true DNL")
    ax1.plot(last["dnl_cal"], label="calibrated-width DNL", alpha=0.85)
    ax1.set_ylabel("DNL (LSB)")
    ax1.set_title("Synthetic TDL DNL/INL before vs after code-density representation")
    ax1.legend()
    ax2 = fig.add_subplot(2, 1, 2)
    ax2.plot(last["inl_true"], label="true INL")
    ax2.plot(last["inl_cal"], label="calibrated-width INL", alpha=0.85)
    ax2.set_xlabel("Bin index")
    ax2.set_ylabel("INL (LSB)")
    ax2.legend()
    save_figure(fig, out / "dnl_inl")

    params = {
        "n_bins": n_bins,
        "t_coarse_s": t_coarse,
        "t_coarse_note": "illustrative; not a measured FPGA coarse period",
        "systematic_amplitude": DEFAULT_SYSTEMATIC_AMPLITUDE,
        "random_cv": DEFAULT_RANDOM_CV,
        "cal_counts": list(counts_list),
        "n_validation": N_VALIDATION,
        "fast": fast,
        "parameter_provenance": {
            "n_bins": "engineering assumption",
            "t_coarse_s": "engineering assumption",
            "bin_variation": "engineering assumption",
        },
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.code_density",
        random_seed=seed,
        input_parameters=params,
        extra={"final_metrics": last["metrics"]},
    )
    write_json(out / "summary.json", {"final_metrics": last["metrics"], "n_bins": n_bins})
    (out / "interpretation.md").write_text(
        f"""# Synthetic code-density calibration

**Classification:** model-based simulation. Not FPGA data.

Illustrative TDL: {n_bins} bins over {t_coarse * 1e9:.3f} ns (mean bin {t_coarse / n_bins * 1e12:.3f} ps).
Digital bin-centre reconstruction after code-density estimation does not prove 1 ps physical resolution.

Final (largest-N) validation RMS = {last["metrics"]["rms_ps"]:.4f} ps
MAE = {last["metrics"]["mae_ps"]:.4f} ps
P95 = {last["metrics"]["p95_abs_ps"]:.4f} ps
P99 = {last["metrics"]["p99_abs_ps"]:.4f} ps
max |error| = {last["metrics"]["max_abs_ps"]:.4f} ps

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "table": df, "widths_s": widths}
