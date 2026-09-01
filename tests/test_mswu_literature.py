import json

import pandas as pd

from tidl_poc import RESULT_CLASSIFICATION
from tidl_poc.common.metadata import validate_metadata_schema
from tidl_poc.common.paths import outputs_dir
from tidl_poc.models.error_budget import literature_tdc_ssp_ps, scenarios
from tidl_poc.models.mswu_literature import (
    OFFSET_TC_PS_PER_C,
    SOURCE_LABEL,
    TABLE1_RESOURCE_SAVING,
    TABLE1_THROUGHPUT_OPT,
    TABLE2_FOUR_SAVING_PREENC,
    TABLE2_MSWU_CORE,
    TABLE2_ONE_CHANNEL,
    TABLE2_TWO_CHANNEL,
    device_capacity_from_table2_pct,
    events_per_second,
    naive_replicate_channel,
    naive_utilization,
    run,
    uncompensated_offset_ps,
)


def test_naive_sixteen_channel_arithmetic():
    n = naive_replicate_channel(16)
    assert n["lut"] == 16 * 2840
    assert n["ff"] == 16 * 1165
    assert n["slices"] == 16 * 953
    assert n["bram"] == 16 * 21.5
    assert n["lut"] == 16 * TABLE2_ONE_CHANNEL["lut"]


def test_sixteen_events_per_second():
    assert events_per_second(16, 1.0) == 16.0


def test_thermal_offset_coefficient():
    assert OFFSET_TC_PS_PER_C == 0.525
    assert OFFSET_TC_PS_PER_C * 40.0 == 21.0
    assert uncompensated_offset_ps(40.0, 10.0) == 15.75
    assert uncompensated_offset_ps(21.5, 21.5) == 0.0


def test_inferred_capacity_from_table2_percentages():
    cap = device_capacity_from_table2_pct()
    assert cap["lut"] == TABLE2_TWO_CHANNEL["lut"] / (TABLE2_TWO_CHANNEL["lut_pct"] / 100.0)
    assert cap["bram"] == TABLE2_TWO_CHANNEL["bram"] / (TABLE2_TWO_CHANNEL["bram_pct"] / 100.0)
    util = naive_utilization(16)
    assert util["bram_naive_exceeds_inferred_device"] is True
    assert util["lut_pct"] < 100.0
    assert util["slices_pct"] < 100.0
    assert cap["derivation"] == "derived from paper percentage rounding"


def test_table1_and_table2_constants():
    assert TABLE1_RESOURCE_SAVING == {
        "slices": 216,
        "lut": 679,
        "ff": 211,
        "latency": 1,
        "fmax_mhz": 140.0,
    }
    assert TABLE1_THROUGHPUT_OPT == {
        "slices": 370,
        "lut": 811,
        "ff": 1462,
        "latency": 10,
        "fmax_mhz": 385.0,
    }
    assert TABLE2_MSWU_CORE == {"lut": 208, "ff": 800, "slices": 154, "bram": 0.0}
    assert TABLE2_FOUR_SAVING_PREENC == {"lut": 2411, "ff": 0, "slices": 707, "bram": 0.0}
    assert TABLE2_ONE_CHANNEL == {"lut": 2840, "ff": 1165, "slices": 953, "bram": 21.5}
    assert TABLE2_TWO_CHANNEL["lut"] == 6304
    assert TABLE2_TWO_CHANNEL["lut_pct"] == 6.22
    assert TABLE2_TWO_CHANNEL["ff"] == 2998
    assert TABLE2_TWO_CHANNEL["ff_pct"] == 1.48
    assert TABLE2_TWO_CHANNEL["slices"] == 2184
    assert TABLE2_TWO_CHANNEL["slices_pct"] == 8.62
    assert TABLE2_TWO_CHANNEL["bram"] == 43.0
    assert TABLE2_TWO_CHANNEL["bram_pct"] == 13.23


def test_mswu_literature_cli_metadata_schema():
    result = run()
    payload = json.loads((outputs_dir("mswu_literature") / "metadata.json").read_text(encoding="utf-8"))
    assert validate_metadata_schema(payload) == []
    assert payload["result_classification"] == RESULT_CLASSIFICATION
    assert payload["input_parameters"]["this_is_not_mswu_physics"] is True
    assert payload["input_parameters"]["source_label"] == SOURCE_LABEL
    assert result["extra"]["challenge_events_per_s"] == 16.0
    assert result["extra"]["does_not_prove_16ch_unfittable"] is True
    src = pd.read_csv(outputs_dir("mswu_literature") / "literature_source_table.csv")
    assert set(src["source"].unique()) == {SOURCE_LABEL}


def test_target_allocation_numbers_unchanged():
    terms = {t.name: t.sigma_ps for t in scenarios()["target_allocation"]}
    assert terms["frontend_threshold_jitter_ps"] == 5.0
    assert terms["time_walk_residual_ps"] == 3.0
    assert terms["fpga_fine_tdc_ssp_ps"] == literature_tdc_ssp_ps(8)
    assert terms["coarse_reference_jitter_ps"] == 4.0
    assert terms["channel_random_residual_ps"] == 4.0
    assert terms["calibration_random_residual_ps"] == 3.0
    assert terms["pvt_random_residual_ps"] == 4.0
    assert terms["supply_noise_ps"] == 2.0
    assert terms["clock_distribution_ps"] == 3.0
    assert terms["common_correlated_ps"] == 2.0
