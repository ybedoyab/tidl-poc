"""Kintex-7 structural TDC Vivado baseline.

Usage:
  python scripts/vivado/run_kintex7_baseline.py
  python scripts/vivado/run_kintex7_baseline.py --vivado "C:\\path\\vivado.bat"
  python -m tidl_poc vivado-baseline

Not a CI dependency. Not a physical measurement. No bitstreams.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tidl_poc.vivado.baseline import compact_resource_line, run
from tidl_poc.vivado.discover import find_vivado


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Kintex-7 CARRY4 TDL structural synthesis/implementation evidence"
    )
    parser.add_argument("--vivado", type=Path, default=None, help="path to vivado.bat or vivado")
    parser.add_argument("--impl-all", action="store_true", help="place/route all 12 cases")
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="write Tcl and metadata without invoking Vivado",
    )
    parser.add_argument("--only", type=str, default=None, help="run a single case id")
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=21600.0,
        help="per-case Vivado timeout seconds (default 6 h)",
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="re-parse existing outputs/vivado_kintex7 reports; do not launch Vivado",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.export_only:
        result = run(export_only=True)
        extra = result["extra"]
        print("RTL/synthesis/implementation evidence; not a physical measurement")
        print(f"output_dir={result['output_dir']}")
        print(f"evidence_dir={result.get('evidence_dir')}")
        print(f"synth_ok={extra.get('synth_ok')} synth_failed={extra.get('synth_failed')} synth_skipped={extra.get('synth_skipped')}")
        print(f"impl_ok={extra.get('impl_ok')} impl_failed={extra.get('impl_failed')} impl_skipped={extra.get('impl_skipped')}")
        for n_ch in (1, 4, 8, 16):
            print(compact_resource_line(extra, n_ch, 64))
        return 0 if extra.get("synth_ok", 0) > 0 else 2
    if args.vivado is None and find_vivado() is None and not args.skip_run:
        print(
            "Vivado not found. Pass --vivado or set TIDL_VIVADO, or install Vivado 2026.1.",
            file=sys.stderr,
        )
        # Still emit scaffolding so RTL/tests/docs remain usable.
        result = run(skip_run=True)
        extra = result["extra"]
        print("generated Tcl/metadata without a Vivado run", file=sys.stderr)
        print(f"output_dir={result['output_dir']}", file=sys.stderr)
        print(f"part={extra.get('part')}", file=sys.stderr)
        return 2
    result = run(
        vivado=args.vivado,
        impl_all=args.impl_all,
        skip_run=args.skip_run,
        only=args.only,
        timeout_s=args.timeout_s,
    )
    extra = result["extra"]
    print("RTL/synthesis/implementation evidence; not a physical measurement")
    print(f"output_dir={result['output_dir']}")
    print(f"vivado_found={'yes' if extra.get('vivado_found') else 'no'}")
    print(f"vivado_version={extra.get('vivado_version')}")
    print(f"part={extra.get('part')}")
    print(f"synth_ok={extra.get('synth_ok')} synth_failed={extra.get('synth_failed')}")
    print(f"impl_ok={extra.get('impl_ok')} impl_failed={extra.get('impl_failed')}")
    for n_ch in (1, 4, 8, 16):
        print(compact_resource_line(extra, n_ch, 64))
    if extra.get("discover_error") and extra.get("synth_ok", 0) == 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
