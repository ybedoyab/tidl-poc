"""Software twin of rtl/timestamp/timestamp_combiner.sv arithmetic."""

import pytest

from tidl_poc.models.coarse_fine import combine


def test_combiner_matches_sv_examples():
    t_ref_ps = 100e-12
    assert float(combine(0, 0, t_ref_ps)) == pytest.approx(0.0, abs=1e-18)
    assert float(combine(1, 7e-12, t_ref_ps)) == pytest.approx(107e-12, abs=1e-18)
    assert float(combine(-1, 0.0, t_ref_ps)) == pytest.approx(-100e-12, abs=1e-18)
    assert float(combine(-1, 1e-12, t_ref_ps)) == pytest.approx(-99e-12, abs=1e-18)
