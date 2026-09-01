"""Signed coarse + fine timestamp representation model.

Classification: model-based simulation of arithmetic/range feasibility.
This does not demonstrate clock accuracy over ±1 s.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure

FINE_QUANT_S = 1.0e-12  # 1 ps digital quantization; not physical resolution
RANGE_S = 1.0  # ±1 s signed requirement
CANDIDATE_COARSE_HZ = (100e6, 200e6, 400e6, 500e6)


def combine(n_coarse: np.ndarray | int, t_fine_s: np.ndarray | float, t_ref_s: float) -> np.ndarray:
    """Delta_t = N * T_ref + t_fine. N is signed. Units: seconds."""
    return np.asarray(n_coarse, dtype=np.int64) * float(t_ref_s) + np.asarray(t_fine_s, dtype=float)


def quantize_fine(t_fine_s: np.ndarray | float, quantum_s: float = FINE_QUANT_S) -> np.ndarray:
    """Round fine time onto a quantum. Units: seconds."""
    q = float(quantum_s)
    return np.round(np.asarray(t_fine_s, dtype=float) / q) * q


def split(delta_t_s: np.ndarray | float, t_ref_s: float) -> tuple[np.ndarray, np.ndarray]:
    """Floor-split a signed interval into coarse count and remainder in [0, T_ref)."""
    t = np.asarray(delta_t_s, dtype=float)
    n = np.floor(t / t_ref_s).astype(np.int64)
    remainder = t - n.astype(float) * t_ref_s
    # Numerical guard for values that land on a negative multiple of T_ref.
    snap = remainder < 0
    n = n - snap.astype(np.int64)
    remainder = np.where(snap, remainder + t_ref_s, remainder)
    return n, remainder


def signed_counter_bits(max_abs_counts: int) -> int:
    """Minimum two's-complement width to represent [-max, +max]."""
    if max_abs_counts < 0:
        raise ValueError("max_abs_counts must be >= 0")
    span = 2 * int(max_abs_counts) + 1
    return int(math.ceil(math.log2(span))) if span > 1 else 1


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    del seed, fast
    out = outputs_dir("coarse_fine")
    test_points_s = np.array(
        [
            -RANGE_S,
            -RANGE_S + FINE_QUANT_S,
            -2.5e-8,
            -1.0e-8,
            -FINE_QUANT_S,
            0.0,
            FINE_QUANT_S,
            1.0e-8,
            2.5e-8,
            RANGE_S - FINE_QUANT_S,
            RANGE_S,
        ]
    )

    rows = []
    width_rows = []
    for f_hz in CANDIDATE_COARSE_HZ:
        t_ref = 1.0 / f_hz
        n, rem = split(test_points_s, t_ref)
        rem_q = quantize_fine(rem)
        recon = combine(n, rem_q, t_ref)
        err = recon - test_points_s
        for t, n_i, r, rq, rec, e in zip(test_points_s, n, rem, rem_q, recon, err, strict=True):
            rows.append(
                {
                    "coarse_hz": f_hz,
                    "t_ref_s": t_ref,
                    "true_delta_t_s": t,
                    "n_coarse": int(n_i),
                    "t_fine_s": r,
                    "t_fine_quant_s": rq,
                    "reconstructed_s": rec,
                    "error_s": e,
                    "error_ps": e * 1e12,
                    "near_zero": abs(t) <= 2 * FINE_QUANT_S,
                    "near_plus_one_s": abs(t - RANGE_S) <= 2 * FINE_QUANT_S,
                    "near_minus_one_s": abs(t + RANGE_S) <= 2 * FINE_QUANT_S,
                    "near_plus_tref": abs(t - t_ref) <= 2 * FINE_QUANT_S,
                    "near_minus_tref": abs(t + t_ref) <= 2 * FINE_QUANT_S,
                    "result_classification": "model-based simulation",
                }
            )
        max_counts = int(math.ceil(RANGE_S * f_hz))
        width_rows.append(
            {
                "coarse_hz": f_hz,
                "t_ref_ns": t_ref * 1e9,
                "max_abs_coarse_counts_for_pm_1s": max_counts,
                "signed_counter_bits": signed_counter_bits(max_counts),
                "arithmetic_range_ok": True,
                "clock_accuracy_demonstrated": False,
                "note": (
                    "Bit width is arithmetic feasibility only. Meeting 20 ps over 1 s "
                    "is a reference-clock stability problem (NIST SP 1065 / IEEE 1139), "
                    "not a counter-width problem."
                ),
                "result_classification": "model-based simulation",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(out / "boundary_reconstruction.csv", index=False)
    widths = pd.DataFrame(width_rows)
    widths.to_csv(out / "counter_widths.csv", index=False)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    for f_hz, grp in df.groupby("coarse_hz"):
        ax.plot(grp["true_delta_t_s"], grp["error_ps"], marker="o", linestyle="none", label=f"{f_hz/1e6:.0f} MHz")
    ax.set_xlabel("True signed interval (s)")
    ax.set_ylabel("Reconstruction error after 1 ps fine quantization (ps)")
    ax.set_title("Coarse+fine arithmetic (not clock accuracy)")
    ax.legend()
    save_figure(fig, out / "reconstruction_error")

    max_abs_err_ps = float(np.max(np.abs(df["error_ps"])))
    params = {
        "fine_quantization_s": FINE_QUANT_S,
        "signed_range_s": RANGE_S,
        "candidate_coarse_hz": list(CANDIDATE_COARSE_HZ),
        "parameter_provenance": {
            "fine_quantization_s": "S14 resolution requirement (digital LSB, not physical resolution)",
            "signed_range_s": "S14 signed range requirement",
            "candidate_coarse_hz": "engineering candidates",
        },
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.coarse_fine",
        random_seed=DEFAULT_SEED,
        input_parameters=params,
        extra={"max_abs_reconstruction_error_ps": max_abs_err_ps},
    )
    write_json(
        out / "summary.json",
        {
            "max_abs_reconstruction_error_ps": max_abs_err_ps,
            "counter_widths": widths.to_dict(orient="records"),
        },
    )
    (out / "interpretation.md").write_text(
        f"""# Coarse + fine signed range

**Classification:** model-based simulation of representation/arithmetic.
Maximum |error| after 1 ps fine quantization on the tested points: {max_abs_err_ps:.4f} ps.

1 ps digital quantization is not 1 ps physical resolution.
A ±1 s interval at 20 ps precision is dominated by 10 MHz / UTC reference stability,
not by the integer counter width. See NIST SP 1065 and IEEE 1139.

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "table": df, "widths": widths}
