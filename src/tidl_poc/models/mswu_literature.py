"""Kwiatkowski 2023 MSWU literature-evidence calculator.

This is not a physics simulation of Wave Union and not a local FPGA result.
Copied numerical values are literature evidence from:

    Kwiatkowski, Sondej, Szplet, Measurement 209 (2023) 112510,
    DOI 10.1016/j.measurement.2023.112510

Naive 16-channel arithmetic and the 1 PPS event-rate comparison are
challenge-specific interpretations, not paper claims.
"""

from __future__ import annotations

import pandas as pd

from tidl_poc import DEFAULT_SEED, MEASUREMENT_DISCLAIMER
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir
from tidl_poc.common.plotting import plt, save_figure

DOI = "10.1016/j.measurement.2023.112510"
SOURCE_LABEL = (
    "literature evidence — Kwiatkowski et al. 2023, "
    "DOI 10.1016/j.measurement.2023.112510"
)

# --- Paper implementation (literature) ---
DEVICE = "XC7K160"
FAMILY = "Kintex-7"
MAIN_CLOCK_MHZ = 710.0
REF_INPUT_MHZ = 10.0
CARRY_MUX_PER_TDL = 200
SAMPLING_REGISTERS = 4
CODE_DENSITY_N = 100_000
PREENCODER_COMPARE_N = 400_000
MBD = 5
SUB_TDL_BITS = 40  # 200 / 5
PREENC_OUT_BITS = 11

# Resolution / precision (literature)
TCL_MEAN_RES_PS = (10.5, 10.51)
WU_ONE_REGISTER_RES_PS = 2.15
MSWU_MEAN_RES_PS = 0.4
CH1_MEAN_LSB_FS = 407.0
CH2_MEAN_LSB_FS = 401.0
CH1_EQ_RES_FS = 546.0
CH2_EQ_RES_FS = 494.0
CH1_MAX_BIN_PS = 2.83
CH2_MAX_BIN_PS = 1.54
INL_BEFORE_CORR_PS = (89.25, 80.76)
INTERVAL_STD_TYP_LT_PS = 4.0
INTERVAL_STD_NEAR_10NS_PS = 5.2
BEST_SPLIT_PRECISION_PS = 2.6
TEMP_RECAL_SPLIT_LT_PS = 3.0
TEMP_RECAL_SSP_LT_PS = 2.1
OFFSET_SPAN_0_TO_40C_PS = 21.0
OFFSET_TC_PS_PER_C = 0.525  # 21 ps / 40 C
PAPER_TEMP_MIN_C = 0.0
PAPER_TEMP_MAX_C = 40.0

# Table 1 pre-encoder for ONE 200-bit register (literature)
TABLE1_RESOURCE_SAVING = {
    "slices": 216,
    "lut": 679,
    "ff": 211,
    "latency": 1,
    "fmax_mhz": 140.0,
}
TABLE1_THROUGHPUT_OPT = {
    "slices": 370,
    "lut": 811,
    "ff": 1462,
    "latency": 10,
    "fmax_mhz": 385.0,
}

# Table 2 XC7K160 (literature)
# Core/pre-encoder BRAM 0.0 means not listed for that Table 2 block.
TABLE2_MSWU_CORE = {"lut": 208, "ff": 800, "slices": 154, "bram": 0.0}
TABLE2_FOUR_SAVING_PREENC = {"lut": 2411, "ff": 0, "slices": 707, "bram": 0.0}
TABLE2_ONE_CHANNEL = {"lut": 2840, "ff": 1165, "slices": 953, "bram": 21.5}
TABLE2_TWO_CHANNEL = {
    "lut": 6304,
    "lut_pct": 6.22,
    "ff": 2998,
    "ff_pct": 1.48,
    "slices": 2184,
    "slices_pct": 8.62,
    "bram": 43.0,
    "bram_pct": 13.23,
}

N_CHALLENGE_CHANNELS = 16
CHALLENGE_PPS_HZ = 1.0


def events_per_second(n_channels: int = N_CHALLENGE_CHANNELS, pps_hz: float = CHALLENGE_PPS_HZ) -> float:
    """S5/S7 challenge event rate. Units: events/s."""
    return float(n_channels) * float(pps_hz)


def naive_replicate_channel(n_channels: int = N_CHALLENGE_CHANNELS) -> dict[str, float]:
    """16 × paper's complete measurement channel. Not a fit claim."""
    return {
        "n_channels": n_channels,
        "lut": n_channels * TABLE2_ONE_CHANNEL["lut"],
        "ff": n_channels * TABLE2_ONE_CHANNEL["ff"],
        "slices": n_channels * TABLE2_ONE_CHANNEL["slices"],
        "bram": n_channels * TABLE2_ONE_CHANNEL["bram"],
    }


def device_capacity_from_table2_pct() -> dict[str, float]:
    """Infer XC7K160 totals from Table 2 percentages. Rounding is the paper's."""
    t = TABLE2_TWO_CHANNEL
    return {
        "lut": t["lut"] / (t["lut_pct"] / 100.0),
        "ff": t["ff"] / (t["ff_pct"] / 100.0),
        "slices": t["slices"] / (t["slices_pct"] / 100.0),
        "bram": t["bram"] / (t["bram_pct"] / 100.0),
        "derivation": "derived from paper percentage rounding",
    }


def naive_utilization(n_channels: int = N_CHALLENGE_CHANNELS) -> dict[str, float]:
    naive = naive_replicate_channel(n_channels)
    cap = device_capacity_from_table2_pct()
    return {
        "lut_pct": 100.0 * naive["lut"] / cap["lut"],
        "ff_pct": 100.0 * naive["ff"] / cap["ff"],
        "slices_pct": 100.0 * naive["slices"] / cap["slices"],
        "bram_pct": 100.0 * naive["bram"] / cap["bram"],
        "bram_naive_exceeds_inferred_device": naive["bram"] > cap["bram"],
        "capacity_note": cap["derivation"],
    }


def uncompensated_offset_ps(
    temp_c: float,
    t_ref_c: float,
    tc_ps_per_c: float = OFFSET_TC_PS_PER_C,
) -> float:
    """Linear offset vs reference using the paper coefficient. Not our board."""
    return float(tc_ps_per_c) * (float(temp_c) - float(t_ref_c))


def run(seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    del seed, fast
    out = outputs_dir("mswu_literature")
    cap = device_capacity_from_table2_pct()
    naive = naive_replicate_channel()
    util = naive_utilization()
    rate = events_per_second()
    saving_fmax_hz = TABLE1_RESOURCE_SAVING["fmax_mhz"] * 1e6

    source_rows = [
        {"quantity": "device", "value": DEVICE, "unit": "", "source": SOURCE_LABEL},
        {"quantity": "main_clock", "value": MAIN_CLOCK_MHZ, "unit": "MHz", "source": SOURCE_LABEL},
        {"quantity": "tcl_mean_resolution_ch_a", "value": TCL_MEAN_RES_PS[0], "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "tcl_mean_resolution_ch_b", "value": TCL_MEAN_RES_PS[1], "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "wu_one_register_resolution", "value": WU_ONE_REGISTER_RES_PS, "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "mswu_mean_resolution", "value": MSWU_MEAN_RES_PS, "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "ch1_mean_lsb", "value": CH1_MEAN_LSB_FS, "unit": "fs", "source": SOURCE_LABEL},
        {"quantity": "ch2_mean_lsb", "value": CH2_MEAN_LSB_FS, "unit": "fs", "source": SOURCE_LABEL},
        {"quantity": "ch1_equivalent_resolution", "value": CH1_EQ_RES_FS, "unit": "fs", "source": SOURCE_LABEL},
        {"quantity": "ch2_equivalent_resolution", "value": CH2_EQ_RES_FS, "unit": "fs", "source": SOURCE_LABEL},
        {"quantity": "ch1_max_physical_bin", "value": CH1_MAX_BIN_PS, "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "ch2_max_physical_bin", "value": CH2_MAX_BIN_PS, "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "interval_std_typical_lt", "value": INTERVAL_STD_TYP_LT_PS, "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "interval_std_near_10ns", "value": INTERVAL_STD_NEAR_10NS_PS, "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "best_split_precision", "value": BEST_SPLIT_PRECISION_PS, "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "temp_recal_split_precision_lt", "value": TEMP_RECAL_SPLIT_LT_PS, "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "temp_recal_ssp_lt", "value": TEMP_RECAL_SSP_LT_PS, "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "offset_tc", "value": OFFSET_TC_PS_PER_C, "unit": "ps/C", "source": SOURCE_LABEL},
        {"quantity": "offset_span_0_to_40C", "value": OFFSET_SPAN_0_TO_40C_PS, "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "code_density_n", "value": CODE_DENSITY_N, "unit": "measurements", "source": SOURCE_LABEL},
        {"quantity": "inl_before_correction_ch1", "value": INL_BEFORE_CORR_PS[0], "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "inl_before_correction_ch2", "value": INL_BEFORE_CORR_PS[1], "unit": "ps", "source": SOURCE_LABEL},
        {"quantity": "table1_saving_slices", "value": TABLE1_RESOURCE_SAVING["slices"], "unit": "slices", "source": SOURCE_LABEL},
        {"quantity": "table1_saving_lut", "value": TABLE1_RESOURCE_SAVING["lut"], "unit": "LUT", "source": SOURCE_LABEL},
        {"quantity": "table1_saving_ff", "value": TABLE1_RESOURCE_SAVING["ff"], "unit": "FF", "source": SOURCE_LABEL},
        {"quantity": "table1_saving_latency", "value": TABLE1_RESOURCE_SAVING["latency"], "unit": "cycles", "source": SOURCE_LABEL},
        {"quantity": "table1_saving_fmax", "value": TABLE1_RESOURCE_SAVING["fmax_mhz"], "unit": "MHz", "source": SOURCE_LABEL},
        {"quantity": "table1_throughput_slices", "value": TABLE1_THROUGHPUT_OPT["slices"], "unit": "slices", "source": SOURCE_LABEL},
        {"quantity": "table1_throughput_lut", "value": TABLE1_THROUGHPUT_OPT["lut"], "unit": "LUT", "source": SOURCE_LABEL},
        {"quantity": "table1_throughput_ff", "value": TABLE1_THROUGHPUT_OPT["ff"], "unit": "FF", "source": SOURCE_LABEL},
        {"quantity": "table1_throughput_latency", "value": TABLE1_THROUGHPUT_OPT["latency"], "unit": "cycles", "source": SOURCE_LABEL},
        {"quantity": "table1_throughput_fmax", "value": TABLE1_THROUGHPUT_OPT["fmax_mhz"], "unit": "MHz", "source": SOURCE_LABEL},
        {"quantity": "table2_core_lut", "value": TABLE2_MSWU_CORE["lut"], "unit": "LUT", "source": SOURCE_LABEL},
        {"quantity": "table2_core_ff", "value": TABLE2_MSWU_CORE["ff"], "unit": "FF", "source": SOURCE_LABEL},
        {"quantity": "table2_core_slices", "value": TABLE2_MSWU_CORE["slices"], "unit": "slices", "source": SOURCE_LABEL},
        {"quantity": "table2_four_preenc_lut", "value": TABLE2_FOUR_SAVING_PREENC["lut"], "unit": "LUT", "source": SOURCE_LABEL},
        {"quantity": "table2_four_preenc_ff", "value": TABLE2_FOUR_SAVING_PREENC["ff"], "unit": "FF", "source": SOURCE_LABEL},
        {"quantity": "table2_four_preenc_slices", "value": TABLE2_FOUR_SAVING_PREENC["slices"], "unit": "slices", "source": SOURCE_LABEL},
        {"quantity": "table2_one_channel_lut", "value": TABLE2_ONE_CHANNEL["lut"], "unit": "LUT", "source": SOURCE_LABEL},
        {"quantity": "table2_one_channel_ff", "value": TABLE2_ONE_CHANNEL["ff"], "unit": "FF", "source": SOURCE_LABEL},
        {"quantity": "table2_one_channel_slices", "value": TABLE2_ONE_CHANNEL["slices"], "unit": "slices", "source": SOURCE_LABEL},
        {"quantity": "table2_one_channel_bram", "value": TABLE2_ONE_CHANNEL["bram"], "unit": "BRAM", "source": SOURCE_LABEL},
        {"quantity": "table2_two_channel_lut", "value": TABLE2_TWO_CHANNEL["lut"], "unit": "LUT", "source": SOURCE_LABEL},
        {"quantity": "table2_two_channel_lut_pct", "value": TABLE2_TWO_CHANNEL["lut_pct"], "unit": "%", "source": SOURCE_LABEL},
        {"quantity": "table2_two_channel_ff", "value": TABLE2_TWO_CHANNEL["ff"], "unit": "FF", "source": SOURCE_LABEL},
        {"quantity": "table2_two_channel_ff_pct", "value": TABLE2_TWO_CHANNEL["ff_pct"], "unit": "%", "source": SOURCE_LABEL},
        {"quantity": "table2_two_channel_slices", "value": TABLE2_TWO_CHANNEL["slices"], "unit": "slices", "source": SOURCE_LABEL},
        {"quantity": "table2_two_channel_slices_pct", "value": TABLE2_TWO_CHANNEL["slices_pct"], "unit": "%", "source": SOURCE_LABEL},
        {"quantity": "table2_two_channel_bram", "value": TABLE2_TWO_CHANNEL["bram"], "unit": "BRAM", "source": SOURCE_LABEL},
        {"quantity": "table2_two_channel_bram_pct", "value": TABLE2_TWO_CHANNEL["bram_pct"], "unit": "%", "source": SOURCE_LABEL},
    ]
    pd.DataFrame(source_rows).to_csv(out / "literature_source_table.csv", index=False)

    table1 = pd.DataFrame(
        [
            {"variant": "resource_saving", "scope": "one_200bit_register", **TABLE1_RESOURCE_SAVING, "source": SOURCE_LABEL},
            {"variant": "throughput_optimized", "scope": "one_200bit_register", **TABLE1_THROUGHPUT_OPT, "source": SOURCE_LABEL},
        ]
    )
    table1.to_csv(out / "table1_preencoder.csv", index=False)

    table2 = pd.DataFrame(
        [
            {"block": "mswu_tdc_core", **TABLE2_MSWU_CORE, "source": SOURCE_LABEL},
            {"block": "four_resource_saving_preencoders", **TABLE2_FOUR_SAVING_PREENC, "source": SOURCE_LABEL},
            {"block": "one_complete_measurement_channel", **TABLE2_ONE_CHANNEL, "source": SOURCE_LABEL},
            {
                "block": "full_two_channel_design",
                "lut": TABLE2_TWO_CHANNEL["lut"],
                "ff": TABLE2_TWO_CHANNEL["ff"],
                "slices": TABLE2_TWO_CHANNEL["slices"],
                "bram": TABLE2_TWO_CHANNEL["bram"],
                "source": SOURCE_LABEL,
            },
        ]
    )
    table2.to_csv(out / "table2_xc7k160.csv", index=False)

    naive_row = {
        **naive,
        "lut_pct_of_inferred_xc7k160": util["lut_pct"],
        "ff_pct_of_inferred_xc7k160": util["ff_pct"],
        "slices_pct_of_inferred_xc7k160": util["slices_pct"],
        "bram_pct_of_inferred_xc7k160": util["bram_pct"],
        "bram_naive_exceeds_inferred_device": util["bram_naive_exceeds_inferred_device"],
        "does_not_prove_16ch_unfittable": True,
        "interpretation": "naive replicate-entire-paper-channel; not our architecture",
        "result_classification": "model-based simulation",
        "capacity_derivation": cap["derivation"],
    }
    pd.DataFrame([naive_row]).to_csv(out / "naive_16ch_scaling.csv", index=False)

    rate_row = {
        "n_channels": N_CHALLENGE_CHANNELS,
        "pps_hz": CHALLENGE_PPS_HZ,
        "events_per_s": rate,
        "resource_saving_preencoder_fmax_sa_s": saving_fmax_hz,
        "throughput_headroom_ratio": saving_fmax_hz / rate,
        "paper_fifos_required_by_event_rate": False,
        "fake_final_bram_usage_calculated": False,
        "bram_reduction_is_design_hypothesis": True,
        "result_classification": "model-based simulation",
        "literature_fmax_source": SOURCE_LABEL,
    }
    pd.DataFrame([rate_row]).to_csv(out / "challenge_event_rate.csv", index=False)

    temps = [10.0, 21.5, 40.0]
    therm_rows = []
    for t in temps:
        therm_rows.append(
            {
                "temp_c": t,
                "t_ref_c": 21.5,
                "uncompensated_offset_ps": uncompensated_offset_ps(t, 21.5),
                "after_temperature_specific_recalibration_ps": 0.0,
                "coefficient_ps_per_c": OFFSET_TC_PS_PER_C,
                "source": SOURCE_LABEL,
                "note": "linear use of paper 0.525 ps/C; not our board",
            }
        )
    therm_rows.append(
        {
            "temp_c": "span_10_to_40",
            "t_ref_c": 10.0,
            "uncompensated_offset_ps": OFFSET_TC_PS_PER_C * (40.0 - 10.0),
            "after_temperature_specific_recalibration_ps": 0.0,
            "coefficient_ps_per_c": OFFSET_TC_PS_PER_C,
            "source": SOURCE_LABEL,
            "note": "30 C span; paper quoted 21 ps over 0-40 C",
        }
    )
    pd.DataFrame(therm_rows).to_csv(out / "literature_thermal_offset.csv", index=False)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    labels = ["LUT", "FF", "slices", "BRAM"]
    pcts = [util["lut_pct"], util["ff_pct"], util["slices_pct"], util["bram_pct"]]
    ax.bar(labels, pcts, color="0.5")
    ax.axhline(100.0, color="0.1", linestyle="--")
    ax.set_ylabel("% of XC7K160 capacity inferred from Table 2 percentages")
    ax.set_title("Naive 16 x paper-channel (not a fit claim; not our architecture)")
    save_figure(fig, out / "naive_16ch_utilization")

    extra = {
        "naive_16ch_lut": naive["lut"],
        "naive_16ch_ff": naive["ff"],
        "naive_16ch_slices": naive["slices"],
        "naive_16ch_bram": naive["bram"],
        "inferred_xc7k160_lut": cap["lut"],
        "inferred_xc7k160_ff": cap["ff"],
        "inferred_xc7k160_slices": cap["slices"],
        "inferred_xc7k160_bram": cap["bram"],
        "naive_lut_pct": util["lut_pct"],
        "naive_ff_pct": util["ff_pct"],
        "naive_slices_pct": util["slices_pct"],
        "naive_bram_pct": util["bram_pct"],
        "bram_naive_exceeds_inferred_device": util["bram_naive_exceeds_inferred_device"],
        "challenge_events_per_s": rate,
        "resource_saving_fmax_hz": saving_fmax_hz,
        "uncompensated_offset_10_to_40C_ps": OFFSET_TC_PS_PER_C * 30.0,
        "uncompensated_offset_at_40C_vs_21p5_ps": uncompensated_offset_ps(40.0, 21.5),
        "does_not_prove_16ch_unfittable": True,
    }
    params = {
        "doi": DOI,
        "source_label": SOURCE_LABEL,
        "this_is_not_mswu_physics": True,
        "this_is_not_our_fpga_result": True,
        "parameter_provenance": "literature table transcription plus challenge arithmetic",
    }
    write_metadata(
        out / "metadata.json",
        script_name="tidl_poc.models.mswu_literature",
        random_seed=DEFAULT_SEED,
        input_parameters=params,
        extra=extra,
    )
    write_json(out / "summary.json", extra)
    (out / "interpretation.md").write_text(
        f"""# Kwiatkowski 2023 MSWU literature calculator

All paper numbers: {SOURCE_LABEL}
Naive 16-channel products and the 16 events/s comparison are challenge-specific
interpretations, not claims in the paper and not this project's FPGA result.

Naive 16 x one paper channel: LUT={naive["lut"]}, FF={naive["ff"]},
slices={naive["slices"]}, BRAM={naive["bram"]}.
Inferred XC7K160 (from Table 2 % rounding): LUT={cap["lut"]:.1f},
FF={cap["ff"]:.1f}, slices={cap["slices"]:.1f}, BRAM={cap["bram"]:.2f}.
Naive BRAM exceeds inferred device ({util["bram_pct"]:.1f}%). That does **not**
prove 16 channels cannot fit; the paper FIFOs target a much higher sample rate.

Challenge event rate: {rate:.0f} events/s vs resource-saving pre-encoder
{saving_fmax_hz:.0f} Sa/s. Per-channel deep FIFOs are not required by S5/S7
rate. BRAM reduction is a design hypothesis needing Vivado evidence.

Uncompensated 0.525 ps/C over 10-40 C: {OFFSET_TC_PS_PER_C * 30.0:.3f} ps.
Temperature-specific recalibration in the paper kept split-signal interval
precision <3 ps over 0-40 C; this calculator does not interpolate between
temperatures.

{MEASUREMENT_DISCLAIMER}
""",
        encoding="utf-8",
    )
    return {"output_dir": str(out), "extra": extra}
