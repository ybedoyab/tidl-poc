"""Derive Vivado case status from reports, not from a lone subprocess returncode.

A Python timeout must not label a completed child as failed, and a leftover
report file is not success by itself.
"""

from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path
from typing import Any

from tidl_poc.vivado.counts import expected_counts
from tidl_poc.vivado.reports import parse_metrics_kv, parse_route_status, parse_utilization


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def terminate_process_tree(pid: int) -> None:
    """Kill pid and descendants. Prevents orphaned Vivado after a Python timeout."""
    if pid <= 0:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            check=False,
            capture_output=True,
            timeout=60,
        )
        return
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except OSError:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def mapped_carry4_from_dir(case_dir: Path) -> int | None:
    metrics = parse_metrics_kv(_read(case_dir / "metrics.txt"))
    raw = metrics.get("TIDL_CARRY4_COUNT")
    if raw is not None:
        try:
            return int(raw)
        except ValueError:
            pass
    util = parse_utilization(_read(case_dir / "utilization_impl.rpt")) or parse_utilization(
        _read(case_dir / "utilization_synth.rpt")
    )
    value = util.get("carry4")
    return int(value) if value is not None else None


def reports_confirm_synth(case_dir: Path, expected_carry4: int) -> bool:
    if not (case_dir / "utilization_synth.rpt").is_file():
        return False
    metrics = parse_metrics_kv(_read(case_dir / "metrics.txt"))
    if metrics.get("TIDL_SYNTH_STATUS") != "ok":
        return False
    mapped = mapped_carry4_from_dir(case_dir)
    return mapped == expected_carry4


def reports_confirm_impl(case_dir: Path, expected_carry4: int) -> bool:
    if not (case_dir / "utilization_impl.rpt").is_file():
        return False
    if not (case_dir / "timing_summary.rpt").is_file():
        return False
    if not (case_dir / "route_status.rpt").is_file():
        return False
    metrics = parse_metrics_kv(_read(case_dir / "metrics.txt"))
    if metrics.get("TIDL_IMPL_STATUS") != "ok":
        return False
    if not reports_confirm_synth(case_dir, expected_carry4):
        return False
    route = parse_route_status(_read(case_dir / "route_status.rpt"))
    return bool(route.get("fully_routed"))


def reconcile_runner_status(
    *,
    channels: int,
    chains_per_channel: int,
    carry4_per_chain: int,
    do_impl: bool,
    case_dir: Path,
    timed_out: bool,
    returncode: int | None,
) -> dict[str, Any]:
    """Combine subprocess outcome with validated report markers."""
    expected = expected_counts(channels, chains_per_channel, carry4_per_chain).carry4
    synth_valid = reports_confirm_synth(case_dir, expected)
    impl_valid = reports_confirm_impl(case_dir, expected) if do_impl else None

    if timed_out:
        if synth_valid and (not do_impl or impl_valid):
            return {
                "runner_status": "recovered_after_timeout",
                "synth_status": "ok",
                "impl_status": "ok" if do_impl else "skipped",
                "synth_ok": True,
                "impl_ok": True if do_impl else None,
            }
        return {
            "runner_status": "timeout",
            "synth_status": "ok" if synth_valid else "timeout",
            "impl_status": ("ok" if impl_valid else "timeout") if do_impl else "skipped",
            "synth_ok": synth_valid,
            "impl_ok": False if do_impl else None,
        }

    if returncode == 0 and synth_valid and (not do_impl or impl_valid):
        return {
            "runner_status": "succeeded",
            "synth_status": "ok",
            "impl_status": "ok" if do_impl else "skipped",
            "synth_ok": True,
            "impl_ok": True if do_impl else None,
        }

    return {
        "runner_status": "failed",
        "synth_status": "ok" if synth_valid else "failed",
        "impl_status": ("ok" if impl_valid else "failed") if do_impl else "skipped",
        "synth_ok": synth_valid,
        "impl_ok": impl_valid if do_impl else None,
    }
