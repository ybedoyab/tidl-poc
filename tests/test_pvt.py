import numpy as np
import pytest

from tidl_poc.models.pvt import (
    T_MAX_C,
    T_MIN_C,
    T_REF_C,
    modeled_drift_ps,
    profile_ramp,
    profile_static,
    residual_continuous,
    residual_no_cal,
    residual_periodic_series,
)


def test_no_cal_worse_than_lag_limited_continuous_at_band_edge():
    dt = T_MAX_C - T_REF_C
    off, btc = 1.0, 3e-4
    none = abs(residual_no_cal(np.array([dt]), off, btc)[0])
    cont = abs(residual_continuous(np.array([dt]), off, btc, 0.2, 0.05)[0])
    assert none > cont


def test_periodic_zeros_at_calibration_epochs():
    t_s = np.linspace(0.0, 100.0, 101)
    temp = 10.0 + 0.05 * t_s
    residual = residual_periodic_series(t_s, temp, 1.0, 3e-4, interval_s=10.0)
    epochs = np.arange(0, 101, 10)
    assert np.allclose(residual[epochs], 0.0, atol=1e-12)
    assert abs(residual[5]) > 0.0


def test_static_periodic_is_identically_zero_after_first_epoch():
    t_s = np.linspace(0.0, 200.0, 201)
    temp = profile_static(t_s, T_MAX_C)
    residual = residual_periodic_series(t_s, temp, 2.0, 1e-3, interval_s=10.0)
    assert np.max(np.abs(residual)) == pytest.approx(0.0, abs=1e-12)


def test_shorter_interval_reduces_periodic_residual_on_ramp():
    t_s = np.linspace(0.0, 600.0, 1201)
    temp = profile_ramp(t_s, T_MIN_C, 0.05)
    fast = residual_periodic_series(t_s, temp, 1.0, 3e-4, 1.0)
    slow = residual_periodic_series(t_s, temp, 1.0, 3e-4, 60.0)
    assert float(np.max(np.abs(fast))) < float(np.max(np.abs(slow)))


def test_zero_at_reference_temperature():
    assert modeled_drift_ps(T_REF_C, 2.0, 1e-3) == pytest.approx(0.0)


def test_operating_range_constants():
    assert T_MIN_C == 10.0
    assert T_MAX_C == 40.0
