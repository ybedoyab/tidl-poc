import pytest

from tidl_poc import RTL_RESULT_CLASSIFICATION
from tidl_poc.vivado.mswu_counts import (
    MSWU_CARRY4_PER_TDL,
    MSWU_LOGICAL_TAPS,
    MSWU_MBD_PARTITIONS,
    MSWU_MBD_SUB_BITS,
    expected_mswu_counts,
    mbd_partition_ranges,
)
from tidl_poc.vivado.mswu_evidence import (
    CaptureFfMismatchError,
    Carry4MismatchError,
    assert_mswu_capture_ff,
    assert_mswu_carry4,
)
from tidl_poc.vivado.mswu import default_matrix, mswu_matrix


def test_mswu_carry4_formula():
    one = expected_mswu_counts(1)
    assert one.carry4 == 50
    assert one.capture_ff_min == 800
    assert MSWU_CARRY4_PER_TDL * 4 == MSWU_LOGICAL_TAPS
    sixteen = expected_mswu_counts(16)
    assert sixteen.carry4 == 800
    assert sixteen.capture_ff_min == 12800


def test_mbd_partition_covers_200_taps_without_gap():
    ranges = mbd_partition_ranges()
    assert len(ranges) == MSWU_MBD_PARTITIONS
    assert ranges[0][0] == 0
    assert ranges[-1][1] == MSWU_LOGICAL_TAPS - 1
    for i in range(len(ranges) - 1):
        assert ranges[i][1] + 1 == ranges[i + 1][0]
        width = ranges[i][1] - ranges[i][0] + 1
        assert width == MSWU_MBD_SUB_BITS


def test_mswu_default_matrix_cases():
    cases = default_matrix()
    ids = {c.case_id for c in cases}
    assert "mswu_structural_1ch_core" in ids
    assert "mswu_structural_1ch_preencoder" in ids
    assert "mswu_lowrate_16ch_frontends" in ids
    assert len(cases) == 3


def test_mswu_full_matrix_includes_scaling_fallbacks():
    assert len(mswu_matrix()) == 5


def test_assert_mswu_carry4_and_capture_ff():
    assert_mswu_carry4([{"case_id": "x", "expected_carry4": 50, "mapped_carry4": 50}])
    with pytest.raises(Carry4MismatchError):
        assert_mswu_carry4([{"case_id": "x", "expected_carry4": 50, "mapped_carry4": 49}])
    assert_mswu_capture_ff(
        [{"case_id": "x", "expected_capture_ff_min": 800, "mapped_fdre": 805}]
    )
    with pytest.raises(CaptureFfMismatchError):
        assert_mswu_capture_ff(
            [{"case_id": "x", "expected_capture_ff_min": 800, "mapped_fdre": 700}]
        )


def test_mswu_evidence_classification_constant():
    assert RTL_RESULT_CLASSIFICATION == "RTL/synthesis/implementation evidence"
