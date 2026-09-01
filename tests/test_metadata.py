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
    assert MEASUREMENT_DISCLAIMER in payload["disclaimer"] or "not a physical measurement" in payload["disclaimer"].lower()


def test_schema_rejects_missing_disclaimer():
    payload = build_metadata(script_name="x", random_seed=1, input_parameters={})
    payload["disclaimer"] = "nope"
    assert "disclaimer_text" in validate_metadata_schema(payload)
