"""MSWU-inspired Kintex-7 structural Vivado runner."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tidl_poc.common.paths import outputs_dir, repo_root
from tidl_poc.vivado.baseline import (
    BENCHMARK_CLOCK_NS,
    CLASSIFICATION,
    REPORT_FILES,
    _plot_placement,
    _read_text,
    collect_case_result,
    run_vivado_batch,
    staging_root,
)
from tidl_poc.vivado.counts import expected_counts as multichain_counts
from tidl_poc.vivado.discover import (
    choose_kintex7_part,
    find_vivado,
    query_installed_kintex7_parts,
    query_vivado_version,
)
from tidl_poc.vivado.mswu_counts import MSWU_CARRY4_PER_TDL, expected_mswu_counts
from tidl_poc.vivado.mswu_evidence import write_mswu_evidence_snapshot
from tidl_poc.vivado.mswu_tcl import generate_mswu_case_tcl, generate_mswu_wrap_sv
from tidl_poc.vivado.reports import parse_carry_locs
from tidl_poc.vivado.status import reconcile_runner_status

from tidl_poc.vivado import baseline as _baseline

OUTPUT_NAME = "vivado_kintex7_mswu_structural"

# Round 7 multichain comparator (local evidence only).
MULTICHAIN_R7_16 = {
    "architecture": "8-chain multichain (Round 7 timing-clean)",
    "channels": 16,
    "carry4": 8192,
    "ff": 32800,
    "lut": 21547,
    "slices": 13669,
    "slices_pct": 53.92,
    "wns_ns": 3.045,
    "route_status": "fully_routed",
    "evidence": "docs/evidence/vivado_kintex7_timing_clean/",
}


@dataclass(frozen=True)
class MswuCase:
    case_id: str
    channels: int
    include_preencoder: bool
    shared_post: bool

    @property
    def chains_per_channel(self) -> int:
        return 1

    @property
    def carry4_per_chain(self) -> int:
        return MSWU_CARRY4_PER_TDL


def mswu_matrix() -> list[MswuCase]:
    return [
        MswuCase("mswu_structural_1ch_core", 1, False, False),
        MswuCase("mswu_structural_1ch_preencoder", 1, True, False),
        MswuCase("mswu_lowrate_16ch_frontends", 16, True, True),
        MswuCase("mswu_lowrate_8ch_frontends", 8, True, True),
        MswuCase("mswu_lowrate_4ch_frontends", 4, True, True),
    ]


def default_matrix() -> list[MswuCase]:
    return [c for c in mswu_matrix() if c.case_id != "mswu_lowrate_8ch_frontends" and c.case_id != "mswu_lowrate_4ch_frontends"]


def prepare_mswu_staging(repo: Path) -> tuple[Path, Path, Path, Path]:
    root = staging_root() / "mswu"
    mswu_dst = root / "mswu_rtl"
    k7_dst = root / "kintex7_rtl"
    mswu_dst.mkdir(parents=True, exist_ok=True)
    k7_dst.mkdir(parents=True, exist_ok=True)
    for name in (
        "carry4_tdl_chain.sv",
        "tdc_capture_bank.sv",
    ):
        shutil.copy2(repo / "rtl" / "tdc" / "kintex7" / name, k7_dst / name)
    for name in (
        "mswu_launcher_boundary.sv",
        "mswu_tdl_200.sv",
        "mswu_capture_quad.sv",
        "mswu_mbd5_preencoder_surrogate.sv",
        "mswu_channel_core.sv",
        "mswu_lowrate_shared_post.sv",
        "mswu_benchmark_top.sv",
    ):
        shutil.copy2(repo / "rtl" / "tdc" / "kintex7_mswu" / name, mswu_dst / name)
    xdc = root / "mswu_benchmark_ooc.xdc"
    shutil.copy2(repo / "constraints" / "kintex7_mswu" / "mswu_benchmark_ooc.xdc", xdc)
    return root, mswu_dst, k7_dst, xdc


def _mswu_to_benchmark_case(case: MswuCase) -> _baseline.BenchmarkCase:
    return _baseline.BenchmarkCase(
        channels=case.channels,
        chains_per_channel=1,
        carry4_per_chain=MSWU_CARRY4_PER_TDL,
        do_impl=True,
    )


def _collect_mswu_row(case: MswuCase, case_dir: Path, **kwargs: Any) -> dict[str, Any]:
    bench = _mswu_to_benchmark_case(case)
    row = collect_case_result(bench, case_dir, **kwargs)
    expected = expected_mswu_counts(case.channels)
    from tidl_poc.vivado.reports import parse_metrics_kv

    metrics = parse_metrics_kv(_read_text(case_dir / "metrics.txt"))
    bram = metrics.get("TIDL_BRAM_COUNT")
    row.update(
        {
            "case_id": case.case_id,
            "benchmark_variant": "mswu_structural",
            "include_preencoder": case.include_preencoder,
            "shared_post": case.shared_post,
            "expected_carry4": expected.carry4,
            "expected_capture_ff_min": expected.capture_ff_min,
            "logical_taps_per_tdl": expected.logical_taps,
            "capture_banks_per_channel": expected.capture_banks,
            "mapped_bram": int(bram) if bram is not None else None,
            "carry4_per_tdl": MSWU_CARRY4_PER_TDL,
        }
    )
    if row.get("mapped_carry4") != expected.carry4:
        row["carry4_mismatch"] = True
    row["capture_ff_ok"] = (
        row.get("mapped_fdre") is not None
        and int(row["mapped_fdre"]) >= expected.capture_ff_min
    )
    return row


def _plot_comparison(rows: list[dict[str, Any]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    from tidl_poc.common.plotting import save_figure

    mswu16 = next((r for r in rows if r.get("case_id") == "mswu_lowrate_16ch_frontends"), None)
    if not mswu16:
        mswu16 = max(rows, key=lambda r: r.get("channels") or 0)
    labels = ["multichain R7\n16ch", f"MSWU\n{mswu16.get('channels')}ch"]
    slices = [MULTICHAIN_R7_16["slices"], mswu16.get("slices") or 0]
    luts = [MULTICHAIN_R7_16["lut"], mswu16.get("slice_luts") or 0]
    fig, ax = plt.subplots(figsize=(5.5, 4.0))
    x = [0, 1]
    ax.bar([i - 0.15 for i in x], slices, width=0.3, label="slices")
    ax.bar([i + 0.15 for i in x], luts, width=0.3, label="LUT")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Local structural resource comparison (not metrology)")
    ax.legend(fontsize=8)
    save_figure(fig, out_dir / "resource_comparison")


def run(
    *,
    vivado: Path | None = None,
    skip_run: bool = False,
    timeout_s: float = 21600.0,
    only: str | None = None,
    export_only: bool = False,
    include_scaling_fallbacks: bool = False,
) -> dict[str, Any]:
    root = outputs_dir(OUTPUT_NAME)
    repo = repo_root()
    cases = mswu_matrix() if include_scaling_fallbacks else default_matrix()
    if only:
        cases = [c for c in mswu_matrix() if c.case_id == only]
        if not cases:
            raise ValueError(f"unknown MSWU case id {only!r}")

    version = None
    part = None
    exe = None
    prior = _baseline._load_json(root / "summary.json")
    if export_only:
        version = prior.get("vivado_version") or "2026.1"
        part = prior.get("part") or "xc7k160tffg676-2"
    else:
        exe = find_vivado(vivado)
        if exe is not None and not skip_run:
            version = query_vivado_version(exe)
            try:
                staging_root().mkdir(parents=True, exist_ok=True)
                version2, parts, blob = query_installed_kintex7_parts(
                    exe, staging_root() / "_discover_mswu.tcl"
                )
                version = version or version2
                part = choose_kintex7_part(parts) if parts else "xc7k160tffg676-2"
            except Exception:
                part = "xc7k160tffg676-2"
        elif exe is None and not skip_run:
            pass
        if part is None:
            part = "xc7k160tffg676-2"

    stage_root = mswu_rtl = k7_rtl = xdc = None
    if not export_only:
        stage_root, mswu_rtl, k7_rtl, xdc = prepare_mswu_staging(repo)

    results: list[dict[str, Any]] = []
    for case in cases:
        case_dir = root / case.case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        bench = _mswu_to_benchmark_case(case)
        expected = expected_mswu_counts(case.channels)

        if not export_only:
            stage_case = stage_root / case.case_id
            stage_case.mkdir(parents=True, exist_ok=True)
            wrap_path = stage_case / "mswu_benchmark_wrap.sv"
            tcl_path = stage_case / "run.tcl"
            wrap_path.write_text(
                generate_mswu_wrap_sv(
                    case_id=case.case_id,
                    n_channels=case.channels,
                    include_preencoder=case.include_preencoder,
                    shared_post=case.shared_post,
                ),
                encoding="utf-8",
            )
            tcl_path.write_text(
                generate_mswu_case_tcl(
                    part=part or "PART_UNSELECTED",
                    rtl_dir=mswu_rtl,
                    kintex7_rtl_dir=k7_rtl,
                    xdc_path=xdc,
                    wrap_path=wrap_path,
                    out_dir=stage_case,
                    n_carry4_per_tdl=MSWU_CARRY4_PER_TDL,
                    expected_capture_ff=expected.capture_ff_min,
                    place_guide=case.channels == 1,
                ),
                encoding="utf-8",
            )
            shutil.copy2(wrap_path, case_dir / "mswu_benchmark_wrap.sv")
            shutil.copy2(tcl_path, case_dir / "run.tcl")

        ran = exe is not None and part is not None and not skip_run and not export_only
        synth_ok = impl_ok = None
        returncode = None
        log_text = ""
        ran_this = False
        timed_out = False
        recon: dict[str, Any] | None = None

        if export_only or (ran and _baseline._case_already_complete(bench, case_dir)):
            log_text = _read_text(case_dir / "vivado.log")
            returncode = 0
        elif ran:
            ran_this = True
            log_path = stage_case / "vivado.log"
            returncode, log_text, timed_out = run_vivado_batch(
                exe, tcl_path, log_path, timeout_s=timeout_s
            )
        else:
            log_text = "vivado not run"

        if ran_this:
            for name in REPORT_FILES:
                src = stage_case / name
                if src.is_file():
                    shutil.copy2(src, case_dir / name)
            tp = stage_case / "timing_paths.rpt"
            if tp.is_file():
                shutil.copy2(tp, case_dir / "timing_paths.rpt")

        if ran or export_only:
            recon = reconcile_runner_status(
                channels=case.channels,
                chains_per_channel=1,
                carry4_per_chain=MSWU_CARRY4_PER_TDL,
                do_impl=True,
                case_dir=case_dir,
                timed_out=timed_out,
                returncode=returncode,
            )
            synth_ok = recon["synth_ok"]
            impl_ok = recon["impl_ok"]

        row = _collect_mswu_row(
            case,
            case_dir,
            synth_ok=synth_ok,
            impl_ok=impl_ok,
            returncode=returncode,
            log_text=log_text,
        )
        if recon:
            row["runner_status"] = recon["runner_status"]
            row["synth_status"] = recon["synth_status"]
            row["impl_status"] = recon["impl_status"]
        loc_rows = parse_carry_locs(_read_text(case_dir / "carry_locs.txt"))
        _plot_placement(case_dir, loc_rows)
        _baseline.write_json(case_dir / "summary.json", row)
        results.append(row)

    by_id = {r["case_id"]: r for r in results}
    for path in sorted(root.glob("mswu_*/summary.json")):
        try:
            prior_row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cid = prior_row.get("case_id")
        if isinstance(cid, str) and cid:
            by_id[cid] = prior_row
    results = list(by_id.values())
    results.sort(key=lambda r: r.get("case_id", ""))

    _plot_comparison(results, root)

    summary = {
        "result_classification": CLASSIFICATION,
        "benchmark_variant": "mswu_structural",
        "vivado_version": version,
        "part": part,
        "cases": results,
        "multichain_round7_comparator": MULTICHAIN_R7_16,
        "multichain_16_carry4": multichain_counts(16, 8, 64).carry4,
        "architecture_winner_selected": False,
        "synth_ok": sum(1 for r in results if r.get("synth_status") == "ok"),
        "impl_ok": sum(1 for r in results if r.get("impl_status") == "ok"),
    }
    _baseline.write_json(root / "summary.json", summary)

    evidence_path = None
    if export_only or any(r.get("synth_status") == "ok" for r in results):
        evidence_path = write_mswu_evidence_snapshot(
            cases=results,
            vivado_version=version,
            part=part,
            outputs_root=root,
            multichain_r7=MULTICHAIN_R7_16,
        )
        summary["evidence_snapshot"] = str(evidence_path.relative_to(repo))
        _baseline.write_json(root / "summary.json", summary)

    return {
        "output_dir": str(root),
        "evidence_dir": str(evidence_path) if evidence_path else None,
        "extra": summary,
    }
