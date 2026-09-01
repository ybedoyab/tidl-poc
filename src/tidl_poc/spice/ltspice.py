"""LTspice discovery, batch execution, and .meas log parsing."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

_MEAS_AT = re.compile(
    r"^(?P<name>[A-Za-z_][\w]*)\s*:.*?\bAT\s+(?P<val>[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)",
    re.MULTILINE,
)
_MEAS_EQ = re.compile(
    r"^(?P<name>[A-Za-z_][\w]*)\s*:.*?=\s*(?P<val>[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)",
    re.MULTILINE,
)
_MEAS_FAIL = re.compile(r"Measurement\s+\"(?P<name>[^\"]+)\"\s+FAIL", re.IGNORECASE)
_STEP_HEADER = re.compile(r"^Measurement:\s+(?P<name>\S+)\s*$", re.MULTILINE)


def common_ltspice_candidates() -> list[Path]:
    local = os.environ.get("LOCALAPPDATA", "")
    pf = os.environ.get("ProgramFiles", "")
    pf86 = os.environ.get("ProgramFiles(x86)", "")
    home = os.environ.get("USERPROFILE", "")
    names = (
        Path(local) / "Programs" / "ADI" / "LTspice" / "LTspice.exe",
        Path(pf) / "ADI" / "LTspice" / "LTspice.exe",
        Path(pf86) / "ADI" / "LTspice" / "LTspice.exe",
        Path(local) / "LTspice" / "LTspice.exe",
        Path(home) / "AppData" / "Local" / "Programs" / "ADI" / "LTspice" / "LTspice.exe",
    )
    return [p for p in names if str(p)]


def find_ltspice(explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        return explicit if explicit.is_file() else None
    env = os.environ.get("TIDL_LTSPICE")
    if env:
        p = Path(env)
        if p.is_file():
            return p
    for cand in common_ltspice_candidates():
        if cand.is_file():
            return cand
    return None


def find_adcmp580_library(ltspice_exe: Path | None) -> dict[str, str]:
    """Locate installed symbol/model/example. Paths are for local metadata only."""
    found: dict[str, str] = {}
    local = os.environ.get("LOCALAPPDATA", "")
    roots = [Path(local) / "LTspice"]
    if ltspice_exe is not None:
        roots.append(ltspice_exe.parent)
        roots.append(Path(local) / "LTspice")
    files = {
        "symbol": Path("lib") / "sym" / "Comparators" / "ADCMP580.asy",
        "model": Path("lib") / "sub" / "ADCMP580.sub",
        "example": Path("examples") / "Applications" / "ADCMP580.asc",
    }
    for root in roots:
        for key, rel in files.items():
            path = root / rel
            if key not in found and path.is_file():
                found[key] = str(path)
    return found


def ltspice_version(ltspice_exe: Path, timeout_s: float = 30.0) -> str | None:
    try:
        completed = subprocess.run(
            [str(ltspice_exe), "-version"],
            check=False,
            capture_output=True,
            timeout=timeout_s,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = _decode(completed.stdout) + _decode(completed.stderr)
    match = re.search(r"\d+\.\d+\.\d+", text)
    if match:
        return match.group(0)
    stripped = text.strip()
    return stripped or None


def run_batch(
    ltspice_exe: Path,
    schematic: Path,
    timeout_s: float = 600.0,
    include_path: Path | None = None,
) -> subprocess.CompletedProcess[bytes]:
    schematic = schematic.resolve()
    cmd = [str(ltspice_exe), "-b", str(schematic)]
    if include_path is not None:
        cmd.append(f"-I{include_path}")
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        timeout=timeout_s,
        cwd=str(schematic.parent),
    )


def _decode(data: bytes) -> str:
    if not data:
        return ""
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16")
    for enc in ("utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def read_log(path: Path) -> str:
    return _decode(path.read_bytes())


def parse_meas_log(text: str) -> dict[str, Any]:
    """Parse LTspice .log .meas results (single-run or .step tables)."""
    failed = {m.group("name") for m in _MEAS_FAIL.finditer(text)}
    values: dict[str, Any] = {}
    for block in _STEP_HEADER.finditer(text):
        name = block.group("name")
        start = block.end()
        nxt = _STEP_HEADER.search(text, start)
        chunk = text[start : nxt.start() if nxt else len(text)]
        nums = _column_floats(chunk, name)
        if nums:
            values[name] = nums if len(nums) > 1 else nums[0]
    at_hits: dict[str, list[float]] = {}
    for match in _MEAS_AT.finditer(text):
        at_hits.setdefault(match.group("name"), []).append(float(match.group("val")))
    eq_hits: dict[str, list[float]] = {}
    for match in _MEAS_EQ.finditer(text):
        eq_hits.setdefault(match.group("name"), []).append(float(match.group("val")))
    for name, nums in at_hits.items():
        if name not in values:
            values[name] = nums if len(nums) > 1 else nums[0]
    for name, nums in eq_hits.items():
        if name not in values:
            values[name] = nums if len(nums) > 1 else nums[0]
    values["_failed"] = sorted(failed)
    return values


def _column_floats(chunk: str, meas_name: str) -> list[float]:
    rows: list[float] = []
    for line in chunk.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("step"):
            continue
        if stripped.lower().startswith(meas_name.lower()) and not re.match(r"^\d", stripped):
            continue
        parts = stripped.replace(",", " ").split()
        if len(parts) >= 2 and re.match(r"^\d+$", parts[0]):
            try:
                rows.append(float(parts[1]))
                continue
            except ValueError:
                pass
        try:
            rows.append(float(parts[-1]))
        except ValueError:
            continue
    return rows


def log_has_model_error(text: str) -> bool:
    lowered = text.lower()
    needles = (
        "could not open",
        "unknown subcircuit",
        "unable to find",
        "missing subcircuit",
        "fatal error",
        "undefined subcircuit",
    )
    return any(n in lowered for n in needles)


def switched_clean(vout_max: float, vout_min: float, swing_v: float = 0.2) -> bool:
    return vout_max >= swing_v and vout_min <= -swing_v
