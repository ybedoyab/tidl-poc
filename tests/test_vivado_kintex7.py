from pathlib import Path

import pytest

from tidl_poc import RTL_DISCLAIMER, RTL_RESULT_CLASSIFICATION
from tidl_poc.common.metadata import build_metadata, validate_metadata_schema
from tidl_poc.vivado.counts import expected_counts
from tidl_poc.vivado.discover import choose_kintex7_part, parse_get_parts_output, parse_vivado_version
from tidl_poc.vivado.reports import (
    parse_carry_locs,
    parse_impl_failure,
    parse_route_status,
    parse_timing_summary,
    parse_utilization,
    placement_scatter_metrics,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "vivado"


def test_primary_matrix_impl_subset():
    from tidl_poc.vivado.baseline import primary_matrix, staging_root
    from tidl_poc.vivado.tcl import generate_case_tcl

    cases = primary_matrix()
    assert len(cases) == 12
    impl = {c.case_id for c in cases if c.do_impl}
    assert impl == {
        "ch01_nch08_c4_32",
        "ch01_nch08_c4_48",
        "ch01_nch08_c4_64",
        "ch04_nch08_c4_64",
        "ch08_nch08_c4_64",
        "ch16_nch08_c4_64",
    }
    assert "," not in str(staging_root())
    dummy = Path("dummy")
    guided = generate_case_tcl(
        part="xc7k160tffg676-2",
        rtl_dir=dummy,
        xdc_path=dummy / "x.xdc",
        wrap_path=dummy / "w.sv",
        out_dir=dummy / "out",
        do_impl=True,
        n_carry4=32,
        expected_capture_ff=1024,
        place_guide=True,
    )
    assert "set do_place_guide 1" in guided
    skipped = generate_case_tcl(
        part="xc7k160tffg676-2",
        rtl_dir=dummy,
        xdc_path=dummy / "x.xdc",
        wrap_path=dummy / "w.sv",
        out_dir=dummy / "out",
        do_impl=True,
        n_carry4=64,
        expected_capture_ff=2048,
        place_guide=False,
        fast_impl=True,
    )
    assert "set do_place_guide 0" in skipped
    assert "place_design -no_timing_driven" in skipped
    assert "route_design -no_timing_driven" in skipped
    assert "TIDL_PLACE=skipped_large_case" in skipped


def test_expected_carry4_and_tap_formula():
    counts = expected_counts(16, 8, 64)
    assert counts.carry4 == 16 * 8 * 64
    assert counts.taps == counts.carry4 * 4
    assert counts.capture_ff_min == counts.taps
    assert counts.carry4 == 8192
    assert counts.taps == 32768


def test_expected_counts_small_case():
    counts = expected_counts(1, 8, 32)
    assert counts.carry4 == 256
    assert counts.taps == 1024
    assert not counts.optimized_away(256)
    assert counts.optimized_away(10)


def test_parse_utilization_fixture():
    text = (FIXTURES / "utilization_ok.rpt").read_text(encoding="utf-8")
    util = parse_utilization(text)
    assert util["carry4"] == 512
    assert util["fdre"] == 2048
    assert util["slice_luts"] == 1028
    assert util["slice_registers"] == 2056
    assert util["slices"] == 520
    assert util["slices_pct"] == 2.05


def test_parse_utilization_vivado2026_columns():
    text = (
        "| Slice LUTs*             |  218 |     0 |          0 |    101400 |  0.21 |\n"
        "| Slice Registers         | 1027 |  1024 |          0 |    202800 |  0.51 |\n"
        "| Slice                    |  416 |     0 |          0 |     25350 |  1.64 |\n"
        "| CARRY4   |  256 |          CarryLogic |\n"
        "| FDRE     | 1027 |        Flop & Latch |\n"
    )
    util = parse_utilization(text)
    assert util["slice_luts"] == 218
    assert util["slice_luts_pct"] == 0.21
    assert util["slices_pct"] == 1.64
    assert util["carry4"] == 256
    assert util["fdre"] == 1027


def test_parse_timing_met_and_failed():
    ok = parse_timing_summary((FIXTURES / "timing_ok.rpt").read_text(encoding="utf-8"))
    assert ok["timing_closed"] is True
    assert ok["wns_ns"] == 0.412
    assert ok["tns_ns"] == 0.0
    bad = parse_timing_summary((FIXTURES / "timing_fail.rpt").read_text(encoding="utf-8"))
    assert bad["timing_closed"] is False
    assert bad["wns_ns"] == -1.250


def test_parse_failed_implementation():
    text = (FIXTURES / "impl_fail.log").read_text(encoding="utf-8")
    fail = parse_impl_failure(text)
    assert fail["failed"] is True
    assert fail["stage"] == "place_design"
    assert any("ERROR:" in e for e in fail["errors"])
    route = parse_route_status((FIXTURES / "route_ok.rpt").read_text(encoding="utf-8"))
    assert route["fully_routed"] is True
    routed = parse_route_status(
        "# of fully routed nets............. :        1492 :\n"
        "# of routable nets..................... :        1492 :\n"
        "# of nets with routing errors.......... :           0 :\n"
    )
    assert routed["fully_routed"] is True
    assert routed["route_status"] == "fully_routed"


def test_rtl_metadata_classification():
    payload = build_metadata(
        script_name="run_kintex7_baseline.py",
        random_seed=42,
        input_parameters={"channels": [1, 4, 8, 16]},
        result_classification=RTL_RESULT_CLASSIFICATION,
        disclaimer=RTL_DISCLAIMER,
    )
    assert validate_metadata_schema(payload) == []
    assert payload["result_classification"] == "RTL/synthesis/implementation evidence"
    assert "not a physical measurement" in payload["disclaimer"].lower()


def test_choose_part_prefers_xc7k160_speed_minus_2():
    parts = [
        "xc7k70tfbg484-2",
        "xc7k160tfbg484-1",
        "xc7k160tffg676-2L",
        "xc7k160tffg676-2",
        "xc7k160tfbg484-2",
        "xc7k325tffg900-2",
        "xc7k160tffv676-2",
    ]
    assert choose_kintex7_part(parts) == "xc7k160tffg676-2"


def test_choose_part_falls_back_to_xc7k325_when_no_k160():
    parts = [
        "xc7k70tfbg484-2",
        "xc7k325tfbg676-2",
        "xc7k325tffg900-2",
        "xc7k410tffg900-2",
    ]
    assert choose_kintex7_part(parts) == "xc7k325tffg900-2"


def test_parse_get_parts_and_version():
    blob = "vivado v2026.1 (64-bit)\nK7_PART=xc7k160tffg676-2\nK7_PART=xc7k325tffg900-2\n"
    assert parse_vivado_version(blob) == "2026.1"
    assert parse_get_parts_output(blob) == ["xc7k160tffg676-2", "xc7k325tffg900-2"]


def test_placement_scatter_from_fixture():
    rows = parse_carry_locs((FIXTURES / "carry_locs.txt").read_text(encoding="utf-8"))
    metrics = placement_scatter_metrics(rows)
    assert metrics["n_chains_reported"] == 2
    assert metrics["n_scattered_chains"] == 1
    assert metrics["scattered"] is True


def test_timing_clean_matrix_is_four_impl_cases_at_64():
    from tidl_poc.vivado.timing_clean import timing_clean_matrix

    cases = timing_clean_matrix()
    assert len(cases) == 4
    assert {c.channels for c in cases} == {1, 4, 8, 16}
    assert all(c.carry4_per_chain == 64 for c in cases)
    assert all(c.do_impl for c in cases)


def test_assert_capture_ff_matches():
    from tidl_poc.vivado.evidence import CaptureFfMismatchError, assert_capture_ff_matches

    assert_capture_ff_matches(
        [
            {
                "case_id": "ch01_nch08_c4_64",
                "channels": 1,
                "chains_per_channel": 8,
                "carry4_per_chain": 64,
                "expected_capture_ff_min": 2048,
                "mapped_fdre": 2051,
            }
        ]
    )
    with pytest.raises(CaptureFfMismatchError):
        assert_capture_ff_matches(
            [
                {
                    "case_id": "ch16_nch08_c4_64",
                    "channels": 16,
                    "chains_per_channel": 8,
                    "carry4_per_chain": 64,
                    "expected_capture_ff_min": 32768,
                    "mapped_fdre": 32000,
                }
            ]
        )


def test_no_machine_paths_in_tracked_sources():
    root = Path(__file__).resolve().parents[1]
    skip_dirs = {".git", ".venv", "venv", "__pycache__", "outputs", ".pytest_cache", ".Xil"}
    forbidden = (
        r":\AMD\20",
        r":/AMD/20",
        r":\Xilinx\Vivado\20",
        r":/Xilinx/Vivado/20",
        r"C:\Users\\",
    )
    hits: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.name == "test_vivado_kintex7.py":
            continue
        if path.suffix.lower() not in {".py", ".md", ".sv", ".v", ".tcl", ".xdc", ".toml", ".yml", ".yaml", ".txt", ".csv"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for token in forbidden:
            if token.lower() in text.lower() or token in text:
                hits.append(f"{path}: {token}")
    assert hits == []
