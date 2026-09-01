"""16-channel scaling, covariance, and simultaneous-activity model.

Classification: model-based simulation. Coefficients are engineering allocations.
Static per-channel offsets are drawn once and reused across activity levels.
Crosstalk is a sensitivity sweep, not a single privileged value.
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
ACTIVITY_LEVELS = (1, 2, 4, 8, 16)
CROSSTALK_SWEEP_PS_PER_EXTRA = (0.0, 0.2, 0.4, 0.8, 1.6)
# Representative heatmap point only; not a privileged hardware value.
HEATMAP_CROSSTALK_PS = 0.4
SIGMA_OFFSET_PS = 8.0
SIGMA_COMMON_PS = 4.0
SIGMA_INDEP_PS = 6.0


def covariance_matrix(n: int, sigma_indep: float, sigma_common: float) -> np.ndarray:
    """K = sigma_indep^2 I + sigma_common^2 1 1^T. Units: ps^2."""
    return (sigma_indep**2) * np.eye(n) + (sigma_common**2) * np.ones((n, n))


def sample_channels(
    n_channels: int,
    n_samples: int,
    rng: np.random.Generator,
    n_active: int,
    offsets: np.ndarray | None = None,
    sigma_offset: float = SIGMA_OFFSET_PS,
    sigma_common: float = SIGMA_COMMON_PS,
    sigma_indep: float = SIGMA_INDEP_PS,
    crosstalk: float = 0.0,
) -> np.ndarray:
    """Return (n_samples, n_channels) timestamps in ps.

    `offsets` is the static per-channel bias. If omitted, a new draw is made
    (tests only). Production comparisons must pass the same offsets.
    """
    if offsets is None:
        offsets = rng.normal(0.0, sigma_offset, size=n_channels)
    offsets = np.asarray(offsets, dtype=float)
    common = rng.normal(0.0, sigma_common, size=(n_samples, 1))
    indep = rng.normal(0.0, sigma_indep, size=(n_samples, n_channels))
    extra_active = max(int(n_active) - 1, 0)
    xtalk_sigma = float(crosstalk) * extra_active
    xtalk_noise = rng.normal(0.0, xtalk_sigma, size=(n_samples, n_channels)) if xtalk_sigma > 0 else 0.0
    return offsets[None, :] + common + indep + xtalk_noise


def pairwise_skew(samples_or_offsets_ps: np.ndarray) -> np.ndarray:
    """Mean pairwise differences. 1-D input is treated as static offsets."""
    arr = np.asarray(samples_or_offsets_ps, dtype=float)
    if arr.ndim == 1:
        mean = arr
    else:
        mean = arr.mean(axis=0)
    return mean[:, None] - mean[None, :]


def precision_rms_ps(samples_ps: np.ndarray) -> float:
    """RMS after removing the static per-channel mean. Units: ps."""
    demeaned = samples_ps - samples_ps.mean(axis=0, keepdims=True)
    return float(np.sqrt(np.mean(demeaned**2)))


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    out = outputs_dir("channel_scaling")
    gen = make_rng(seed)
    n_samples = N_SAMPLES_FAST if fast else N_SAMPLES_FULL
    offsets = gen.normal(0.0, SIGMA_OFFSET_PS, size=N_CHANNELS)
    noise_rng = make_rng(seed + 99)

    cov_model = covariance_matrix(N_CHANNELS, SIGMA_INDEP_PS, SIGMA_COMMON_PS)
    simultaneous = sample_channels(
        N_CHANNELS,
        n_samples,
        noise_rng,
        n_active=N_CHANNELS,
        offsets=offsets,
        crosstalk=HEATMAP_CROSSTALK_PS,
    )
    cov_emp = np.cov(simultaneous, rowvar=False)

    skew = pairwise_skew(offsets)
    tri = skew[np.triu_indices(N_CHANNELS, k=1)]
    worst_channel = float(np.max(np.abs(offsets)))
    worst_pair = float(np.max(np.abs(tri)))

    activity_rows = []
    for xtalk in CROSSTALK_SWEEP_PS_PER_EXTRA:
        for n_active in ACTIVITY_LEVELS:
            trial_rng = make_rng(seed + 1000 + int(n_active) + int(xtalk * 100))
            samples = sample_channels(
                N_CHANNELS,
                n_samples,
                trial_rng,
                n_active=n_active,
                offsets=offsets,
                crosstalk=xtalk,
            )
            recovered_offset_rms = float(np.sqrt(np.mean((samples.mean(axis=0) - offsets) ** 2)))
            activity_rows.append(
                {
                    "n_active": n_active,
                    "crosstalk_ps_per_extra_active": xtalk,
                    "static_worst_channel_offset_ps": worst_channel,
                    "static_worst_pair_skew_ps": worst_pair,
                    "precision_rms_ps": precision_rms_ps(samples),
                    "recovered_offset_rms_vs_true_ps": recovered_offset_rms,
                    "result_classification": "model-based simulation",
                }
            )
    activity_df = pd.DataFrame(activity_rows)
    activity_df.to_csv(out / "activity_crosstalk_sweep.csv", index=False)

    pd.DataFrame(cov_emp).to_csv(out / "covariance_empirical.csv", index=False, header=False)
    pd.DataFrame(cov_model).to_csv(out / "covariance_model.csv", index=False, header=False)
    metrics = pd.DataFrame(
        [
            {
                "n_channels": N_CHANNELS,
                "static_worst_channel_offset_ps": worst_channel,
                "static_worst_pair_skew_ps": worst_pair,
                "static_pairwise_skew_rms_ps": float(np.sqrt(np.mean(tri**2))),
                "heatmap_crosstalk_ps_per_extra_active": HEATMAP_CROSSTALK_PS,
                "offsets_shared_across_activity": True,
                "result_classification": "model-based simulation",
            }
        ]
    )
    metrics.to_csv(out / "metrics.csv", index=False)
    pd.DataFrame({"pairwise_static_skew_ps": tri, "result_classification": "model-based simulation"}).to_csv(
        out / "pairwise_skew.csv", index=False
    )

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    im = ax.imshow(cov_emp, cmap="gray")
    ax.set_title(f"Empirical 16x16 covariance (ps^2), 16-active, xtalk={HEATMAP_CROSSTALK_PS} ps (sweep point)")
    ax.set_xlabel("Channel")
    ax.set_ylabel("Channel")
    fig.colorbar(im, ax=ax, label="ps^2")
    save_figure(fig, out / "covariance_heatmap")

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.hist(tri, bins=24, color="0.45")
    ax.set_xlabel("Pairwise static skew from shared offsets (ps)")
    ax.set_ylabel("Count")
    ax.set_title("Static pairwise channel skew (independent of activity)")
    save_figure(fig, out / "pairwise_skew_hist")

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    for xtalk in CROSSTALK_SWEEP_PS_PER_EXTRA:
        sub = activity_df[activity_df["crosstalk_ps_per_extra_active"] == xtalk]
        ax.plot(sub["n_active"], sub["precision_rms_ps"], marker="o", label=f"xtalk {xtalk} ps/extra")
    ax.set_xlabel("Simultaneous active channels")
    ax.set_ylabel("Precision RMS after removing static offsets (ps)")
    ax.set_title("Activity vs precision; offsets held fixed")
    ax.legend()
    save_figure(fig, out / "activity_rms")

    xtalk0_1 = float(
        activity_df[
            (activity_df["n_active"] == 1) & (activity_df["crosstalk_ps_per_extra_active"] == 0.0)
        ]["precision_rms_ps"].iloc[0]
    )
    xtalk04_16 = float(
        activity_df[
            (activity_df["n_active"] == 16) & (activity_df["crosstalk_ps_per_extra_active"] == HEATMAP_CROSSTALK_PS)
        ]["precision_rms_ps"].iloc[0]
    )

    params = {
        "n_channels": N_CHANNELS,
        "n_samples": n_samples,
        "activity_levels": list(ACTIVITY_LEVELS),
        "crosstalk_sweep_ps_per_extra_active": list(CROSSTALK_SWEEP_PS_PER_EXTRA),
        "sigma_offset_ps": SIGMA_OFFSET_PS,
        "sigma_common_ps": SIGMA_COMMON_PS,
        "sigma_indep_ps": SIGMA_INDEP_PS,
        "parameter_provenance": "engineering allocations; crosstalk is a sweep not evidence",
        "fast": fast,
    }
    extra = {
        "static_worst_channel_offset_ps": worst_channel,
        "static_worst_pair_skew_ps": worst_pair,
        "precision_rms_1_active_xtalk0_ps": xtalk0_1,
        "precision_rms_16_active_xtalk0p4_ps": xtalk04_16,
        "model_cov_trace": float(np.trace(cov_model)),
        "empirical_cov_trace": float(np.trace(cov_emp)),
        "offsets_shared_across_activity": True,
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

Static offsets are one realisation, reused at activity 1/2/4/8/16.
Worst-channel static offset = {worst_channel:.3f} ps
Worst-pair static skew = {worst_pair:.3f} ps
Precision RMS (1-active, xtalk=0) = {xtalk0_1:.3f} ps
Precision RMS (16-active, xtalk=0.4 sweep point) = {xtalk04_16:.3f} ps

Crosstalk is an assumed linear penalty versus extra active channels, swept
rather than treated as a measured FPGA coupling coefficient.

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {
        "output_dir": str(out),
        "metrics": metrics,
        "activity": activity_df,
        "offsets": offsets,
        "cov_model": cov_model,
        "cov_emp": cov_emp,
    }
