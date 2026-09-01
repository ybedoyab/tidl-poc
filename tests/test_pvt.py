import numpy as np
import pytest

from tidl_poc.models.pvt import (
    T_MAX_C,
    T_MIN_C,
    T_REF_C,
    residual_continuous,
    residual_no_cal,
    residual_periodic,
)


def test_no_cal_worse_than_continuous_at_band_edge():
    dt = T_MAX_C - T_REF_C
    off, btc = 1.0, 3e-4
    none = abs(residual_no_cal(np.array([dt]), off, btc)[0])
    cont = abs(residual_continuous(np.array([dt]), off, btc, 0.2, 0.05)[0])
    assert none > cont


def test_shorter_interval_reduces_periodic_residual():
    dt = np.array([T_MAX_C - T_REF_C])
    fast = abs(residual_periodic(dt, 1.0, 3e-4, 1.0, 0.05)[0])
    slow = abs(residual_periodic(dt, 1.0, 3e-4, 600.0, 0.05)[0])
    assert fast < slow


def test_zero_at_reference_temperature():
    assert residual_no_cal(np.array([0.0]), 2.0, 1e-3)[0] == pytest.approx(0.0)


def test_operating_range_constants():
    assert T_MIN_C == 10.0
    assert T_MAX_C == 40.0
