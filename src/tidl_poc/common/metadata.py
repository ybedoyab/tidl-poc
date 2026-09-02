from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tidl_poc import (
    MEASUREMENT_DISCLAIMER,
    RESULT_CLASSIFICATION,
    RTL_DISCLAIMER,
    RTL_RESULT_CLASSIFICATION,
    SPICE_DISCLAIMER,
    SPICE_RESULT_CLASSIFICATION,
)

ALLOWED_RESULT_CLASSIFICATIONS = (
    RESULT_CLASSIFICATION,
    SPICE_RESULT_CLASSIFICATION,
    RTL_RESULT_CLASSIFICATION,
)

METADATA_REQUIRED_KEYS = (
    "script_name",
    "git_commit",
    "random_seed",
    "input_parameters",
    "datetime_utc",
    "result_classification",
    "disclaimer",
)


def git_commit() -> str | None:
    """Return HEAD SHA if this is a git checkout; otherwise None."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    sha = completed.stdout.strip()
    return sha or None


def build_metadata(
    *,
    script_name: str,
    random_seed: int,
    input_parameters: dict[str, Any],
    extra: dict[str, Any] | None = None,
    result_classification: str | None = None,
    disclaimer: str | None = None,
) -> dict[str, Any]:
    classification = result_classification or RESULT_CLASSIFICATION
    if classification not in ALLOWED_RESULT_CLASSIFICATIONS:
        raise ValueError(f"unsupported result_classification {classification!r}")
    text = disclaimer
    if text is None:
        if classification == SPICE_RESULT_CLASSIFICATION:
            text = SPICE_DISCLAIMER
        elif classification == RTL_RESULT_CLASSIFICATION:
            text = RTL_DISCLAIMER
        else:
            text = MEASUREMENT_DISCLAIMER
    payload: dict[str, Any] = {
        "script_name": script_name,
        "git_commit": git_commit(),
        "random_seed": int(random_seed),
        "input_parameters": input_parameters,
        "datetime_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "result_classification": classification,
        "disclaimer": text,
        "units_note": "Times are in seconds unless a field name ends with _ps, _ns, or _hz.",
    }
    if extra:
        payload["extra"] = extra
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_metadata(path: Path, **kwargs: Any) -> dict[str, Any]:
    payload = build_metadata(**kwargs)
    write_json(path, payload)
    return payload


def validate_metadata_schema(payload: dict[str, Any]) -> list[str]:
    missing = [key for key in METADATA_REQUIRED_KEYS if key not in payload]
    if payload.get("result_classification") not in ALLOWED_RESULT_CLASSIFICATIONS:
        missing.append("result_classification_value")
    if "not a physical measurement" not in str(payload.get("disclaimer", "")).lower():
        missing.append("disclaimer_text")
    return missing
