import numpy as np
import pytest

from tidl_poc.models.frontend_jitter import combined_jitter_ps, threshold_crossing_jitter_s


def test_threshold_crossing_units():
    # 1 mV RMS / 1 V/ns = 1 ps
    assert threshold_crossing_jitter_s(1e-3, 1e9) == pytest.approx(1e-12)


def test_zero_slew_rejected():
    with pytest.raises(ValueError):
        threshold_crossing_jitter_s(1e-3, 0.0)


def test_rss_combines_additive_terms():
    j = float(combined_jitter_ps(0.0, 1e9, 0.0, 3.0, 4.0))
    assert j == pytest.approx(5.0)
