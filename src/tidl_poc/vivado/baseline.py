"""Kintex-7 structural TDC Vivado baseline (RTL/synthesis/implementation evidence)."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tidl_poc import RTL_DISCLAIMER, RTL_RESULT_CLASSIFICATION
from tidl_poc.common.metadata import write_json, write_metadata
from tidl_poc.common.paths import outputs_dir, repo_root
from tidl_poc.common.plotting import save_figure
from tidl_poc.vivado.counts import expected_counts
from tidl_poc.vivado.discover import (
    choose_kintex7_part,
    find_vivado,
    part_is_synthesis_target_only,
    query_installed_kintex7_parts,
    query_vivado_version,
)
from tidl_poc.vivado.reports import (
    parse_carry_locs,
    parse_drc_methodology,
    parse_impl_failure,
    parse_metrics_kv,
    parse_route_status,
    parse_timing_summary,
    parse_utilization,
    placement_scatter_metrics,
)
from tidl_poc.vivado.evidence import assert_mapped_carry4_matches, write_evidence_snapshot
from tidl_poc.vivado.status import reconcile_runner_status, terminate_process_tree
from tidl_poc.vivado.tcl import generate_case_tcl, generate_wrap_sv

CHANNELS = (1, 4, 8, 16)
CHAINS_PER_CHANNEL = 8
CARRY4_LENGTHS = (32, 48, 64)
BENCHMARK_CLOCK_NS = 4.0

CLASSIFICATION = RTL_RESULT_CLASSIFICATION


@dataclass(frozen=True)
class BenchmarkCase:
    channels: int
    chains_per_channel: int
    carry4_per_chain: int
    do_impl: bool

    @property
    def case_id(self) -> str:
        return f"ch{self.channels:02d}_nch{self.chains_per_channel:02d}_c4_{self.carry4_per_chain:02d}"


def primary_matrix(*, impl_all: bool = False) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    for n_ch in CHANNELS:
        for n_c4 in CARRY4_LENGTHS:
            do_impl = impl_all or _default_impl(n_ch, n_c4)
            cases.append(
                BenchmarkCase(
                    channels=n_ch,
                    chains_per_channel=CHAINS_PER_CHANNEL,
                    carry4_per_chain=n_c4,
                    do_impl=do_impl,
                )
            )
    return cases


def _default_impl(n_ch: int, n_c4: int) -> bool:
    # Synth all 12. Full P&R: 1/4/8/16 x 64, plus 1-channel for each length.
    if n_ch in {1, 4, 8, 16} and n_c4 == 64:
        return True
    if n_ch == 1 and n_c4 in CARRY4_LENGTHS:
        return True
    return False


def case_output_dir(root: Path, case: BenchmarkCase) -> Path:
    return root / case.case_id


def _prior_timeout_hint(case_dir: Path) -> bool:
    path = case_dir / "summary.json"
    if not path.is_file():
        return False
    try:
        prior = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if prior.get("returncode") == -1:
        return True
    return prior.get("runner_status") in {"timeout", "recovered_after_timeout"}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _case_already_complete(case: BenchmarkCase, case_dir: Path) -> bool:
    if not (case_dir / "metrics.txt").is_file():
        return False
    if not (case_dir / "utilization_synth.rpt").is_file():
        return False
    metrics = parse_metrics_kv(_read_text(case_dir / "metrics.txt"))
    if metrics.get("TIDL_SYNTH_STATUS") != "ok":
        return False
    if case.do_impl:
        if metrics.get("TIDL_IMPL_STATUS") != "ok":
            return False
        return (case_dir / "utilization_impl.rpt").is_file()
    return True


def staging_root() -> Path:
    """Vivado rejects commas in some file arguments; keep the run off the repo path."""
    return Path(tempfile.gettempdir()) / "tidl_poc_vivado"


def prepare_staging(repo: Path) -> tuple[Path, Path, Path]:
    root = staging_root()
    rtl_dst = root / "rtl"
    rtl_dst.mkdir(parents=True, exist_ok=True)
    rtl_src = repo / "rtl" / "tdc" / "kintex7"
    for name in (
        "carry4_tdl_chain.sv",
        "tdc_capture_bank.sv",
        "multi_chain_tdc_structural.sv",
        "tdc_benchmark_top.sv",
    ):
        shutil.copy2(rtl_src / name, rtl_dst / name)
    xdc_dst = root / "tdc_benchmark_ooc.xdc"
    shutil.copy2(repo / "constraints" / "kintex7" / "tdc_benchmark_ooc.xdc", xdc_dst)
    return root, rtl_dst, xdc_dst


REPORT_FILES = (
    "utilization_synth.rpt",
    "utilization_hier_synth.rpt",
    "utilization_impl.rpt",
    "timing_summary.rpt",
    "methodology.rpt",
    "drc_synth.rpt",
    "drc_impl.rpt",
    "route_status.rpt",
    "clock_utilization.rpt",
    "carry_locs.txt",
    "metrics.txt",
    "vivado.log",
    "vivado.jou",
    "tdc_benchmark_wrap.sv",
    "run.tcl",
)


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def collect_case_result(
    case: BenchmarkCase,
    out_dir: Path,
    *,
    synth_ok: bool | None,
    impl_ok: bool | None,
    returncode: int | None,
    log_text: str,
) -> dict[str, Any]:
    expected = expected_counts(case.channels, case.chains_per_channel, case.carry4_per_chain)
    metrics = parse_metrics_kv(_read_text(out_dir / "metrics.txt") + "\n" + log_text)
    util_synth = parse_utilization(_read_text(out_dir / "utilization_synth.rpt"))
    util_impl = parse_utilization(_read_text(out_dir / "utilization_impl.rpt"))
    util = util_impl or util_synth
    timing = parse_timing_summary(_read_text(out_dir / "timing_summary.rpt"))
    route = parse_route_status(_read_text(out_dir / "route_status.rpt"))
    drc = parse_drc_methodology(_read_text(out_dir / "drc_impl.rpt") or _read_text(out_dir / "drc_synth.rpt"))
    meth = parse_drc_methodology(_read_text(out_dir / "methodology.rpt"))
    fail = parse_impl_failure(log_text)
    loc_rows = parse_carry_locs(_read_text(out_dir / "carry_locs.txt"))
    scatter = placement_scatter_metrics(loc_rows) if loc_rows else {}

    mapped_carry4 = None
    if "TIDL_CARRY4_COUNT" in metrics:
        try:
            mapped_carry4 = int(metrics["TIDL_CARRY4_COUNT"])
        except ValueError:
            mapped_carry4 = None
    if mapped_carry4 is None:
        mapped_carry4 = util.get("carry4")

    mapped_fdre = None
    if "TIDL_FDRE_COUNT" in metrics:
        try:
            mapped_fdre = int(metrics["TIDL_FDRE_COUNT"])
        except ValueError:
            mapped_fdre = None
    if mapped_fdre is None:
        mapped_fdre = util.get("fdre") or util.get("slice_registers")

    if synth_ok is None:
        synth_ok = metrics.get("TIDL_SYNTH_STATUS") == "ok"
    impl_status = metrics.get("TIDL_IMPL_STATUS")
    if impl_ok is None:
        if not case.do_impl:
            impl_ok = None
        else:
            impl_ok = impl_status == "ok"

    optimized_away = expected.optimized_away(mapped_carry4)
    capture_ff_ok = (
        mapped_fdre is not None and int(mapped_fdre) >= expected.capture_ff_min
    )
    return {
        "case_id": case.case_id,
        "channels": case.channels,
        "chains_per_channel": case.chains_per_channel,
        "carry4_per_chain": case.carry4_per_chain,
        "expected_carry4": expected.carry4,
        "expected_taps": expected.taps,
        "expected_capture_ff_min": expected.capture_ff_min,
        "mapped_carry4": mapped_carry4,
        "mapped_fdre": mapped_fdre,
        "capture_ff_ok": capture_ff_ok,
        "carry4_optimized_away": optimized_away,
        "slice_luts": util.get("slice_luts"),
        "slice_registers": util.get("slice_registers"),
        "slices": util.get("slices"),
        "slice_luts_pct": util.get("slice_luts_pct"),
        "slice_registers_pct": util.get("slice_registers_pct"),
        "slices_pct": util.get("slices_pct"),
        "utilization_source": "impl" if util_impl else ("synth" if util_synth else None),
        "synth_status": "ok" if synth_ok else "failed",
        "impl_requested": case.do_impl,
        "impl_status": impl_status or ("skipped" if not case.do_impl else ("ok" if impl_ok else "failed")),
        "impl_ok": impl_ok,
        "returncode": returncode,
        "wns_ns": timing.get("wns_ns"),
        "tns_ns": timing.get("tns_ns"),
        "control_timing_closed": timing.get("timing_closed"),
        "route_status": route.get("route_status"),
        "fully_routed": route.get("fully_routed"),
        "drc_warnings": drc.get("warnings"),
        "methodology_warnings": meth.get("warnings"),
        "methodology_carry_notes": meth.get("carry_or_async_notes"),
        "placement": scatter,
        "failure": fail if fail.get("failed") else None,
        "classification": CLASSIFICATION,
        "runner_status": None,
    }


def run_vivado_batch(
    vivado: Path,
    tcl_path: Path,
    log_path: Path,
    *,
    timeout_s: float,
) -> tuple[int, str, bool]:
    """Run Vivado batch. On timeout, kill the process tree (no orphaned jobs).

    Returns (returncode, combined_log, timed_out).
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    journal = log_path.with_suffix(".jou")
    popen_kw: dict[str, Any] = {
        "args": [
            str(vivado),
            "-mode",
            "batch",
            "-source",
            str(tcl_path),
            "-log",
            str(log_path),
            "-journal",
            str(journal),
        ],
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "cwd": str(tcl_path.parent),
    }
    if os.name != "nt":
        popen_kw["start_new_session"] = True
    proc = subprocess.Popen(**popen_kw)
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        terminate_process_tree(proc.pid)
        try:
            stdout, stderr = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            stdout, stderr = "", ""
        blob = "TIMEOUT\n" + (stdout or "") + "\n" + (stderr or "")
        if log_path.is_file():
            blob += "\n" + _read_text(log_path)
        return -1, blob, True
    blob = (stdout or "") + "\n" + (stderr or "")
    if log_path.is_file():
        blob += "\n" + _read_text(log_path)
    return int(proc.returncode if proc.returncode is not None else -1), blob, False


def _merge_existing_case_rows(root: Path, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep prior case summaries when this invocation ran a subset (`--only`)."""
    by_id: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("ch*_nch*_c4_*/summary.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cid = row.get("case_id")
        if isinstance(cid, str) and cid:
            by_id[cid] = row
    for row in results:
        cid = row.get("case_id")
        if isinstance(cid, str) and cid:
            by_id[cid] = row
    merged = list(by_id.values())
    merged.sort(key=lambda r: (int(r.get("channels") or 0), int(r.get("carry4_per_chain") or 0)))
    return merged


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _plot_scaling(rows: list[dict[str, Any]], out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    impl_or_synth = [r for r in rows if r.get("slice_luts") is not None or r.get("mapped_carry4") is not None]
    if not impl_or_synth:
        return

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
    for n_c4 in CARRY4_LENGTHS:
        subset = [r for r in impl_or_synth if r["carry4_per_chain"] == n_c4]
        if not subset:
            continue
        subset = sorted(subset, key=lambda r: r["channels"])
        xs = [r["channels"] for r in subset]
        axes[0].plot(xs, [r.get("slices") or 0 for r in subset], marker="o", label=f"{n_c4} CARRY4/chain slices")
        axes[0].plot(xs, [r.get("slice_luts") or 0 for r in subset], marker="s", label=f"{n_c4} LUT")
        axes[0].plot(xs, [r.get("slice_registers") or r.get("mapped_fdre") or 0 for r in subset], marker="^", label=f"{n_c4} FF")
        axes[0].plot(xs, [r.get("mapped_carry4") or 0 for r in subset], marker="d", label=f"{n_c4} CARRY4")
        axes[1].plot(xs, [r.get("slices_pct") or 0 for r in subset], marker="o", label=f"{n_c4} slice %")
        axes[1].plot(xs, [r.get("slice_luts_pct") or 0 for r in subset], marker="s", label=f"{n_c4} LUT %")
    axes[0].set_xlabel("channels")
    axes[0].set_ylabel("count")
    axes[0].set_title("Resources vs channels (actual Vivado cases)")
    axes[0].legend(fontsize=7, ncol=2)
    axes[1].set_xlabel("channels")
    axes[1].set_ylabel("utilization %")
    axes[1].set_title("Utilization vs channels (actual Vivado cases)")
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    save_figure(fig, out_dir / "resource_scaling")

    fig2, ax = plt.subplots()
    width = 0.22
    chans = sorted({r["channels"] for r in impl_or_synth})
    for i, n_c4 in enumerate(CARRY4_LENGTHS):
        ys = []
        for ch in chans:
            match = [r for r in impl_or_synth if r["channels"] == ch and r["carry4_per_chain"] == n_c4]
            ys.append((match[0].get("mapped_carry4") or 0) if match else 0)
        ax.bar([c + (i - 1) * width for c in chans], ys, width=width, label=f"{n_c4} CARRY4/chain")
    ax.set_xlabel("channels")
    ax.set_ylabel("mapped CARRY4")
    ax.set_title("CARRY4 vs channels and TDL length (actual cases)")
    ax.legend()
    save_figure(fig2, out_dir / "carry4_length_effect")


def _plot_placement(case_dir: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    from collections import defaultdict

    import matplotlib.pyplot as plt

    groups: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("x") is None or row.get("y") is None:
            continue
        groups[(row.get("channel"), row.get("chain"))].append(row)
    if not groups:
        return
    fig, ax = plt.subplots(figsize=(6.4, 7.4))
    cmap = plt.cm.tab10
    for i, (key, members) in enumerate(sorted(groups.items(), key=lambda kv: kv[0])):
        members = sorted(members, key=lambda m: m.get("carry_index") or 0)
        xs = [m["x"] for m in members]
        ys = [m["y"] for m in members]
        color = cmap(i % 10)
        ax.plot(xs, ys, "-", color=color, alpha=0.45, lw=1.1)
        label = f"ch{key[0]} chain {key[1]}"
        ax.scatter(xs, ys, s=14, color=color, zorder=3, label=label)
    ax.set_xlabel("SLICE_X")
    ax.set_ylabel("SLICE_Y")
    ax.set_title("CARRY4 placement from Vivado LOC text (not a GUI screenshot)")
    if len(groups) <= 12:
        ax.legend(fontsize=7, ncol=2, loc="best", framealpha=0.9)
    ax.set_aspect("equal", adjustable="box")
    save_figure(fig, case_dir / "carry4_placement")


def _interpretation(summary: dict[str, Any]) -> str:
    cases = summary.get("cases", [])
    lines = [
        "# Kintex-7 structural TDC Vivado baseline",
        "",
        f"**Classification:** {CLASSIFICATION}.",
        "Not a physical measurement. Not TDC bin widths. Not 1 ps resolution. Not DNL/SSP/accuracy.",
        "",
        f"Vivado {summary.get('vivado_version')}  part `{summary.get('part')}`.",
        f"Git commit `{summary.get('git_commit')}`.",
        "",
        "False paths (narrow): asynchronous `hit[*]` event inputs and `rst_n` into FDRE.R.",
        "The 4 ns `clk` constraint times capture/control logic only. WNS is not TDL picosecond accuracy.",
        "",
        "## Cases that reached implementation",
        "",
    ]
    impl_ok = [c for c in cases if c.get("impl_status") == "ok"]
    impl_fail = [c for c in cases if c.get("impl_requested") and c.get("impl_status") == "failed"]
    impl_skip = [c for c in cases if c.get("impl_status") in {"skipped", "not_run"} or not c.get("impl_requested")]
    synth_ok = [c for c in cases if c.get("synth_status") == "ok"]
    synth_fail = [c for c in cases if c.get("synth_status") == "failed"]
    synth_skip = [c for c in cases if c.get("synth_status") in {"skipped", "not_run"}]
    recovered = [c for c in cases if c.get("runner_status") == "recovered_after_timeout"]
    lines.append(f"- synthesis succeeded: {len(synth_ok)} / failed: {len(synth_fail)} / skipped: {len(synth_skip)}")
    lines.append(
        f"- implementation succeeded: {len(impl_ok)} / failed: {len(impl_fail)} / skipped: {len(impl_skip)}"
    )
    if recovered:
        lines.append(
            "- runner status recovered_after_timeout: "
            + ", ".join(c["case_id"] for c in recovered)
            + " (Python timeout while Vivado later completed valid reports)."
        )
    lines.append("")
    unmet = [c["case_id"] for c in cases if isinstance(c.get("wns_ns"), (int, float)) and c["wns_ns"] < 0]
    if unmet:
        lines.extend(
            [
                "Control-clock WNS was negative for: " + ", ".join(unmet) + ".",
                "That is capture/control timing against the 4 ns benchmark only. It is not TDL accuracy.",
                "",
            ]
        )
    lines.append("| case | synth | impl | CARRY4 mapped/expected | FF | slices | LUT | WNS ns | route |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for c in cases:
        lines.append(
            "| {case_id} | {synth_status} | {impl_status} | {mapped_carry4}/{expected_carry4} | {mapped_fdre} | {slices} | {slice_luts} | {wns_ns} | {route_status} |".format(
                **{k: c.get(k) for k in (
                    "case_id",
                    "synth_status",
                    "impl_status",
                    "mapped_carry4",
                    "expected_carry4",
                    "mapped_fdre",
                    "slices",
                    "slice_luts",
                    "wns_ns",
                    "route_status",
                )}
            )
        )
    lines.extend(
        [
            "",
            "16 channels × 8 chains × 64 CARRY4 structurally fit and fully routed on XC7K160T.",
            "That lowers implementation-capacity risk. It is not metrological performance.",
            "Do not choose multichain vs MSWU-B from these reports.",
            "",
            RTL_DISCLAIMER,
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def run(
    *,
    vivado: Path | None = None,
    seed: int = 42,
    impl_all: bool = False,
    skip_run: bool = False,
    timeout_s: float = 21600.0,
    only: str | None = None,
    export_only: bool = False,
) -> dict[str, Any]:
    root = outputs_dir("vivado_kintex7")
    repo = repo_root()
    cases = primary_matrix(impl_all=impl_all)
    if only:
        cases = [c for c in cases if c.case_id == only]
        if not cases:
            raise ValueError(f"unknown case id {only!r}")

    exe = None
    version = None
    parts: list[str] = []
    part = None
    discover_error = None
    prior_root = _load_json(root / "summary.json")
    if export_only:
        version = prior_root.get("vivado_version") or "2026.1"
        part = prior_root.get("part") or "xc7k160tffg676-2"
    else:
        exe = find_vivado(vivado)
        if exe is not None and not skip_run:
            version = query_vivado_version(exe)
            try:
                staging_root().mkdir(parents=True, exist_ok=True)
                version2, parts, blob = query_installed_kintex7_parts(
                    exe, staging_root() / "_discover_parts.tcl"
                )
                version = version or version2
                if parts:
                    part = choose_kintex7_part(parts)
                elif "K7_COUNT=0" in blob:
                    discover_error = "get_parts returned no Kintex-7 devices"
            except Exception as exc:  # noqa: BLE001 — keep runner going; still emit RTL/docs outputs
                discover_error = str(exc)
        elif exe is None:
            discover_error = "Vivado executable not found"

        if part is None and parts:
            part = choose_kintex7_part(parts)

        local_paths = {
            "vivado": str(exe) if exe else None,
            "staging_root": str(staging_root()),
            "note": "Machine-specific. Gitignored via outputs/. Do not copy into tracked docs.",
        }
        write_json(root / "local_paths.json", local_paths)

    stage_root = rtl_dir = xdc_path = None
    if not export_only:
        stage_root, rtl_dir, xdc_path = prepare_staging(repo)

    results: list[dict[str, Any]] = []
    for case in cases:
        case_dir = case_output_dir(root, case)
        case_dir.mkdir(parents=True, exist_ok=True)
        if not export_only:
            stage_case = stage_root / case.case_id
            stage_case.mkdir(parents=True, exist_ok=True)
            wrap_path = stage_case / "tdc_benchmark_wrap.sv"
            tcl_path = stage_case / "run.tcl"
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
                    do_impl=case.do_impl,
                    n_carry4=case.carry4_per_chain,
                    expected_capture_ff=expected_counts(
                        case.channels, case.chains_per_channel, case.carry4_per_chain
                    ).capture_ff_min,
                    place_guide=case.do_impl and case.channels == 1,
                    fast_impl=case.do_impl and case.channels >= 8,
                ),
                encoding="utf-8",
            )
            shutil.copy2(wrap_path, case_dir / "tdc_benchmark_wrap.sv")
            shutil.copy2(tcl_path, case_dir / "run.tcl")

        ran = exe is not None and part is not None and not skip_run and not export_only
        synth_ok = None
        impl_ok = None
        returncode = None
        log_text = ""
        ran_this = False
        timed_out = False
        runner_status = None
        recon: dict[str, Any] | None = None
        if export_only or (ran and _case_already_complete(case, case_dir)):
            log_text = _read_text(case_dir / "vivado.log")
            returncode = 0
            timed_out = _prior_timeout_hint(case_dir) if export_only else False
        elif ran:
            ran_this = True
            log_path = stage_case / "vivado.log"
            returncode, log_text, timed_out = run_vivado_batch(
                exe, tcl_path, log_path, timeout_s=timeout_s
            )
        else:
            log_text = discover_error or "vivado not run"

        if ran_this:
            for name in REPORT_FILES:
                src = stage_case / name
                if src.is_file():
                    shutil.copy2(src, case_dir / name)

        if ran or export_only:
            recon = reconcile_runner_status(
                channels=case.channels,
                chains_per_channel=case.chains_per_channel,
                carry4_per_chain=case.carry4_per_chain,
                do_impl=case.do_impl,
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
        if runner_status and recon is not None:
            row["runner_status"] = runner_status
            row["synth_status"] = recon["synth_status"]
            row["impl_status"] = recon["impl_status"]
        if not ran and not export_only:
            row["synth_status"] = "not_run"
            if case.do_impl:
                row["impl_status"] = "not_run"
        loc_rows = parse_carry_locs(_read_text(case_dir / "carry_locs.txt"))
        _plot_placement(case_dir, loc_rows)
        write_json(case_dir / "summary.json", row)
        results.append(row)

    results = _merge_existing_case_rows(root, results)

    resource_fields = [
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
    ]
    impl_fields = resource_fields + [
        "impl_requested",
        "wns_ns",
        "tns_ns",
        "control_timing_closed",
        "route_status",
        "fully_routed",
        "drc_warnings",
        "methodology_warnings",
    ]
    _write_csv(root / "resource_scaling.csv", results, resource_fields)
    _write_csv(root / "implementation_summary.csv", results, impl_fields)
    _plot_scaling(results, root)

    from tidl_poc.common.metadata import git_commit

    summary = {
        "result_classification": CLASSIFICATION,
        "vivado_version": version,
        "part": part,
        "part_synthesis_target_only": part_is_synthesis_target_only(part) if part else None,
        "kwiatkowski_xc7k160_comparability": bool(part) and not part_is_synthesis_target_only(part),
        "git_commit": git_commit(),
        "chains_per_channel": CHAINS_PER_CHANNEL,
        "carry4_lengths_swept": list(CARRY4_LENGTHS),
        "benchmark_clock_ns": BENCHMARK_CLOCK_NS,
        "bitstream_generated": False,
        "board_pins_assigned": False,
        "vivado_found": exe is not None,
        "discover_error": discover_error,
        "synth_ok": sum(1 for r in results if r["synth_status"] == "ok"),
        "synth_failed": sum(1 for r in results if r["synth_status"] == "failed"),
        "synth_skipped": sum(1 for r in results if r["synth_status"] in {"skipped", "not_run"}),
        "impl_ok": sum(1 for r in results if r["impl_status"] == "ok"),
        "impl_failed": sum(1 for r in results if r["impl_requested"] and r["impl_status"] == "failed"),
        "impl_skipped": sum(1 for r in results if r["impl_status"] in {"skipped", "not_run"} or not r["impl_requested"]),
        "recovered_after_timeout": sum(1 for r in results if r.get("runner_status") == "recovered_after_timeout"),
        "cases": results,
        "false_paths": [
            "hit[*] asynchronous event inputs",
            "rst_n into FDRE.R",
        ],
        "disclaimer": RTL_DISCLAIMER,
    }
    write_json(root / "summary.json", summary)
    write_metadata(
        root / "metadata.json",
        script_name="run_kintex7_baseline.py",
        random_seed=seed,
        input_parameters={
            "channels": list(CHANNELS),
            "chains_per_channel": CHAINS_PER_CHANNEL,
            "carry4_per_chain": list(CARRY4_LENGTHS),
            "part": part,
            "vivado_version": version,
            "impl_policy": "all_synth; impl 1/4/8/16ch x 64 plus 1ch x 32/48/64" if not impl_all else "all_impl",
            "bitstream": False,
        },
        extra={
            "classification": CLASSIFICATION,
            "vivado_path_recorded_in": "local_paths.json",
            "physical_measurement": False,
        },
        result_classification=CLASSIFICATION,
        disclaimer=RTL_DISCLAIMER,
    )
    (root / "interpretation.md").write_text(_interpretation(summary), encoding="utf-8")
    evidence_path = None
    if export_only or any(r.get("synth_status") == "ok" for r in results):
        assert_mapped_carry4_matches(results)
        evidence_path = write_evidence_snapshot(
            cases=results,
            vivado_version=version,
            part=part,
            outputs_root=root,
        )
        try:
            summary["evidence_snapshot"] = str(evidence_path.relative_to(repo))
        except ValueError:
            summary["evidence_snapshot"] = str(evidence_path)
        write_json(root / "summary.json", summary)
    return {
        "output_dir": str(root),
        "evidence_dir": str(evidence_path) if evidence_path else None,
        "extra": summary,
        "vivado": str(exe) if exe else None,
        "part": part,
    }


def compact_resource_line(summary: dict[str, Any], channels: int, carry4: int = 64) -> str:
    for case in summary.get("cases", []):
        if case.get("channels") == channels and case.get("carry4_per_chain") == carry4:
            return (
                f"{channels}ch: CARRY4 {case.get('mapped_carry4')}/{case.get('expected_carry4')} "
                f"LUT {case.get('slice_luts')} FF {case.get('mapped_fdre')} "
                f"slices {case.get('slices')} impl {case.get('impl_status')}"
            )
    return f"{channels}ch x {carry4}: no case"
