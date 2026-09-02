from tidl_poc import MEASUREMENT_DISCLAIMER, RESULT_CLASSIFICATION
from tidl_poc.common.metadata import build_metadata, validate_metadata_schema


def test_metadata_schema_complete():
    payload = build_metadata(
        script_name="test",
        random_seed=42,
        input_parameters={"a": 1},
    )
    assert validate_metadata_schema(payload) == []
    assert payload["result_classification"] == RESULT_CLASSIFICATION
    assert "not a physical measurement" in payload["disclaimer"].lower()


def test_spice_classification_is_allowed():
    from tidl_poc import SPICE_DISCLAIMER, SPICE_RESULT_CLASSIFICATION

    payload = build_metadata(
        script_name="spice",
        random_seed=1,
        input_parameters={},
        result_classification=SPICE_RESULT_CLASSIFICATION,
        disclaimer=SPICE_DISCLAIMER,
    )
    assert validate_metadata_schema(payload) == []
    assert MEASUREMENT_DISCLAIMER in payload["disclaimer"] or "not a physical measurement" in payload["disclaimer"].lower()


def test_rtl_classification_is_allowed():
    from tidl_poc import RTL_DISCLAIMER, RTL_RESULT_CLASSIFICATION

    payload = build_metadata(
        script_name="vivado",
        random_seed=1,
        input_parameters={},
        result_classification=RTL_RESULT_CLASSIFICATION,
        disclaimer=RTL_DISCLAIMER,
    )
    assert validate_metadata_schema(payload) == []
    assert payload["result_classification"] == RTL_RESULT_CLASSIFICATION
    assert "not a physical measurement" in payload["disclaimer"].lower()


def test_schema_rejects_missing_disclaimer():
    payload = build_metadata(script_name="x", random_seed=1, input_parameters={})
    payload["disclaimer"] = "nope"
    assert "disclaimer_text" in validate_metadata_schema(payload)
