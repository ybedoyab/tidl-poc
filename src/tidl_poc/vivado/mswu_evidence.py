"""Tracked MSWU-inspired structural evidence snapshot."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

from tidl_poc import RTL_RESULT_CLASSIFICATION
from tidl_poc.common.paths import repo_root
from tidl_poc.vivado.evidence import (
    CaptureFfMismatchError,
    Carry4MismatchError,
    git_commit_source,
)

EVIDENCE_RELATIVE = Path("docs") / "evidence" / "vivado_kintex7_mswu_structural"

MSWU_DISCLAIMER = (
    "This is a project-authored structural/resource surrogate informed by published "
    "MSWU-B architecture. Vivado does not validate Wave Union pulse generation, "
    "picosecond bin widths, DNL, SSP, accuracy, or temperature behavior."
)

IMPL_FIELDS = [
    "case_id",
    "channels",
    "include_preencoder",
    "shared_post",
    "expected_carry4",
    "mapped_carry4",
    "expected_capture_ff_min",
    "mapped_fdre",
    "capture_ff_ok",
    "slice_luts",
    "slice_registers",
    "slices",
    "slices_pct",
    "mapped_bram",
    "wns_ns",
    "tns_ns",
    "control_timing_closed",
    "route_status",
    "fully_routed",
    "n_chains_reported",
    "n_vertical_runs",
    "n_scattered_chains",
    "synth_status",
    "impl_status",
]


def evidence_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / EVIDENCE_RELATIVE


def assert_mswu_carry4(cases: list[dict[str, Any]]) -> None:
    mismatches = []
    for row in cases:
        exp = row.get("expected_carry4")
        mapped = row.get("mapped_carry4")
        if exp is None or mapped is None:
            continue
        if int(mapped) != int(exp):
            mismatches.append(f"{row.get('case_id')}: {mapped} != {exp}")
    if mismatches:
        raise Carry4MismatchError("; ".join(mismatches))


def assert_mswu_capture_ff(cases: list[dict[str, Any]]) -> None:
    mismatches = []
    for row in cases:
        exp = row.get("expected_capture_ff_min")
        mapped = row.get("mapped_fdre")
        if exp is None or mapped is None:
            continue
        if int(mapped) < int(exp):
            mismatches.append(f"{row.get('case_id')}: {mapped} < {exp}")
    if mismatches:
        raise CaptureFfMismatchError("; ".join(mismatches))


def write_mswu_evidence_snapshot(
    *,
    cases: list[dict[str, Any]],
    vivado_version: str | None,
    part: str | None,
    outputs_root: Path,
    multichain_r7: dict[str, Any],
    dest: Path | None = None,
) -> Path:
    assert_mswu_carry4(cases)
    assert_mswu_capture_ff(cases)
    dest = dest or evidence_dir()
    dest.mkdir(parents=True, exist_ok=True)

    with (dest / "implementation_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=IMPL_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in cases:
            flat = dict(row)
            placement = row.get("placement") if isinstance(row.get("placement"), dict) else {}
            flat["n_chains_reported"] = placement.get("n_chains_reported")
            flat["n_vertical_runs"] = placement.get("n_vertical_runs")
            flat["n_scattered_chains"] = placement.get("n_scattered_chains")
            writer.writerow({k: flat.get(k) for k in IMPL_FIELDS})

    resource_rows = []
    for row in cases:
        resource_rows.append(
            {
                "case_id": row.get("case_id"),
                "channels": row.get("channels"),
                "mapped_carry4": row.get("mapped_carry4"),
                "mapped_fdre": row.get("mapped_fdre"),
                "slice_luts": row.get("slice_luts"),
                "slices": row.get("slices"),
                "slices_pct": row.get("slices_pct"),
                "mapped_bram": row.get("mapped_bram"),
            }
        )
    with (dest / "resource_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(resource_rows[0].keys()))
        writer.writeheader()
        writer.writerows(resource_rows)

    copies = {
        "resource_comparison.png": outputs_root / "resource_comparison.png",
        "placement_1ch.png": outputs_root / "mswu_structural_1ch_core" / "carry4_placement.png",
        "placement_16ch.png": outputs_root / "mswu_lowrate_16ch_frontends" / "carry4_placement.png",
    }
    copied = {}
    for name, src in copies.items():
        if src.is_file():
            shutil.copyfile(src, dest / name)
            copied[name] = True
        else:
            copied[name] = False

    mswu16 = next((c for c in cases if c.get("case_id") == "mswu_lowrate_16ch_frontends"), {})
    if not mswu16:
        mswu16 = max(cases, key=lambda c: c.get("channels") or 0)

    manifest = {
        "classification": RTL_RESULT_CLASSIFICATION,
        "benchmark_variant": "mswu_structural_surrogate",
        "vivado_version": vivado_version or "2026.1",
        "target_part": part or "xc7k160tffg676-2",
        "git_commit_source": git_commit_source(),
        "architecture_winner_selected": False,
        "cases": cases,
        "comparison": {
            "local_multichain_round7": multichain_r7,
            "local_mswu_highest_channel": {
                "case_id": mswu16.get("case_id"),
                "channels": mswu16.get("channels"),
                "carry4": mswu16.get("mapped_carry4"),
                "ff": mswu16.get("mapped_fdre"),
                "lut": mswu16.get("slice_luts"),
                "slices": mswu16.get("slices"),
                "slices_pct": mswu16.get("slices_pct"),
                "wns_ns": mswu16.get("wns_ns"),
                "route_status": mswu16.get("route_status"),
            },
            "literature_kwiatkowski_2023_one_channel": {
                "evidence_class": "literature evidence",
                "lut": 2840,
                "ff": 1165,
                "slices": 953,
                "bram": 21.5,
                "note": "Paper-reported complete measurement channel; not local",
            },
            "metrology_comparison_allowed": False,
        },
        "figures_copied": copied,
        "disclaimer": MSWU_DISCLAIMER,
    }
    (dest / "evidence_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (dest / "README.md").write_text(
        _readme_text(multichain_r7, mswu16),
        encoding="utf-8",
    )
    return dest


def _readme_text(multichain_r7: dict[str, Any], mswu_row: dict[str, Any]) -> str:
    return f"""# Kintex-7 MSWU-inspired structural evidence

**Classification:** RTL/synthesis/implementation evidence.
**Part:** `xc7k160tffg676-2`. **Vivado:** 2026.1.

Original project-authored structural surrogate informed by Kwiatkowski et al. 2023
(Measurement 209, 112510). HDL is **not** copied from the paper or third parties.
Wave Union pulse generation is **not** validated by Vivado.

{MSWU_DISCLAIMER}

## Local cases

| case_id | role |
| --- | --- |
| `mswu_structural_1ch_core` | 1× TDL + 4 capture banks |
| `mswu_structural_1ch_preencoder` | + MBD=5 pre-encoder surrogate |
| `mswu_lowrate_16ch_frontends` | 16 independent front-ends + shared low-rate post |

Front-ends are never shared between simultaneous channels; only post-capture
processing may be serialized at 16 events/s.

## Comparison (structural resources only — not metrology)

| Architecture | Source | CARRY4 | FF | LUT | Slices | WNS | Route |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8-chain multichain R7 16ch | local Round 7 | {multichain_r7.get('carry4')} | {multichain_r7.get('ff')} | {multichain_r7.get('lut')} | {multichain_r7.get('slices')} | {multichain_r7.get('wns_ns')} ns | {multichain_r7.get('route_status')} |
| MSWU surrogate {mswu_row.get('channels')}ch | local this snapshot | {mswu_row.get('mapped_carry4')} | {mswu_row.get('mapped_fdre')} | {mswu_row.get('slice_luts')} | {mswu_row.get('slices')} | {mswu_row.get('wns_ns')} | {mswu_row.get('route_status')} |
| Kwiatkowski 2023 1ch complete | literature | n/a | 1165 | 2840 | 953 | n/a | n/a |

**No architecture selected solely from Vivado resource evidence.**

## Reproduce

```text
python -m tidl_poc vivado-mswu-structural
python -m tidl_poc vivado-mswu-structural --export-only
```

Raw Vivado trees: gitignored `outputs/vivado_kintex7_mswu_structural/`.
"""
