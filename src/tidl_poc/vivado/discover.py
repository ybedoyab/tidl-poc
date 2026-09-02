"""Discover a local Vivado install and choose a Kintex-7 part.

Machine-specific paths must stay in gitignored outputs, never in tracked docs.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

_VERSION_RE = re.compile(r"vivado\s+v(?P<ver>[\d.]+)", re.IGNORECASE)
_PART_RE = re.compile(r"^xc7k\d+", re.IGNORECASE)
_SPEED_RE = re.compile(r"(-[0-9]+[lL]?)$")
_DEVICE_RE = re.compile(r"(xc7k\d+t)", re.IGNORECASE)


def common_vivado_roots() -> list[Path]:
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    return [
        Path("D:/AMD"),
        Path("C:/AMD"),
        Path("D:/Xilinx"),
        Path("C:/Xilinx"),
        Path(pf) / "AMD",
        Path(pf) / "Xilinx",
        Path(pf86) / "Xilinx",
        Path(pf86) / "AMD",
    ]


def _vivado_bins_under(root: Path) -> list[Path]:
    found: list[Path] = []
    if not root.is_dir():
        return found
    # Classic: <root>/Vivado/<ver>/bin/vivado.bat
    # Compact 2026 layout: <root>/<ver>/Vivado/bin/vivado.bat
    direct = root / "Vivado" / "bin" / "vivado.bat"
    if direct.is_file():
        found.append(direct)
    for child in root.iterdir():
        if not child.is_dir():
            continue
        for cand in (
            child / "Vivado" / "bin" / "vivado.bat",
            child / "bin" / "vivado.bat",
            child / "Vivado" / child.name / "bin" / "vivado.bat",
        ):
            if cand.is_file():
                found.append(cand)
        nested = child / "Vivado"
        if nested.is_dir():
            for ver in nested.iterdir():
                bat = ver / "bin" / "vivado.bat"
                if bat.is_file():
                    found.append(bat)
    return found


def _unique_existing(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        try:
            key = p.resolve()
        except OSError:
            key = p
        if key in seen or not p.is_file():
            continue
        seen.add(key)
        out.append(p)
    return out


def vivado_on_path() -> Path | None:
    for name in ("vivado.bat", "vivado.exe", "vivado"):
        found = _which(name)
        if found is not None:
            return found
    return None


def _which(name: str) -> Path | None:
    path = os.environ.get("PATH", "")
    exts = [""]
    if os.name == "nt" and "." not in Path(name).suffix:
        pathext = os.environ.get("PATHEXT", ".BAT;.EXE;.CMD").split(";")
        exts = [e.lower() for e in pathext if e]
        if Path(name).suffix:
            exts = [""]
    for directory in path.split(os.pathsep):
        if not directory:
            continue
        base = Path(directory) / name
        if base.is_file():
            return base
        for ext in exts:
            cand = Path(directory) / f"{name}{ext}" if ext and not name.lower().endswith(ext.lower()) else base
            if cand.is_file():
                return cand
    return None


def find_vivado(explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        p = Path(explicit)
        return p if p.is_file() else None
    env = os.environ.get("TIDL_VIVADO")
    if env:
        p = Path(env)
        if p.is_file():
            return p
    on_path = vivado_on_path()
    found: list[Path] = []
    if on_path is not None:
        found.append(on_path)
    for root in common_vivado_roots():
        found.extend(_vivado_bins_under(root))
    unique = _unique_existing(found)
    if not unique:
        return None
    preferred = [p for p in unique if "2026.1" in str(p)]
    return (preferred or unique)[0]


def parse_vivado_version(text: str) -> str | None:
    match = _VERSION_RE.search(text)
    if match:
        return match.group("ver")
    short = re.search(r"VIVADO_VERSION=([\d.]+)", text)
    return short.group(1) if short else None


def query_vivado_version(vivado: Path, *, timeout_s: float = 120.0) -> str | None:
    try:
        completed = subprocess.run(
            [str(vivado), "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    blob = (completed.stdout or "") + "\n" + (completed.stderr or "")
    return parse_vivado_version(blob)


def speed_grade(part: str) -> str:
    match = _SPEED_RE.search(part.strip())
    return match.group(1).lower() if match else ""


def is_speed_minus_2(part: str) -> bool:
    return speed_grade(part) == "-2"


def device_name(part: str) -> str:
    match = _DEVICE_RE.search(part.lower())
    return match.group(1).lower() if match else part.lower()


def _package_rank(part: str) -> tuple[int, str]:
    lower = part.lower()
    if "ffg676" in lower:
        return (0, lower)
    if "ffg900" in lower:
        return (1, lower)
    if "ffg" in lower:
        return (2, lower)
    if "fbg" in lower:
        return (3, lower)
    return (4, lower)


def choose_kintex7_part(parts: list[str]) -> str:
    """Deterministic Kintex-7 pick from a `get_parts` list.

    Prefer speed-grade -2 (not -2L). Prefer XC7K160 for Kwiatkowski 2023
    literature comparability. Otherwise pick an installed Kintex-7 with
    enough resources (XC7K325T-class first).
    """
    kintex = [p.strip() for p in parts if _PART_RE.match(p.strip())]
    if not kintex:
        raise ValueError("no Kintex-7 parts in list")
    speed2 = [p for p in kintex if is_speed_minus_2(p)]
    pool = speed2 or kintex

    k160 = [p for p in pool if device_name(p) == "xc7k160t"]
    if k160:
        return sorted(k160, key=_package_rank)[0]

    for prefix in (
        "xc7k325t",
        "xc7k410t",
        "xc7k355t",
        "xc7k420t",
        "xc7k480t",
        "xc7k70t",
    ):
        cand = [p for p in pool if device_name(p) == prefix]
        if cand:
            return sorted(cand, key=_package_rank)[0]
    return sorted(pool, key=_package_rank)[0]


def part_is_synthesis_target_only(part: str) -> bool:
    return device_name(part) != "xc7k160t"


def parse_get_parts_output(text: str) -> list[str]:
    parts: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("K7_PART="):
            parts.append(line.split("=", 1)[1].strip())
            continue
        if _PART_RE.match(line) and " " not in line:
            parts.append(line)
    return parts


DISCOVER_PARTS_TCL = """\
puts "VIVADO_VERSION=[version -short]"
set k7 [get_parts -filter {FAMILY == kintex7}]
puts "K7_COUNT=[llength $k7]"
foreach p [lsort $k7] {
  puts "K7_PART=$p"
}
exit 0
"""


def query_installed_kintex7_parts(
    vivado: Path,
    tcl_path: Path,
    *,
    timeout_s: float = 180.0,
) -> tuple[str | None, list[str], str]:
    """Run a harmless get_parts Tcl. Returns (version, parts, combined output)."""
    tcl_path.parent.mkdir(parents=True, exist_ok=True)
    tcl_path.write_text(DISCOVER_PARTS_TCL, encoding="utf-8")
    try:
        completed = subprocess.run(
            [
                str(vivado),
                "-mode",
                "batch",
                "-nolog",
                "-nojournal",
                "-source",
                str(tcl_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, [], str(exc)
    blob = (completed.stdout or "") + "\n" + (completed.stderr or "")
    return parse_vivado_version(blob), parse_get_parts_output(blob), blob
