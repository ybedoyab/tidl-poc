import numpy as np
import pytest

from tidl_poc.models.channel_scaling import covariance_matrix, pairwise_skew, sample_channels
from tidl_poc.common.rng import rng


def test_covariance_positive_semidefinite():
    k = covariance_matrix(16, 6.0, 4.0)
    eig = np.linalg.eigvalsh(k)
    assert np.all(eig >= -1e-9)


def test_common_mode_rank_one_plus_diagonal():
    k = covariance_matrix(8, 3.0, 5.0)
    # After removing independent diagonal, remainder is rank-1.
    remainder = k - (3.0**2) * np.eye(8)
    rank = np.linalg.matrix_rank(remainder, tol=1e-8)
    assert rank == 1


def test_pairwise_skew_antisymmetric():
    samples = sample_channels(8, 500, rng(0), n_active=8)
    skew = pairwise_skew(samples)
    assert skew == pytest.approx(-skew.T, abs=1e-12)
    assert np.allclose(np.diag(skew), 0.0)


def test_simultaneous_rms_not_smaller_than_single_when_crosstalk_positive():
    gen = rng(1)
    single = sample_channels(16, 4000, gen, n_active=1)
    simult = sample_channels(16, 4000, rng(2), n_active=16)
    # Crosstalk adds variance; allow statistical slack.
    assert np.std(simult) >= np.std(single) * 0.9
