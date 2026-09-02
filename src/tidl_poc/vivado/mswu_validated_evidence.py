"""Round-9 validated MSWU structural evidence export."""

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

EVIDENCE_RELATIVE = Path("docs") / "evidence" / "vivado_kintex7_mswu_validated"
ROUND8_EVIDENCE = Path("docs") / "evidence" / "vivado_kintex7_mswu_structural"

MSWU_DISCLAIMER = (
    "This is a project-authored structural/resource surrogate informed by published "
    "MSWU-B architecture. Vivado does not validate Wave Union pulse generation, "
    "picosecond bin widths, DNL, SSP, accuracy, or temperature behavior."
)

ROUND9_SUPERSESSION_NOTE = (
    "Round 8's nominal 1-channel preencoder LUT result was not a valid measure of "
    "the intended preencoder logic because benchmark outputs were not retained and "
    "only subregion 0 was selected. Round 9 corrects benchmark observability and "
    "exercises all MBD=5 regions."
)

IMPL_FIELDS = [
    "case_id",
    "channels",
    "preenc_mode",
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
    "expected_tdl_chains",
    "n_chains_reported",
    "n_vertical_runs",
    "n_scattered_chains",
    "n_unmatched_carry4",
    "preenc_lut_ok",
    "preenc_optimized_away",
    "synth_status",
    "impl_status",
]


class PreencoderOptimizedAwayError(RuntimeError):
    pass


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


def assert_preencoder_not_optimized(cases: list[dict[str, Any]]) -> None:
    bad = [r["case_id"] for r in cases if r.get("preenc_optimized_away")]
    if bad:
        raise PreencoderOptimizedAwayError(
            f"preencoder logic likely optimized away: {', '.join(bad)}"
        )


def write_validated_evidence_snapshot(
    *,
    cases: list[dict[str, Any]],
    vivado_version: str | None,
    part: str | None,
    outputs_root: Path,
    multichain_r7: dict[str, Any],
    round8_superseded: dict[str, Any] | None = None,
    dest: Path | None = None,
) -> Path:
    assert_mswu_carry4(cases)
    assert_mswu_capture_ff(cases)
    assert_preencoder_not_optimized(cases)
    dest = dest or evidence_dir()
    dest.mkdir(parents=True, exist_ok=True)

    with (dest / "implementation_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=IMPL_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in cases:
            flat = dict(row)
            placement = row.get("placement") if isinstance(row.get("placement"), dict) else {}
            flat["expected_tdl_chains"] = placement.get("expected_tdl_chains")
            flat["n_chains_reported"] = placement.get("n_chains_reported")
            flat["n_vertical_runs"] = placement.get("n_vertical_runs")
            flat["n_scattered_chains"] = placement.get("n_scattered_chains")
            flat["n_unmatched_carry4"] = placement.get("n_unmatched_carry4")
            writer.writerow({k: flat.get(k) for k in IMPL_FIELDS})

    resource_rows = [
        {
            "case_id": row.get("case_id"),
            "channels": row.get("channels"),
            "preenc_mode": row.get("preenc_mode"),
            "mapped_carry4": row.get("mapped_carry4"),
            "mapped_fdre": row.get("mapped_fdre"),
            "slice_luts": row.get("slice_luts"),
            "slices": row.get("slices"),
            "slices_pct": row.get("slices_pct"),
            "mapped_bram": row.get("mapped_bram"),
            "wns_ns": row.get("wns_ns"),
        }
        for row in cases
    ]
    with (dest / "resource_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(resource_rows[0].keys()))
        writer.writeheader()
        writer.writerows(resource_rows)

    copies = {
        "resource_comparison.png": outputs_root / "resource_comparison.png",
        "timing_comparison.png": outputs_root / "timing_comparison.png",
        "placement_1ch.png": outputs_root / "mswu_1ch_core_r9" / "carry4_placement.png",
        "placement_16ch.png": outputs_root / "mswu_lowrate_16ch_frontends_r9" / "carry4_placement.png",
    }
    copied = {}
    for name, src in copies.items():
        if src.is_file():
            shutil.copyfile(src, dest / name)
            copied[name] = True
        else:
            copied[name] = False

    mswu16 = next((c for c in cases if c.get("case_id") == "mswu_lowrate_16ch_frontends_r9"), {})
    if not mswu16:
        mswu16 = max(cases, key=lambda c: c.get("channels") or 0)

    manifest = {
        "classification": RTL_RESULT_CLASSIFICATION,
        "benchmark_variant": "mswu_structural_validated_r9",
        "round": 9,
        "supersedes_round8_preencoder_lut": True,
        "round8_superseded_claim": round8_superseded,
        "round9_supersession_note": ROUND9_SUPERSESSION_NOTE,
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
        _readme_text(multichain_r7, mswu16, round8_superseded),
        encoding="utf-8",
    )
    return dest


def _readme_text(
    multichain_r7: dict[str, Any],
    mswu_row: dict[str, Any],
    round8_superseded: dict[str, Any] | None,
) -> str:
    r8_lut = (round8_superseded or {}).get("slice_luts", "3")
    r8_case = (round8_superseded or {}).get("case_id", "mswu_structural_1ch_preencoder")
    return f"""# Kintex-7 MSWU-inspired structural evidence (Round 9 validated)

**Classification:** RTL/synthesis/implementation evidence.
**Part:** `xc7k160tffg676-2`. **Vivado:** 2026.1.

{ROUND9_SUPERSESSION_NOTE}

Round 8 historical snapshot preserved at `{ROUND8_EVIDENCE}/`.
Round 8 `{r8_case}` LUT={r8_lut} is **superseded** for preencoder resource claims.

{MSWU_DISCLAIMER}

## Round 9 local cases

| case_id | role |
| --- | --- |
| `mswu_1ch_core_r9` | 1× TDL + 4 capture banks |
| `mswu_1ch_preenc_seq_r9` | + low-rate sequential MBD=5 scanner (all 5 regions) |
| `mswu_1ch_preenc_parallel_r9` | + parallel 4×5 region encoders (upper bound) |
| `mswu_lowrate_16ch_frontends_r9` | 16 independent front-ends + pipelined shared post |

## Comparison (structural resources only — not metrology)

| Architecture | Source | CARRY4 | FF | LUT | Slices | WNS | Route |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8-chain multichain R7 16ch | local Round 7 | {multichain_r7.get('carry4')} | {multichain_r7.get('ff')} | {multichain_r7.get('lut')} | {multichain_r7.get('slices')} | {multichain_r7.get('wns_ns')} ns | {multichain_r7.get('route_status')} |
| MSWU validated {mswu_row.get('channels')}ch | local Round 9 | {mswu_row.get('mapped_carry4')} | {mswu_row.get('mapped_fdre')} | {mswu_row.get('slice_luts')} | {mswu_row.get('slices')} | {mswu_row.get('wns_ns')} | {mswu_row.get('route_status')} |
| Kwiatkowski 2023 1ch complete | literature | n/a | 1165 | 2840 | 953 | n/a | n/a |

**No architecture selected solely from Vivado resource evidence.**

## Reproduce

```text
python -m tidl_poc vivado-mswu-validated
python -m tidl_poc vivado-mswu-validated --export-only
```

Raw Vivado trees: gitignored `outputs/vivado_kintex7_mswu_validated/`.
"""
