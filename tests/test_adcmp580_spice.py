from pathlib import Path

import pytest

from tidl_poc import SPICE_DISCLAIMER, SPICE_RESULT_CLASSIFICATION
from tidl_poc.common.metadata import build_metadata, validate_metadata_schema
from tidl_poc.spice.adcmp580 import (
    DISPERSION_CSV_COLUMNS,
    RISE_CSV_COLUMNS,
    generate_dispersion_cases,
    generate_rise_cases,
    generate_sweep_cases,
    polarity_sign,
    propagation_dispersion_ps,
    schematic_path,
)
from tidl_poc.spice.ltspice import parse_meas_log, switched_clean

SAMPLE_LOG = """
LTspice 26.0.2 for Windows
Direct Newton iteration succeeded in finding operating point.
Total elapsed time: 0.548 seconds.

t_in: V(VP)-V(VN)=0  AT 2.1e-10
t_out: V(Q)-V(QB)=0  AT 4.13765145644e-10
tpd: t_out-t_in=2.03765145644e-10
vout_max: MAX(V(Q)-V(QB))=0.4 FROM 0 TO 2.22e-09
vout_min: MIN(V(Q)-V(QB))=-0.4 FROM 0 TO 2.22e-09
"""

STEPPED_LOG = """
Measurement: tpd
step	tpd
1	2.00e-10
2	2.10e-10
3	2.20e-10
4	2.50e-10

Measurement: t_in
step	t_in
1	2.1e-10
2	2.1e-10
3	2.1e-10
4	2.1e-10

Measurement: vout_max
  step	MAX(V(Q)-V(QB))	FROM	TO
     1	0.4	0	2.21e-09
     2	0.4	0	2.22e-09
"""


def test_parse_single_meas_log():
    meas = parse_meas_log(SAMPLE_LOG)
    assert meas["t_in"] == 2.1e-10
    assert meas["tpd"] == 2.03765145644e-10
    assert meas["vout_max"] == 0.4
    assert meas["vout_min"] == -0.4
    assert switched_clean(meas["vout_max"], meas["vout_min"])


def test_parse_stepped_meas_log():
    meas = parse_meas_log(STEPPED_LOG)
    assert meas["tpd"] == [2.00e-10, 2.10e-10, 2.20e-10, 2.50e-10]
    assert len(meas["t_in"]) == 4
    assert meas["vout_max"] == [0.4, 0.4]


def test_propagation_dispersion_arithmetic():
    assert propagation_dispersion_ps([200e-12, 180e-12, 205e-12]) == pytest.approx(25.0)


def test_sweep_parameter_generation_counts():
    fast = generate_sweep_cases(fast=True)
    full = generate_sweep_cases(fast=False)
    assert len(generate_dispersion_cases(fast=True)) == 4
    assert len(generate_rise_cases(fast=True)) == 2
    assert len(fast) == 6
    assert len(generate_dispersion_cases(fast=False)) == 56
    assert len(generate_rise_cases(fast=False)) == 12
    assert len(full) == 68
    assert polarity_sign("rise") == 1
    assert polarity_sign("fall") == -1


def test_spice_metadata_classification():
    payload = build_metadata(
        script_name="tidl_poc.spice.adcmp580",
        random_seed=42,
        input_parameters={"schematic": "spice/adcmp580/tidl_adcmp580_characterization.asc"},
        extra={"hardware_measured": False},
        result_classification=SPICE_RESULT_CLASSIFICATION,
        disclaimer=SPICE_DISCLAIMER,
    )
    assert validate_metadata_schema(payload) == []
    assert payload["result_classification"] == "SPICE/front-end simulation"
    assert "not a physical measurement" in payload["disclaimer"].lower()


def test_output_table_schema_constants():
    assert "tpd_ps" in DISPERSION_CSV_COLUMNS
    assert "overdrive_v" in DISPERSION_CSV_COLUMNS
    assert "rise_time_s" in RISE_CSV_COLUMNS
    assert "switched_clean" in RISE_CSV_COLUMNS


def test_tracked_files_have_no_machine_paths():
    root = Path(__file__).resolve().parents[1]
    needles = (
        r"C:\Users",
        "C:/Users",
        "AppData\\Local\\LTspice",
        "AppData/Local/LTspice",
        "Programs\\ADI\\LTspice",
    )
    tracked = [
        root / "spice" / "adcmp580" / "tidl_adcmp580_characterization.asc",
        root / "src" / "tidl_poc" / "spice" / "adcmp580.py",
        root / "src" / "tidl_poc" / "spice" / "ltspice.py",
        root / "scripts" / "ltspice" / "run_adcmp580.py",
        root / "docs" / "analysis" / "frontend-adcmp580-spice.md",
        root / "docs" / "analysis" / "cml-to-kintex7-interface-options.md",
    ]
    for path in tracked:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            assert needle not in text, f"{path} contains {needle!r}"


def test_committed_schematic_is_original_and_named():
    text = schematic_path().read_text(encoding="utf-8")
    assert "ADCMP580" in text
    assert "Not a vendor example copy" in text
    assert "Vod=" in text
    assert "SYMATTR Value 50" in text
    assert "SYMATTR Value 0.4" in text
