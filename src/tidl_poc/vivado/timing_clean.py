"""Timing-clean Kintex-7 structural benchmark (64 CARRY4/channel scaling only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tidl_poc.common.paths import outputs_dir, repo_root
from tidl_poc.vivado.baseline import (
    BENCHMARK_CLOCK_NS,
    CHAINS_PER_CHANNEL,
    BenchmarkCase,
    CLASSIFICATION,
    _plot_placement,
    case_output_dir,
    collect_case_result,
    prepare_staging,
    run_vivado_batch,
    staging_root,
)
from tidl_poc.vivado.counts import expected_counts
from tidl_poc.vivado.discover import (
    choose_kintex7_part,
    find_vivado,
    query_installed_kintex7_parts,
    query_vivado_version,
)
from tidl_poc.vivado.evidence import (
    assert_capture_ff_matches,
    assert_mapped_carry4_matches,
    write_timing_clean_evidence_snapshot,
)
from tidl_poc.vivado.reports import parse_carry_locs
from tidl_poc.vivado.status import reconcile_runner_status
from tidl_poc.vivado.tcl import generate_case_tcl, generate_wrap_sv

from tidl_poc.vivado import baseline as _baseline

CHANNELS_64 = (1, 4, 8, 16)
CARRY4_PER_CHAIN = 64
OUTPUT_NAME = "vivado_kintex7_timing_clean"


def timing_clean_matrix() -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            channels=n,
            chains_per_channel=CHAINS_PER_CHANNEL,
            carry4_per_chain=CARRY4_PER_CHAIN,
            do_impl=True,
        )
        for n in CHANNELS_64
    ]


def _plot_timing_scaling(rows: list[dict[str, Any]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    from tidl_poc.common.plotting import save_figure

    subset = sorted(
        [r for r in rows if r.get("wns_ns") is not None],
        key=lambda r: r["channels"],
    )
    if not subset:
        return
    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    xs = [r["channels"] for r in subset]
    wns = [r["wns_ns"] for r in subset]
    ax.axhline(0.0, color="0.5", lw=0.8, linestyle="--")
    ax.plot(xs, wns, marker="o", label="WNS (ns)")
    ax.set_xlabel("channels")
    ax.set_ylabel("WNS (ns)")
    ax.set_title("4 ns capture-clock WNS vs channels (timing-clean benchmark)")
    ax.legend()
    save_figure(fig, out_dir / "timing_scaling")


def _plot_resource_scaling(rows: list[dict[str, Any]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    from tidl_poc.common.plotting import save_figure

    subset = sorted(rows, key=lambda r: r["channels"])
    if not subset:
        return
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    xs = [r["channels"] for r in subset]
    ax.plot(xs, [r.get("slices") or 0 for r in subset], marker="o", label="slices")
    ax.plot(xs, [r.get("slice_luts") or 0 for r in subset], marker="s", label="LUT")
    ax.plot(xs, [r.get("mapped_fdre") or 0 for r in subset], marker="^", label="FF")
    ax.plot(xs, [r.get("mapped_carry4") or 0 for r in subset], marker="d", label="CARRY4")
    ax.set_xlabel("channels")
    ax.set_ylabel("count")
    ax.set_title("Resources vs channels @ 64 CARRY4/chain (timing-clean)")
    ax.legend(fontsize=8)
    save_figure(fig, out_dir / "resource_scaling")


def run(
    *,
    vivado: Path | None = None,
    skip_run: bool = False,
    timeout_s: float = 21600.0,
    only: str | None = None,
    export_only: bool = False,
) -> dict[str, Any]:
    root = outputs_dir(OUTPUT_NAME)
    repo = repo_root()
    cases = timing_clean_matrix()
    if only:
        cases = [c for c in cases if c.case_id == only]
        if not cases:
            raise ValueError(f"unknown case id {only!r}")

    version = None
    part = None
    discover_error = None
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
                    exe, staging_root() / "_discover_parts_timing_clean.tcl"
                )
                version = version or version2
                if parts:
                    part = choose_kintex7_part(parts)
                elif "K7_COUNT=0" in blob:
                    discover_error = "get_parts returned no Kintex-7 devices"
            except Exception as exc:  # noqa: BLE001
                discover_error = str(exc)
        elif exe is None:
            discover_error = "Vivado executable not found"
        if part is None:
            part = "xc7k160tffg676-2"

    stage_root = rtl_dir = xdc_path = None
    if not export_only:
        stage_root, rtl_dir, xdc_path = prepare_staging(repo)

    results: list[dict[str, Any]] = []
    for case in cases:
        case_dir = case_output_dir(root, case)
        case_dir.mkdir(parents=True, exist_ok=True)
        if not export_only:
            import shutil

            stage_case = stage_root / case.case_id
            stage_case.mkdir(parents=True, exist_ok=True)
            wrap_path = stage_case / "tdc_benchmark_wrap.sv"
            tcl_path = stage_case / "run.tcl"
            expected = expected_counts(case.channels, case.chains_per_channel, case.carry4_per_chain)
            wrap_path.write_text(
                generate_wrap_sv(
                    n_channels=case.channels,
                    n_chains=case.chains_per_channel,
                    n_carry4=case.carry4_per_chain,
                ),
                encoding="utf-8",
            )
            tcl_path.write_text(
                generate_case_tcl(
                    part=part or "PART_UNSELECTED",
                    rtl_dir=rtl_dir,
                    xdc_path=xdc_path,
                    wrap_path=wrap_path,
                    out_dir=stage_case,
                    do_impl=True,
                    n_carry4=case.carry4_per_chain,
                    expected_capture_ff=expected.capture_ff_min,
                    place_guide=case.channels == 1,
                    fast_impl=False,
                ),
                encoding="utf-8",
            )
            shutil.copy2(wrap_path, case_dir / "tdc_benchmark_wrap.sv")
            shutil.copy2(tcl_path, case_dir / "run.tcl")

        ran = exe is not None and part is not None and not skip_run and not export_only
        synth_ok = impl_ok = None
        returncode = None
        log_text = ""
        ran_this = False
        timed_out = False
        runner_status = None
        recon: dict[str, Any] | None = None

        if export_only or (ran and _baseline._case_already_complete(case, case_dir)):
            log_text = _baseline._read_text(case_dir / "vivado.log")
            returncode = 0
            timed_out = _baseline._prior_timeout_hint(case_dir) if export_only else False
        elif ran:
            ran_this = True
            log_path = stage_case / "vivado.log"
            returncode, log_text, timed_out = run_vivado_batch(
                exe, tcl_path, log_path, timeout_s=timeout_s
            )
        else:
            log_text = discover_error or "vivado not run"

        if ran_this:
            import shutil

            for name in _baseline.REPORT_FILES:
                src = stage_case / name
                if src.is_file():
                    shutil.copy2(src, case_dir / name)
            timing_paths = stage_case / "timing_paths.rpt"
            if timing_paths.is_file():
                shutil.copy2(timing_paths, case_dir / "timing_paths.rpt")

        if ran or export_only:
            recon = reconcile_runner_status(
                channels=case.channels,
                chains_per_channel=case.chains_per_channel,
                carry4_per_chain=case.carry4_per_chain,
                do_impl=True,
                case_dir=case_dir,
                timed_out=timed_out,
                returncode=returncode,
            )
            synth_ok = recon["synth_ok"]
            impl_ok = recon["impl_ok"]
            runner_status = recon["runner_status"]

        row = collect_case_result(
            case,
            case_dir,
            synth_ok=synth_ok,
            impl_ok=impl_ok,
            returncode=returncode,
            log_text=log_text,
        )
        row["benchmark_variant"] = "timing_clean"
        if runner_status and recon is not None:
            row["runner_status"] = runner_status
            row["synth_status"] = recon["synth_status"]
            row["impl_status"] = recon["impl_status"]
        loc_rows = parse_carry_locs(_baseline._read_text(case_dir / "carry_locs.txt"))
        _plot_placement(case_dir, loc_rows)
        _baseline.write_json(case_dir / "summary.json", row)
        results.append(row)

    results = _baseline._merge_existing_case_rows(root, results)
    _plot_resource_scaling(results, root)
    _plot_timing_scaling(results, root)

    summary = {
        "result_classification": CLASSIFICATION,
        "benchmark_variant": "timing_clean",
        "benchmark_clock_ns": BENCHMARK_CLOCK_NS,
        "vivado_version": version,
        "part": part,
        "carry4_per_chain": CARRY4_PER_CHAIN,
        "cases": results,
        "synth_ok": sum(1 for r in results if r["synth_status"] == "ok"),
        "impl_ok": sum(1 for r in results if r["impl_status"] == "ok"),
    }
    _baseline.write_json(root / "summary.json", summary)

    evidence_path = None
    if export_only or any(r.get("synth_status") == "ok" for r in results):
        assert_mapped_carry4_matches(results)
        assert_capture_ff_matches(results)
        evidence_path = write_timing_clean_evidence_snapshot(
            cases=results,
            vivado_version=version,
            part=part,
            outputs_root=root,
        )
        summary["evidence_snapshot"] = str(evidence_path.relative_to(repo))
        _baseline.write_json(root / "summary.json", summary)

    return {
        "output_dir": str(root),
        "evidence_dir": str(evidence_path) if evidence_path else None,
        "extra": summary,
        "vivado": str(exe) if exe else None,
        "part": part,
    }
