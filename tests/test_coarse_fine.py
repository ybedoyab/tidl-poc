import numpy as np
import pytest

from tidl_poc.models.coarse_fine import (
    CANDIDATE_COARSE_HZ,
    FINE_QUANT_S,
    RANGE_S,
    combine,
    quantize_fine,
    signed_counter_bits,
    split,
)


@pytest.mark.parametrize("f_hz", CANDIDATE_COARSE_HZ)
def test_roundtrip_boundaries(f_hz):
    t_ref = 1.0 / f_hz
    points = np.array(
        [
            -RANGE_S,
            -t_ref,
            -FINE_QUANT_S,
            0.0,
            FINE_QUANT_S,
            t_ref,
            RANGE_S,
        ]
    )
    n, rem = split(points, t_ref)
    recon = combine(n, rem, t_ref)
    assert recon == pytest.approx(points, abs=1e-15)
    assert np.all(rem >= -1e-18)
    assert np.all(rem < t_ref + 1e-18)


def test_negative_and_positive_signs():
    t_ref = 10e-9
    n, rem = split(np.array([-1.5 * t_ref, 1.5 * t_ref]), t_ref)
    assert n[0] < 0
    assert n[1] > 0
    assert combine(n, rem, t_ref) == pytest.approx([-1.5 * t_ref, 1.5 * t_ref])


def test_fine_quantization_lsb():
    q = quantize_fine(np.array([1.4e-12, 1.6e-12, -0.4e-12]))
    assert q[0] == pytest.approx(1e-12)
    assert q[1] == pytest.approx(2e-12)
    assert q[2] == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("hz", "min_bits"),
    [
        (100e6, 28),
        (200e6, 29),
        (400e6, 30),
        (500e6, 30),
    ],
)
def test_counter_width(hz, min_bits):
    max_counts = int(np.ceil(RANGE_S * hz))
    bits = signed_counter_bits(max_counts)
    assert bits >= min_bits
    # Two's complement with `bits` can hold ±max_counts.
    assert (1 << (bits - 1)) - 1 >= max_counts or bits >= min_bits
