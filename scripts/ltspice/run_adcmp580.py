"""Run ADCMP580 LTspice characterization.

Usage:
  python scripts/ltspice/run_adcmp580.py
  python scripts/ltspice/run_adcmp580.py --all
  python scripts/ltspice/run_adcmp580.py --ltspice "C:\\path\\LTspice.exe"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tidl_poc.spice.adcmp580 import run
from tidl_poc.spice.ltspice import find_ltspice


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ADCMP580 SPICE/front-end characterization")
    parser.add_argument("--fast", action="store_true", help="reduced sweep (default unless --all)")
    parser.add_argument("--all", action="store_true", dest="run_all", help="full overdrive/slew/rise grid")
    parser.add_argument("--ltspice", type=Path, default=None, help="path to LTspice.exe")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    fast = True
    if args.run_all:
        fast = False
    if args.fast:
        fast = True
    exe = find_ltspice(args.ltspice)
    if exe is None:
        print(
            "LTspice.exe not found. Pass --ltspice or set TIDL_LTSPICE.",
            file=sys.stderr,
        )
        return 2
    try:
        result = run(fast=fast, ltspice=exe)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    extra = result["extra"]
    print("SPICE/front-end simulation complete; not a physical measurement")
    print(f"output_dir={result['output_dir']}")
    print(f"mean_tpd_ps={extra.get('mean_tpd_ps')}")
    print(f"dispersion_ps={extra.get('dispersion_ps')}")
    print(f"tpd_sim_minus_datasheet_typ_ps={extra.get('tpd_sim_minus_datasheet_typ_ps')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
