import pytest

from tidl_poc.vivado.mswu_counts import MSWU_MIN_PREENC_LUT_DELTA, mbd_partition_ranges
from tidl_poc.vivado.mswu_validated import ROUND8_SUPERSEDED, validated_matrix
from tidl_poc.vivado.mswu_validated_evidence import (
    PreencoderOptimizedAwayError,
    ROUND9_SUPERSESSION_NOTE,
    assert_preencoder_not_optimized,
)
from tidl_poc.vivado.reports import parse_carry_locs, placement_scatter_metrics


SAMPLE_MSWU_LOCS = """\
# cell loc bel
mswu_benchmark_wrap/u_top/gen_ch[0]/u_ch/u_tdl/u_chain/gen_carry[0]/gen_head/u_carry/CARRY4 SLICE_X12Y100 CARRY4
mswu_benchmark_wrap/u_top/gen_ch[0]/u_ch/u_tdl/u_chain/gen_carry[1]/gen_body/u_carry/CARRY4 SLICE_X12Y101 CARRY4
mswu_benchmark_wrap/u_top/gen_fe[3]/u_tdl/u_chain/gen_carry[0]/gen_head/u_carry/CARRY4 SLICE_X20Y50 CARRY4
mswu_benchmark_wrap/u_top/gen_fe[3]/u_tdl/u_chain/gen_carry[1]/gen_body/u_carry/CARRY4 SLICE_X20Y51 CARRY4
"""


def test_mbd_all_five_regions_in_partition():
    ranges = mbd_partition_ranges()
    assert len(ranges) == 5
    assert ranges[4][1] == 199


def test_validated_matrix_includes_r9_cases():
    ids = {c.case_id for c in validated_matrix(include_parallel=True)}
    assert "mswu_1ch_core_r9" in ids
    assert "mswu_1ch_preenc_seq_r9" in ids
    assert "mswu_1ch_preenc_parallel_r9" in ids
    assert "mswu_lowrate_16ch_frontends_r9" in ids


def test_parser_recognizes_mswu_hierarchy():
    rows = parse_carry_locs(SAMPLE_MSWU_LOCS)
    assert len(rows) == 4
    ch0 = [r for r in rows if r.get("channel") == 0]
    fe3 = [r for r in rows if r.get("channel") == 3]
    assert len(ch0) == 2
    assert len(fe3) == 2
    assert all(r.get("tdl_path") is not None for r in rows)
    assert all(r.get("carry_index") is not None for r in rows)


def test_mswu_placement_chain_grouping():
    rows = parse_carry_locs(SAMPLE_MSWU_LOCS)
    metrics = placement_scatter_metrics(rows, expected_chains=2)
    assert metrics["n_chains_reported"] == 2
    assert metrics["n_vertical_runs"] == 2
    assert metrics["n_scattered_chains"] == 0
    assert metrics["chain_count_ok"] is True


def test_preencoder_optimized_away_detection_fails_export():
    with pytest.raises(PreencoderOptimizedAwayError):
        assert_preencoder_not_optimized(
            [{"case_id": "bad", "preenc_optimized_away": True, "preenc_mode": 1}]
        )


def test_round9_supersession_metadata():
    assert "Round 8" in ROUND9_SUPERSESSION_NOTE
    assert ROUND8_SUPERSEDED["slice_luts"] == 3
    assert MSWU_MIN_PREENC_LUT_DELTA >= 40
