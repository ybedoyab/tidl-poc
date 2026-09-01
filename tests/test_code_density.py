import numpy as np
import pytest

from tidl_poc.common.rng import rng
from tidl_poc.models.code_density import (
    DEFAULT_N_BINS,
    DEFAULT_T_COARSE_S,
    calibrate_widths,
    edges_from_widths,
    make_bin_widths,
    reconstruct,
    run_once,
)


def test_widths_positive_and_sum_to_period():
    widths = make_bin_widths(DEFAULT_N_BINS, DEFAULT_T_COARSE_S, rng(1))
    assert np.all(widths > 0)
    assert widths.sum() == pytest.approx(DEFAULT_T_COARSE_S, rel=1e-12)


def test_seed_reproducible():
    a = make_bin_widths(DEFAULT_N_BINS, DEFAULT_T_COARSE_S, rng(42))
    b = make_bin_widths(DEFAULT_N_BINS, DEFAULT_T_COARSE_S, rng(42))
    c = make_bin_widths(DEFAULT_N_BINS, DEFAULT_T_COARSE_S, rng(43))
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


def test_perfect_counts_recover_widths():
    widths = make_bin_widths(64, 4e-9, rng(0), systematic_amplitude=0.1, random_cv=0.05)
    # Occupancy exactly proportional to width.
    counts = np.round(widths / widths.min() * 1000)
    recovered = calibrate_widths(counts, 4e-9)
    rel = recovered / recovered.sum() - widths / widths.sum()
    assert np.max(np.abs(rel)) < 0.02


def test_reconstruction_uses_bin_centres():
    widths = np.array([1.0, 2.0, 1.0]) * 1e-9
    edges = edges_from_widths(widths)
    t = np.array([0.4e-9, 1.5e-9, 3.5e-9])
    recon = reconstruct(t, edges, edges)
    expected = 0.5 * (edges[:-1] + edges[1:])
    assert np.allclose(recon, expected)


def test_run_once_metrics_finite():
    widths = make_bin_widths(128, 4e-9, rng(7))
    out = run_once(20_000, widths, 4e-9, rng(8), n_validation=2000)
    assert out["metrics"]["rms_ps"] > 0
    assert np.isfinite(out["metrics"]["max_abs_ps"])
