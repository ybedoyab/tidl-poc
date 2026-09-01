import numpy as np
import pytest

from tidl_poc.common.rng import rng
from tidl_poc.models.channel_scaling import (
    ACTIVITY_LEVELS,
    CROSSTALK_SWEEP_PS_PER_EXTRA,
    covariance_matrix,
    pairwise_skew,
    precision_rms_ps,
    sample_channels,
)


def test_covariance_positive_semidefinite():
    k = covariance_matrix(16, 6.0, 4.0)
    eig = np.linalg.eigvalsh(k)
    assert np.all(eig >= -1e-9)


def test_common_mode_rank_one_plus_diagonal():
    k = covariance_matrix(8, 3.0, 5.0)
    remainder = k - (3.0**2) * np.eye(8)
    rank = np.linalg.matrix_rank(remainder, tol=1e-8)
    assert rank == 1


def test_pairwise_skew_from_offsets_antisymmetric():
    offsets = rng(0).normal(0.0, 8.0, size=8)
    skew = pairwise_skew(offsets)
    assert skew == pytest.approx(-skew.T, abs=1e-12)
    assert np.allclose(np.diag(skew), 0.0)


def test_shared_offsets_recovered_at_every_activity_level():
    offsets = rng(1).normal(0.0, 8.0, size=16)
    for n_active in ACTIVITY_LEVELS:
        samples = sample_channels(16, 8000, rng(10 + n_active), n_active, offsets=offsets, crosstalk=0.0)
        assert samples.mean(axis=0) == pytest.approx(offsets, abs=0.4)


def test_crosstalk_increases_precision_rms_not_static_offset():
    offsets = np.linspace(-8.0, 8.0, 16)
    low = sample_channels(16, 8000, rng(3), n_active=1, offsets=offsets, crosstalk=1.6)
    high = sample_channels(16, 8000, rng(4), n_active=16, offsets=offsets, crosstalk=1.6)
    assert precision_rms_ps(high) > precision_rms_ps(low)
    quiet = sample_channels(16, 8000, rng(5), n_active=16, offsets=offsets, crosstalk=0.0)
    assert np.allclose(quiet.mean(axis=0), offsets, atol=0.4)


def test_crosstalk_sweep_includes_requested_points():
    assert ACTIVITY_LEVELS == (1, 2, 4, 8, 16)
    assert 0.0 in CROSSTALK_SWEEP_PS_PER_EXTRA
    assert 1.6 in CROSSTALK_SWEEP_PS_PER_EXTRA
