"""Parse Vivado text reports. Not physical TDC measurements."""

from __future__ import annotations

import re
from typing import Any

_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _int_cell(text: str) -> int | None:
    cleaned = text.replace(",", "").strip()
    if not cleaned or cleaned in {".", "-"}:
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def _float_cell(text: str) -> float | None:
    cleaned = text.replace(",", "").strip()
    if not cleaned or cleaned in {".", "-"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_utilization(text: str) -> dict[str, Any]:
    """Extract LUT/FF/slice/CARRY4/FDRE used counts from a utilization report."""
    result: dict[str, Any] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 2:
            continue
        name = cols[0]
        used = _int_cell(cols[1])
        if used is None:
            continue
        available = None
        pct = None
        if len(cols) >= 6:
            available = _int_cell(cols[4])
            pct = _float_cell(cols[5])
        elif len(cols) == 5:
            available = _int_cell(cols[3])
            pct = _float_cell(cols[4])
        elif len(cols) == 4:
            available = _int_cell(cols[2])
            pct = _float_cell(cols[3])
        key = name.lower().rstrip("*").strip()
        if name.upper().rstrip("*").strip() == "CARRY4" or key == "carry4":
            result["carry4"] = used
        elif name.upper().rstrip("*").strip() == "FDRE" or key == "fdre":
            result["fdre"] = used
        elif key in {"slice luts", "slice lut"}:
            result["slice_luts"] = used
            if available:
                result["slice_luts_available"] = available
            if pct is not None:
                result["slice_luts_pct"] = pct
        elif key == "slice registers":
            result["slice_registers"] = used
            if available:
                result["slice_registers_available"] = available
            if pct is not None:
                result["slice_registers_pct"] = pct
        elif key == "slice" and "logic" not in key:
            result["slices"] = used
            if available:
                result["slices_available"] = available
            if pct is not None:
                result["slices_pct"] = pct
        elif key.startswith("register as flip flop"):
            result["flip_flops"] = used
    return result


def parse_timing_summary(text: str) -> dict[str, Any]:
    """Parse WNS/TNS and whether constraints met. Not TDL bin accuracy."""
    result: dict[str, Any] = {
        "wns_ns": None,
        "tns_ns": None,
        "constraints_met": None,
        "timing_closed": None,
    }
    lower = text.lower()
    if "timing constraints are not met" in lower:
        result["constraints_met"] = False
        result["timing_closed"] = False
    elif "all user specified timing constraints are met" in lower:
        result["constraints_met"] = True
        result["timing_closed"] = True

    wns = re.search(r"Worst Negative Slack\s*\(WNS\):\s*([-+]?\d+\.?\d*)\s*ns", text, re.I)
    tns = re.search(r"Total Negative Slack\s*\(TNS\):\s*([-+]?\d+\.?\d*)\s*ns", text, re.I)
    if wns:
        result["wns_ns"] = float(wns.group(1))
    if tns:
        result["tns_ns"] = float(tns.group(1))

    # Design Timing Summary table: WNS(ns) header then a data row.
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "WNS(ns)" in line.replace(" ", "") or re.search(r"\bWNS\(ns\)", line):
            for follow in lines[i + 1 : i + 8]:
                nums = _NUM.findall(follow)
                if len(nums) >= 2:
                    try:
                        result["wns_ns"] = float(nums[0])
                        result["tns_ns"] = float(nums[1])
                    except ValueError:
                        continue
                    break
            break

    if result["wns_ns"] is not None and result["timing_closed"] is None:
        result["timing_closed"] = result["wns_ns"] >= 0.0
        result["constraints_met"] = result["timing_closed"]
    return result


def parse_route_status(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {"fully_routed": None, "route_status": "unknown"}
    err = re.search(r"nets with routing errors[^\d]*(\d+)", text, re.I)
    fully = re.search(r"fully routed nets[^\d]*(\d+)", text, re.I)
    routable = re.search(r"routable nets[^\d]*(\d+)", text, re.I)
    if err:
        n_err = int(err.group(1))
        result["fully_routed"] = n_err == 0
        result["route_status"] = "fully_routed" if n_err == 0 else "errors"
        return result
    if fully and routable:
        n_full = int(fully.group(1))
        n_r = int(routable.group(1))
        result["fully_routed"] = n_full == n_r
        result["route_status"] = "fully_routed" if n_full == n_r else "partial"
        return result
    lower = text.lower()
    if "fully routed" in lower:
        result["fully_routed"] = True
        result["route_status"] = "fully_routed"
    return result


def parse_drc_methodology(text: str) -> dict[str, Any]:
    """Count criticals/errors/warnings. Keep carry/async methodology notes."""
    result: dict[str, Any] = {
        "critical": 0,
        "errors": 0,
        "warnings": 0,
        "advisory": 0,
        "carry_or_async_notes": [],
    }
    for key, pat in (
        ("critical", r"Critical\s*:\s*(\d+)"),
        ("errors", r"Error(?:s)?\s*:\s*(\d+)"),
        ("warnings", r"Warning(?:s)?\s*:\s*(\d+)"),
        ("advisory", r"Advisory\s*:\s*(\d+)"),
    ):
        match = re.search(pat, text, re.I)
        if match:
            result[key] = int(match.group(1))
    notes: list[str] = []
    for line in text.splitlines():
        low = line.lower()
        if any(tok in low for tok in ("carry", "asynch", "false path", "latch", "combinational loop")):
            stripped = line.strip()
            if stripped and stripped not in notes:
                notes.append(stripped)
    result["carry_or_async_notes"] = notes[:40]
    return result


def parse_metrics_kv(text: str) -> dict[str, str]:
    metrics: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("TIDL_") and "=" in line:
            key, val = line.split("=", 1)
            metrics[key.strip()] = val.strip()
    return metrics


def parse_impl_failure(text: str) -> dict[str, Any]:
    lower = text.lower()
    failed = False
    stage = None
    for name in ("synth_design", "opt_design", "place_design", "route_design"):
        if re.search(rf"(command failed:\s*{name}|{name} failed)", lower):
            failed = True
            stage = name
            break
    if "implementation failed" in lower or "synth_design failed" in lower:
        failed = True
        if stage is None:
            stage = "implementation" if "implementation failed" in lower else "synth_design"
    errors = [ln.strip() for ln in text.splitlines() if "ERROR:" in ln][:20]
    return {"failed": failed, "stage": stage, "errors": errors}


def parse_carry_locs(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # cell loc bel   OR csv cell,loc,x,y
        if "," in line:
            parts = [p.strip() for p in line.split(",")]
            if parts[0].lower() == "cell":
                continue
            cell = parts[0]
            loc = parts[1] if len(parts) > 1 else ""
        else:
            bits = line.split()
            if len(bits) < 2:
                continue
            cell, loc = bits[0], bits[1]
        match = re.search(r"SLICE_X(\d+)Y(\d+)", loc)
        chain = None
        ch_m = re.search(r"gen_chain\[(\d+)\]", cell)
        chn_m = re.search(r"gen_ch\[(\d+)\]", cell)
        fe_m = re.search(r"gen_fe\[(\d+)\]", cell)
        carry_m = re.search(r"gen_carry\[(\d+)\]", cell)
        tdl_m = re.search(r"(.+?/u_chain)/gen_carry\[", cell)
        rows.append(
            {
                "cell": cell,
                "loc": loc,
                "x": int(match.group(1)) if match else None,
                "y": int(match.group(2)) if match else None,
                "channel": (
                    int(chn_m.group(1))
                    if chn_m
                    else (int(fe_m.group(1)) if fe_m else None)
                ),
                "chain": int(ch_m.group(1)) if ch_m else None,
                "carry_index": int(carry_m.group(1)) if carry_m else None,
                "tdl_path": tdl_m.group(1) if tdl_m else None,
            }
        )
    return rows


def _chain_group_key(row: dict[str, Any]) -> tuple[Any, ...] | None:
    if row.get("x") is None or row.get("carry_index") is None:
        return None
    if row.get("chain") is not None:
        return (row.get("channel"), row.get("chain"))
    if row.get("tdl_path") is not None:
        return (row.get("channel"), row.get("tdl_path"))
    if row.get("channel") is not None:
        return (row.get("channel"), "mswu_tdl")
    return ("mswu_tdl", row.get("cell", "").split("/gen_carry")[0])


def placement_scatter_metrics(
    rows: list[dict[str, Any]], *, expected_chains: int | None = None
) -> dict[str, Any]:
    """Group CARRY4 cells into chains; count vertical vs scattered placement."""
    from collections import defaultdict

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    unmatched = 0
    for row in rows:
        key = _chain_group_key(row)
        if key is None:
            unmatched += 1
            continue
        groups[key].append(row)
    scattered = 0
    vertical = 0
    malformed = 0
    for members in groups.values():
        members.sort(key=lambda r: r.get("carry_index") or 0)
        xs = {r["x"] for r in members if r["x"] is not None}
        ys = [r["y"] for r in members if r["y"] is not None]
        if len(members) < 2:
            malformed += 1
        if len(xs) > 1:
            scattered += 1
        elif ys and ys == list(range(min(ys), min(ys) + len(ys))):
            vertical += 1
    out = {
        "n_chains_reported": len(groups),
        "n_scattered_chains": scattered,
        "n_vertical_runs": vertical,
        "n_unmatched_carry4": unmatched,
        "n_malformed_chains": malformed,
        "scattered": scattered > 0,
    }
    if expected_chains is not None:
        out["expected_tdl_chains"] = expected_chains
        out["chain_count_ok"] = len(groups) == expected_chains
    return out
