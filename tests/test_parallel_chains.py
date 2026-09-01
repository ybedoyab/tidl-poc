from pathlib import Path

import numpy as np
import pytest

from tidl_poc.models.parallel_chains import (
    MAO_SSP_1_CHAIN_PS,
    MAO_SSP_10_CHAIN_PS,
    default_fit,
    fit_common_independent,
    sigma_total_ps,
)


def test_fit_recovers_literature_anchors():
    fit = default_fit()
    assert sigma_total_ps(1, fit) == pytest.approx(MAO_SSP_1_CHAIN_PS, rel=0, abs=1e-12)
    assert sigma_total_ps(10, fit) == pytest.approx(MAO_SSP_10_CHAIN_PS, rel=0, abs=1e-12)


def test_infinite_n_equals_common():
    fit = default_fit()
    assert float(sigma_total_ps(1e12, fit)) == pytest.approx(fit.sigma_common_ps, rel=1e-9)


def test_components_positive():
    fit = default_fit()
    assert fit.sigma_common_ps > 0
    assert fit.sigma_independent_ps > 0
    assert fit.sigma_common_ps < MAO_SSP_10_CHAIN_PS


def test_more_chains_never_increases_sigma():
    fit = default_fit()
    n = np.array([1, 2, 4, 8, 16])
    s = sigma_total_ps(n, fit)
    assert np.all(np.diff(s) < 0)


def test_invalid_anchors_rejected():
    with pytest.raises(ValueError):
        fit_common_independent(4.0, 8.0, 10)
