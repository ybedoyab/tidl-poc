"""Timing-clean Kintex-7 structural benchmark (64 CARRY4/channel only).

Usage:
  python scripts/vivado/run_kintex7_timing_clean.py
  python -m tidl_poc vivado-timing-clean
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tidl_poc.vivado.baseline import compact_resource_line
from tidl_poc.vivado.discover import find_vivado
from tidl_poc.vivado.timing_clean import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Kintex-7 timing-clean 64-CARRY4/channel structural benchmark"
    )
    parser.add_argument("--vivado", type=Path, default=None)
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--only", type=str, default=None)
    parser.add_argument("--timeout-s", type=float, default=21600.0)
    parser.add_argument("--export-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.export_only:
        result = run(export_only=True)
    elif args.vivado is None and find_vivado() is None and not args.skip_run:
        print("Vivado not found.", file=sys.stderr)
        return 2
    else:
        result = run(
            vivado=args.vivado,
            skip_run=args.skip_run,
            only=args.only,
            timeout_s=args.timeout_s,
        )
    extra = result["extra"]
    print("RTL/synthesis/implementation evidence; not a physical measurement")
    print(f"output_dir={result['output_dir']}")
    print(f"evidence_dir={result.get('evidence_dir')}")
    for n_ch in (1, 4, 8, 16):
        print(compact_resource_line(extra, n_ch, 64))
    return 0 if extra.get("synth_ok", 0) > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
