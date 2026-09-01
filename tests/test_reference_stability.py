import pytest

from tidl_poc.models.reference_stability import (
    fractional_frequency_from_interval_error,
    interval_error_from_y,
)


def test_delta_t_equals_y_times_tau():
    tau = 1.0
    y = 2e-11
    assert interval_error_from_y(y, tau) == pytest.approx(20e-12)


def test_one_second_allocations():
    assert fractional_frequency_from_interval_error(5e-12, 1.0) == pytest.approx(5e-12)
    assert fractional_frequency_from_interval_error(10e-12, 1.0) == pytest.approx(1e-11)
    assert fractional_frequency_from_interval_error(20e-12, 1.0) == pytest.approx(2e-11)


def test_rejects_nonpositive_tau():
    with pytest.raises(ValueError):
        fractional_frequency_from_interval_error(20e-12, 0.0)
