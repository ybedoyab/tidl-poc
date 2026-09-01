"""16-channel scaling, covariance, and simultaneous-activity model.

Classification: model-based simulation. Coefficients are engineering assumptions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure
from tidl_poc.common.rng import rng as make_rng

N_CHANNELS = 16
N_SAMPLES_FAST = 8_000
N_SAMPLES_FULL = 80_000
# Assumption: independent channel offset RMS, common-mode RMS, pairwise extra, crosstalk.
SIGMA_OFFSET_PS = 8.0
SIGMA_COMMON_PS = 4.0
SIGMA_INDEP_PS = 6.0
CROSSTALK_PS_PER_ACTIVE = 0.4


def covariance_matrix(n: int, sigma_indep: float, sigma_common: float) -> np.ndarray:
    """K = sigma_indep^2 I + sigma_common^2 1 1^T. Units: ps^2."""
    return (sigma_indep**2) * np.eye(n) + (sigma_common**2) * np.ones((n, n))


def sample_channels(
    n_channels: int,
    n_samples: int,
    rng: np.random.Generator,
    n_active: int,
    sigma_offset: float = SIGMA_OFFSET_PS,
    sigma_common: float = SIGMA_COMMON_PS,
    sigma_indep: float = SIGMA_INDEP_PS,
    crosstalk: float = CROSSTALK_PS_PER_ACTIVE,
) -> np.ndarray:
    offsets = rng.normal(0.0, sigma_offset, size=n_channels)
    common = rng.normal(0.0, sigma_common, size=(n_samples, 1))
    indep = rng.normal(0.0, sigma_indep, size=(n_samples, n_channels))
    active = max(n_active, 1)
    xtalk = crosstalk * (active - 1)
    xtalk_noise = rng.normal(0.0, xtalk, size=(n_samples, n_channels)) if xtalk > 0 else 0.0
    return offsets[None, :] + common + indep + xtalk_noise


def pairwise_skew(samples_ps: np.ndarray) -> np.ndarray:
    """Mean pairwise differences over samples. Shape (n, n)."""
    mean = samples_ps.mean(axis=0)
    return mean[:, None] - mean[None, :]


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    out = outputs_dir("channel_scaling")
    gen = make_rng(seed)
    n_samples = N_SAMPLES_FAST if fast else N_SAMPLES_FULL
    single = sample_channels(N_CHANNELS, n_samples, gen, n_active=1)
    simultaneous = sample_channels(N_CHANNELS, n_samples, make_rng(seed + 1), n_active=N_CHANNELS)
    cov_model = covariance_matrix(N_CHANNELS, SIGMA_INDEP_PS, SIGMA_COMMON_PS)
    cov_emp = np.cov(simultaneous, rowvar=False)

    skew = pairwise_skew(simultaneous)
    tri = skew[np.triu_indices(N_CHANNELS, k=1)]
    worst_channel = float(np.max(np.abs(simultaneous.mean(axis=0))))
    worst_pair = float(np.max(np.abs(tri)))
    rms_single = float(np.std(single, ddof=1))
    rms_simult = float(np.std(simultaneous, ddof=1))

    pd.DataFrame(cov_emp).to_csv(out / "covariance_empirical.csv", index=False, header=False)
    pd.DataFrame(cov_model).to_csv(out / "covariance_model.csv", index=False, header=False)
    metrics = pd.DataFrame(
        [
            {
                "n_channels": N_CHANNELS,
                "worst_channel_mean_offset_ps": worst_channel,
                "worst_pair_mean_skew_ps": worst_pair,
                "pairwise_skew_rms_ps": float(np.sqrt(np.mean(tri**2))),
                "rms_single_active_ps": rms_single,
                "rms_simultaneous_ps": rms_simult,
                "crosstalk_ps_per_extra_active": CROSSTALK_PS_PER_ACTIVE,
                "result_classification": "model-based simulation",
            }
        ]
    )
    metrics.to_csv(out / "metrics.csv", index=False)
    pd.DataFrame({"pairwise_skew_ps": tri, "result_classification": "model-based simulation"}).to_csv(
        out / "pairwise_skew.csv", index=False
    )

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    im = ax.imshow(cov_emp, cmap="gray")
    ax.set_title("Empirical 16x16 covariance (ps^2), simultaneous activity")
    ax.set_xlabel("Channel")
    ax.set_ylabel("Channel")
    fig.colorbar(im, ax=ax, label="ps^2")
    save_figure(fig, out / "covariance_heatmap")

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.hist(tri, bins=24, color="0.45")
    ax.set_xlabel("Pairwise mean skew (ps)")
    ax.set_ylabel("Count")
    ax.set_title("Pairwise channel skew (model-based)")
    save_figure(fig, out / "pairwise_skew_hist")

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(["single-active", "16 simultaneous"], [rms_single, rms_simult], color="0.5")
    ax.set_ylabel("Sample RMS (ps)")
    ax.set_title("Activity-dependent RMS including assumed crosstalk")
    save_figure(fig, out / "activity_rms")

    params = {
        "n_channels": N_CHANNELS,
        "n_samples": n_samples,
        "sigma_offset_ps": SIGMA_OFFSET_PS,
        "sigma_common_ps": SIGMA_COMMON_PS,
        "sigma_indep_ps": SIGMA_INDEP_PS,
        "crosstalk_ps_per_extra_active": CROSSTALK_PS_PER_ACTIVE,
        "parameter_provenance": "all coefficients are engineering assumptions",
        "fast": fast,
    }
    extra = {
        "worst_channel_mean_offset_ps": worst_channel,
        "worst_pair_mean_skew_ps": worst_pair,
        "rms_single_active_ps": rms_single,
        "rms_simultaneous_ps": rms_simult,
        "model_cov_trace": float(np.trace(cov_model)),
        "empirical_cov_trace": float(np.trace(cov_emp)),
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.channel_scaling",
        random_seed=seed,
        input_parameters=params,
        extra=extra,
    )
    write_json(out / "summary.json", extra)
    (out / "interpretation.md").write_text(
        f"""# 16-channel scaling

**Classification:** model-based simulation. Preferred architecture is simultaneous
measurement on all 16 channels; channel switching remains an alternate concept.

Worst-channel mean offset = {worst_channel:.3f} ps
Worst-pair mean skew = {worst_pair:.3f} ps
RMS single-active = {rms_single:.3f} ps
RMS simultaneous = {rms_simult:.3f} ps

Crosstalk is an assumed linear penalty versus extra active channels, not a measured
FPGA coupling coefficient.

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "metrics": metrics, "cov_model": cov_model, "cov_emp": cov_emp}
