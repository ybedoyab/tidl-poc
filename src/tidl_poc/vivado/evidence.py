"""Tracked compact Vivado evidence snapshot (not raw tool trees)."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

from tidl_poc import RTL_RESULT_CLASSIFICATION
from tidl_poc.common.metadata import git_commit
from tidl_poc.common.paths import repo_root
from tidl_poc.vivado.counts import expected_counts

EVIDENCE_DISCLAIMER = (
    "No physical timing measurement. No claim of 1 ps resolution, DNL, SSP, "
    "accuracy, or temperature performance."
)

EVIDENCE_RELATIVE = Path("docs") / "evidence" / "vivado_kintex7"
EVIDENCE_TIMING_CLEAN_RELATIVE = Path("docs") / "evidence" / "vivado_kintex7_timing_clean"

RESOURCE_FIELDS = [
    "case_id",
    "channels",
    "chains_per_channel",
    "carry4_per_chain",
    "expected_carry4",
    "mapped_carry4",
    "expected_taps",
    "expected_capture_ff_min",
    "mapped_fdre",
    "carry4_optimized_away",
    "slice_luts",
    "slice_registers",
    "slices",
    "slice_luts_pct",
    "slice_registers_pct",
    "slices_pct",
    "utilization_source",
    "synth_status",
    "impl_status",
    "runner_status",
]

IMPL_FIELDS = RESOURCE_FIELDS + [
    "impl_requested",
    "wns_ns",
    "tns_ns",
    "control_timing_closed",
    "route_status",
    "fully_routed",
    "n_chains_reported",
    "n_vertical_runs",
    "n_scattered_chains",
]


class Carry4MismatchError(RuntimeError):
    """Mapped CARRY4 does not match channels × 8 × carry4_per_chain."""


class CaptureFfMismatchError(RuntimeError):
    """Mapped FDRE count is below the structural capture-FF lower bound."""


def timing_clean_evidence_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / EVIDENCE_TIMING_CLEAN_RELATIVE


def assert_capture_ff_matches(cases: list[dict[str, Any]]) -> None:
    """Fail export if mapped FDRE is below channels × 8 × carry4 × 4."""
    mismatches: list[str] = []
    for row in cases:
        mapped = row.get("mapped_fdre")
        if mapped is None:
            continue
        expected_min = row.get("expected_capture_ff_min")
        if expected_min is None:
            channels = int(row["channels"])
            chains = int(row.get("chains_per_channel") or 8)
            n_c4 = int(row["carry4_per_chain"])
            expected_min = expected_counts(channels, chains, n_c4).capture_ff_min
        if int(mapped) < int(expected_min):
            mismatches.append(
                f"{row.get('case_id')}: mapped_fdre {mapped} < expected_min {expected_min}"
            )
    if mismatches:
        raise CaptureFfMismatchError(
            "mapped FDRE below structural capture-FF lower bound: " + "; ".join(mismatches)
        )


def evidence_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / EVIDENCE_RELATIVE


def git_commit_source() -> str:
    """HEAD SHA if the tree is clean; otherwise a pre-commit working-tree label."""
    sha = git_commit()
    if sha and not _working_tree_dirty():
        return sha
    return "generated from working tree immediately before commit"


def _working_tree_dirty() -> bool:
    try:
        import subprocess

        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return True
    return completed.returncode != 0 or bool(completed.stdout.strip())


def assert_mapped_carry4_matches(cases: list[dict[str, Any]]) -> None:
    """Fail evidence export if any mapped CARRY4 differs from the structural formula."""
    mismatches: list[str] = []
    for row in cases:
        mapped = row.get("mapped_carry4")
        if mapped is None:
            continue
        channels = int(row["channels"])
        chains = int(row.get("chains_per_channel") or 8)
        n_c4 = int(row["carry4_per_chain"])
        expected = expected_counts(channels, chains, n_c4).carry4
        if int(mapped) != expected:
            mismatches.append(
                f"{row.get('case_id')}: mapped {mapped} != expected {expected}"
            )
    if mismatches:
        raise Carry4MismatchError(
            "mapped CARRY4 does not match channels × 8 × carry4_per_chain: "
            + "; ".join(mismatches)
        )


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flattened: list[dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        placement = row.get("placement") if isinstance(row.get("placement"), dict) else {}
        out["n_chains_reported"] = placement.get("n_chains_reported")
        out["n_vertical_runs"] = placement.get("n_vertical_runs")
        out["n_scattered_chains"] = placement.get("n_scattered_chains")
        flattened.append(out)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in flattened:
            writer.writerow({k: row.get(k) for k in fieldnames})


def _copy_png(src: Path, dest: Path) -> bool:
    if not src.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    return True


def _case_status_summary(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact = []
    for row in cases:
        compact.append(
            {
                "case_id": row.get("case_id"),
                "channels": row.get("channels"),
                "carry4_per_chain": row.get("carry4_per_chain"),
                "synth_status": row.get("synth_status"),
                "impl_status": row.get("impl_status"),
                "runner_status": row.get("runner_status"),
                "mapped_carry4": row.get("mapped_carry4"),
                "expected_carry4": row.get("expected_carry4"),
                "slice_luts": row.get("slice_luts"),
                "mapped_fdre": row.get("mapped_fdre"),
                "slices": row.get("slices"),
                "wns_ns": row.get("wns_ns"),
                "route_status": row.get("route_status"),
            }
        )
    return compact


def write_evidence_readme(dest: Path) -> None:
    dest.write_text(
        """# Kintex-7 structural implementation evidence

This directory is a **tracked, compact snapshot** of the first Vivado 2026.1
Kintex-7 CARRY4 TDL matrix. Raw tool output stays gitignored under
`outputs/vivado_kintex7/` (logs, journals, `.runs`, `.cache`, `.Xil`,
checkpoints, and generated project internals). Reviewers can read the derived
tables and figures here without importing a machine-specific Vivado tree.

**Classification:** RTL/synthesis/implementation evidence.
**Part:** `xc7k160tffg676-2`. **Architecture:** 8 chains/channel, CARRY4-based.
No bitstream. No board pins assigned.

No physical timing measurement. No claim of 1 ps resolution, DNL, SSP,
accuracy, or temperature performance.

## Figures

- `resource_scaling.png` — LUT / FF / slice / CARRY4 counts versus channel
  count for the 32/48/64 CARRY4-per-chain sweep.
- `carry4_length_effect.png` — mapped CARRY4 versus channels and TDL length.
- `placement_1ch_64.png` — 1-channel, 64 CARRY4/chain LOC plot (8 vertical
  carry runs, no scatter). Generated from Vivado LOC text, not a GUI
  screenshot.
- `placement_16ch_64.png` — 16-channel, 64 CARRY4/chain LOC plot (128 chains,
  128 vertical runs, 0 scattered).

## Reproduce

From a machine with Vivado 2026.1 and the Kintex-7 device files:

```text
python -m tidl_poc vivado-baseline
```

or `python scripts/vivado/run_kintex7_baseline.py`. The runner synthesizes 12
cases (channels {1,4,8,16} × CARRY4 {32,48,64}) and place/routes the default
implementation subset (1-channel at 32/48/64 plus 1/4/8/16-channel at 64).

To rebuild this snapshot from already-completed local reports without
re-launching place/route:

```text
python -m tidl_poc vivado-baseline --export-only
```

Export fails if any mapped CARRY4 count differs from
`channels × 8 × carry4_per_chain`.

## 16×64 structural conclusion

The 16-channel × 8-chain × 64-CARRY4 topology mapped 8192 CARRY4 primitives
and fully routed on XC7K160T, using 10,980 slices (43.3% of device slices).
Resource scaling is approximately linear. That lowers implementation-capacity
risk. It does **not** prove metrological performance and does **not** select
multichain versus MSWU-B.

## WNS caveat

Negative WNS from the 1-channel / 64-CARRY4 case onward is synchronous
capture/control timing against the 4 ns benchmark clock. It is not a TDC-bin
measurement.

## Runner timeout anomaly (documented, then fixed)

The original 16×64 job used a 10800 s Python `subprocess.run` timeout. The
Python parent returned −1 while the Vivado child continued and later wrote
complete synthesis and implementation reports (`TIDL_SYNTH_STATUS=ok`,
`TIDL_IMPL_STATUS=ok`, CARRY4=8192). The first aggregate `summary.json`
incorrectly recorded `synth_status=failed` for that case.

The runner now:

1. uses `Popen` and, on timeout, kills the full process tree (`taskkill /T /F`
   on Windows) so jobs are not orphaned;
2. derives final status from **both** the subprocess outcome and validated
   report markers (utilization, `TIDL_*_STATUS=ok`, and mapped CARRY4 count);
3. can label a completed child as `recovered_after_timeout` instead of
   inventing a false `failed`.

A leftover file is never treated as success by itself.

## Round 7 timing-clean benchmark

See [docs/evidence/vivado_kintex7_timing_clean/](../evidence/vivado_kintex7_timing_clean/).
This directory is separate from Round 6 above; historical numbers are not overwritten.
""",
        encoding="utf-8",
    )


def write_evidence_snapshot(
    *,
    cases: list[dict[str, Any]],
    vivado_version: str | None,
    part: str | None,
    outputs_root: Path,
    dest: Path | None = None,
) -> Path:
    assert_mapped_carry4_matches(cases)
    dest = dest or evidence_dir()
    dest.mkdir(parents=True, exist_ok=True)

    _write_csv(dest / "resource_scaling.csv", cases, RESOURCE_FIELDS)
    _write_csv(dest / "implementation_summary.csv", cases, IMPL_FIELDS)

    copies = {
        "resource_scaling.png": outputs_root / "resource_scaling.png",
        "carry4_length_effect.png": outputs_root / "carry4_length_effect.png",
        "placement_1ch_64.png": outputs_root / "ch01_nch08_c4_64" / "carry4_placement.png",
        "placement_16ch_64.png": outputs_root / "ch16_nch08_c4_64" / "carry4_placement.png",
    }
    copied: dict[str, bool] = {}
    for name, src in copies.items():
        copied[name] = _copy_png(src, dest / name)

    impl_ok = [c for c in cases if c.get("impl_status") == "ok"]
    synth_ok = [c for c in cases if c.get("synth_status") == "ok"]
    synth_fail = [c for c in cases if c.get("synth_status") == "failed"]
    synth_timeout = [c for c in cases if c.get("synth_status") == "timeout"]
    synth_skip = [c for c in cases if c.get("synth_status") in {"skipped", "not_run"}]
    impl_fail = [c for c in cases if c.get("impl_requested") and c.get("impl_status") == "failed"]
    impl_timeout = [c for c in cases if c.get("impl_requested") and c.get("impl_status") == "timeout"]
    impl_skip = [c for c in cases if c.get("impl_status") in {"skipped", "not_run"} or not c.get("impl_requested")]

    case16 = next((c for c in cases if c.get("case_id") == "ch16_nch08_c4_64"), {})
    placement16 = case16.get("placement") if isinstance(case16.get("placement"), dict) else {}

    manifest = {
        "classification": RTL_RESULT_CLASSIFICATION,
        "vivado_version": vivado_version or "2026.1",
        "target_part": part or "xc7k160tffg676-2",
        "git_commit_source": git_commit_source(),
        "architecture": {
            "fine_tdc": "CARRY4-based structural TDL",
            "chains_per_channel": 8,
            "carry4_per_chain_swept": [32, 48, 64],
            "channels_swept": [1, 4, 8, 16],
        },
        "bitstream_generated": False,
        "board_pins_assigned": False,
        "case_count": len(cases),
        "synthesis": {
            "succeeded": len(synth_ok),
            "failed": len(synth_fail),
            "timeout": len(synth_timeout),
            "skipped": len(synth_skip),
        },
        "implementation": {
            "succeeded": len(impl_ok),
            "failed": len(impl_fail),
            "timeout": len(impl_timeout),
            "skipped": len(impl_skip),
            "implemented_case_count": len(impl_ok),
        },
        "cases": _case_status_summary(cases),
        "sixteen_channel_64": {
            "mapped_carry4": case16.get("mapped_carry4"),
            "expected_carry4": case16.get("expected_carry4"),
            "mapped_fdre": case16.get("mapped_fdre"),
            "slice_luts": case16.get("slice_luts"),
            "slices": case16.get("slices"),
            "slices_pct": case16.get("slices_pct"),
            "wns_ns": case16.get("wns_ns"),
            "route_status": case16.get("route_status"),
            "n_chains_reported": placement16.get("n_chains_reported"),
            "n_vertical_runs": placement16.get("n_vertical_runs"),
            "n_scattered_chains": placement16.get("n_scattered_chains"),
        },
        "figures_copied": copied,
        "timeout_anomaly": {
            "documented": True,
            "case_id": "ch16_nch08_c4_64",
            "note": (
                "The first Python runner recorded synth_status=failed after a "
                "10800 s subprocess timeout (returncode -1) while Vivado "
                "continued and later wrote complete reports. Status is now "
                "reconciled from process outcome plus validated report markers."
            ),
        },
        "disclaimer": EVIDENCE_DISCLAIMER,
    }
    (dest / "evidence_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_evidence_readme(dest / "README.md")
    return dest


def write_timing_clean_evidence_readme(dest: Path) -> None:
    dest.write_text(
        """# Kintex-7 timing-clean structural benchmark

**Classification:** RTL/synthesis/implementation evidence.
**Vivado:** 2026.1. **Part:** `xc7k160tffg676-2`.
**Clock:** 4.000 ns on `clk` (synchronous capture/benchmark-control only).
**Asynchronous hit** inputs are narrowly false-pathed; `rst_n` into FDRE.R only.

This snapshot reran synthesis and place/route for channels {1,4,8,16} at
**64 CARRY4 per chain** after removing the Round-6 **benchmark-only wide XOR
parity tree**. Capture FFs are retained via `KEEP` / `DONT_TOUCH`; the top
exposes one registered bit per channel (chain-0 tap 0) as `bench_status`.

No physical timing measurement. No claim of 1 ps resolution, DNL, SSP,
accuracy, or temperature performance.

## Comparison to Round 6

| | Round 6 (`docs/evidence/vivado_kintex7/`) | This snapshot |
| --- | --- | --- |
| Observability | Wide `^captured_k` parity per chain, hierarchical XOR to `tap_parity` | KEEP on capture bank; one tap per channel registered |
| Matrix | 12 synth; 6 impl (32/48/64 sweep) | 4 impl @ 64 CARRY4/chain only |
| 8/16-ch P&R | `place_design -no_timing_driven` on some cases | Timing-driven place/route |
| WNS | Negative from 1ch/64 upward (likely parity tree) | See `implementation_summary.csv` |

Round-6 numbers are **not** overwritten. Resource deltas vs Round-6 @64 are
mostly LUT/FF reduction from removing parity XOR trees; CARRY4 and capture FF
counts should match structural expectations.

## Figures

- `resource_scaling.png` — slices / LUT / FF / CARRY4 vs channels @ 64 CARRY4/chain.
- `timing_scaling.png` — 4 ns WNS vs channels (not TDC-bin timing).
- `placement_16ch_64.png` — 16×64 LOC plot from Vivado text.

## Reproduce

```text
python -m tidl_poc vivado-timing-clean
python -m tidl_poc vivado-timing-clean --export-only
```

Raw Vivado trees stay gitignored under `outputs/vivado_kintex7_timing_clean/`.
""",
        encoding="utf-8",
    )


def write_timing_clean_evidence_snapshot(
    *,
    cases: list[dict[str, Any]],
    vivado_version: str | None,
    part: str | None,
    outputs_root: Path,
    dest: Path | None = None,
) -> Path:
    assert_mapped_carry4_matches(cases)
    assert_capture_ff_matches(cases)
    dest = dest or timing_clean_evidence_dir()
    dest.mkdir(parents=True, exist_ok=True)

    _write_csv(dest / "implementation_summary.csv", cases, IMPL_FIELDS)

    copies = {
        "resource_scaling.png": outputs_root / "resource_scaling.png",
        "timing_scaling.png": outputs_root / "timing_scaling.png",
        "placement_16ch_64.png": outputs_root / "ch16_nch08_c4_64" / "carry4_placement.png",
    }
    copied: dict[str, bool] = {}
    for name, src in copies.items():
        copied[name] = _copy_png(src, dest / name)

    case16 = next((c for c in cases if c.get("case_id") == "ch16_nch08_c4_64"), {})
    placement16 = case16.get("placement") if isinstance(case16.get("placement"), dict) else {}
    wns16 = case16.get("wns_ns")
    meets_4ns = isinstance(wns16, (int, float)) and wns16 >= 0

    manifest = {
        "classification": RTL_RESULT_CLASSIFICATION,
        "benchmark_variant": "timing_clean",
        "vivado_version": vivado_version or "2026.1",
        "target_part": part or "xc7k160tffg676-2",
        "benchmark_clock_ns": 4.0,
        "clock_scope": "synchronous capture/benchmark-control logic only",
        "async_hit_false_path": "narrow: hit[*] ports only",
        "observability": (
            "Round-6 wide XOR parity tree removed. Capture FFs retained via "
            "KEEP/DONT_TOUCH; bench_status registers chain-0 tap 0 per channel."
        ),
        "round6_comparison": {
            "historical_snapshot": "docs/evidence/vivado_kintex7/",
            "round6_wns_issue": (
                "Negative WNS from 1ch/64 upward was likely the benchmark-only "
                "wide parity reduction network, not the CARRY4 TDL structure."
            ),
        },
        "git_commit_source": git_commit_source(),
        "bitstream_generated": False,
        "board_pins_assigned": False,
        "case_count": len(cases),
        "cases": _case_status_summary(cases),
        "sixteen_channel_64": {
            "expected_carry4": case16.get("expected_carry4"),
            "mapped_carry4": case16.get("mapped_carry4"),
            "expected_capture_ff_min": case16.get("expected_capture_ff_min"),
            "mapped_fdre": case16.get("mapped_fdre"),
            "capture_ff_ok": case16.get("capture_ff_ok"),
            "slice_luts": case16.get("slice_luts"),
            "slices": case16.get("slices"),
            "slices_pct": case16.get("slices_pct"),
            "wns_ns": wns16,
            "tns_ns": case16.get("tns_ns"),
            "route_status": case16.get("route_status"),
            "meets_4ns_benchmark": meets_4ns,
            "n_chains_reported": placement16.get("n_chains_reported"),
            "n_vertical_runs": placement16.get("n_vertical_runs"),
            "n_scattered_chains": placement16.get("n_scattered_chains"),
        },
        "figures_copied": copied,
        "disclaimer": EVIDENCE_DISCLAIMER,
    }
    (dest / "evidence_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_timing_clean_evidence_readme(dest / "README.md")
    return dest
