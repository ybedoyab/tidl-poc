"""Command-line entry: python -m tidl_poc sim --fast"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable

from pathlib import Path

from tidl_poc import DEFAULT_SEED
from tidl_poc.common.metadata import validate_metadata_schema
from tidl_poc.common.paths import outputs_dir
from tidl_poc.models import (
    channel_scaling,
    coarse_fine,
    code_density,
    error_budget,
    frontend_jitter,
    packet_logging,
    parallel_chains,
    pvt,
    reference_stability,
    utc_reference,
    mswu_literature,
)

SIMULATIONS: dict[str, Callable[..., dict]] = {
    "parallel-chains": parallel_chains.run,
    "calibration": code_density.run,
    "coarse-fine": coarse_fine.run,
    "error-budget": error_budget.run,
    "pvt": pvt.run,
    "channel-scaling": channel_scaling.run,
    "frontend-jitter": frontend_jitter.run,
    "reference-clock": utc_reference.run,
    "reference-stability": reference_stability.run,
    "packet-logging": packet_logging.run,
    "mswu-literature": mswu_literature.run,
}


def run_named(name: str, seed: int = DEFAULT_SEED, fast: bool = True) -> dict:
    if name not in SIMULATIONS:
        known = ", ".join(sorted(SIMULATIONS))
        raise KeyError(f"unknown simulation {name!r}; choose from {known}")
    return SIMULATIONS[name](seed=seed, fast=fast)


def run_many(names: list[str] | None, seed: int, fast: bool) -> dict[str, dict]:
    selected = names or list(SIMULATIONS)
    results = {}
    for name in selected:
        results[name] = run_named(name, seed=seed, fast=fast)
    return results


def verify_output_schemas() -> list[str]:
    errors: list[str] = []
    root = outputs_dir()
    metas = list(root.glob("*/metadata.json"))
    if not metas:
        errors.append("no metadata.json files under outputs/")
    for path in metas:
        payload = json.loads(path.read_text(encoding="utf-8"))
        missing = validate_metadata_schema(payload)
        if missing:
            errors.append(f"{path}: missing {missing}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TIDL TRL-2 model-based simulations")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sim = sub.add_parser("sim", help="run model-based simulations")
    sim.add_argument("names", nargs="*", help="simulation names; default is all")
    sim.add_argument("--fast", action="store_true", help="CI-safe reduced sample counts")
    sim.add_argument("--all", action="store_true", dest="run_all", help="include optional heavy cases")
    sim.add_argument("--seed", type=int, default=DEFAULT_SEED)
    sim.add_argument("--verify-schema", action="store_true", help="validate metadata JSON after running")
    vb = sub.add_parser(
        "vivado-baseline",
        help="Kintex-7 structural TDC synthesis/implementation (not CI; not a measurement)",
    )
    vb.add_argument("--vivado", type=Path, default=None, help="path to vivado.bat / vivado")
    vb.add_argument("--impl-all", action="store_true", help="place/route every matrix case (slow)")
    vb.add_argument("--skip-run", action="store_true", help="generate Tcl/CSV scaffolding without launching Vivado")
    vb.add_argument("--only", type=str, default=None, help="run a single case id")
    vb.add_argument(
        "--timeout-s",
        type=float,
        default=21600.0,
        help="per-case Vivado timeout seconds (default 6 h)",
    )
    vb.add_argument(
        "--export-only",
        action="store_true",
        help="re-parse existing outputs/vivado_kintex7 reports; do not launch Vivado",
    )
    tc = sub.add_parser(
        "vivado-timing-clean",
        help="timing-clean 64-CARRY4/channel scaling benchmark (not CI; not a measurement)",
    )
    tc.add_argument("--vivado", type=Path, default=None, help="path to vivado.bat / vivado")
    tc.add_argument("--skip-run", action="store_true", help="generate Tcl without launching Vivado")
    tc.add_argument("--only", type=str, default=None, help="run a single case id")
    tc.add_argument("--timeout-s", type=float, default=21600.0, help="per-case timeout seconds")
    tc.add_argument(
        "--export-only",
        action="store_true",
        help="re-parse outputs/vivado_kintex7_timing_clean; do not launch Vivado",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "sim":
        fast = not args.run_all
        if args.fast:
            fast = True
        names = args.names or None
        run_many(names, seed=args.seed, fast=fast)
        if args.verify_schema or True:
            errors = verify_output_schemas()
            if errors:
                print("schema errors:", file=sys.stderr)
                for err in errors:
                    print(" ", err, file=sys.stderr)
                return 1
        print("simulations complete; outputs are model-based simulation, not physical measurement")
        return 0
    if args.cmd == "vivado-baseline":
        from tidl_poc.vivado.baseline import compact_resource_line, run as run_vivado_baseline

        result = run_vivado_baseline(
            vivado=args.vivado,
            skip_run=args.skip_run,
            impl_all=args.impl_all,
            only=args.only,
            timeout_s=args.timeout_s,
            export_only=args.export_only,
        )
        extra = result["extra"]
        print("RTL/synthesis/implementation evidence; not a physical measurement")
        print(f"output_dir={result['output_dir']}")
        print(f"evidence_dir={result.get('evidence_dir')}")
        print(f"vivado_found={'yes' if extra.get('vivado_found') else 'no'}")
        print(f"vivado_version={extra.get('vivado_version')}")
        print(f"part={extra.get('part')}")
        print(f"synth_ok={extra.get('synth_ok')} synth_failed={extra.get('synth_failed')} synth_skipped={extra.get('synth_skipped')}")
        print(f"impl_ok={extra.get('impl_ok')} impl_failed={extra.get('impl_failed')} impl_skipped={extra.get('impl_skipped')}")
        for n_ch in (1, 4, 8, 16):
            print(compact_resource_line(extra, n_ch, 64))
        return 0 if extra.get("discover_error") is None or extra.get("synth_ok", 0) > 0 else 2
    if args.cmd == "vivado-timing-clean":
        from tidl_poc.vivado.baseline import compact_resource_line
        from tidl_poc.vivado.timing_clean import run as run_timing_clean

        result = run_timing_clean(
            vivado=args.vivado,
            skip_run=args.skip_run,
            only=args.only,
            timeout_s=args.timeout_s,
            export_only=args.export_only,
        )
        extra = result["extra"]
        print("RTL/synthesis/implementation evidence; not a physical measurement")
        print(f"output_dir={result['output_dir']}")
        print(f"evidence_dir={result.get('evidence_dir')}")
        print(f"vivado_version={extra.get('vivado_version')}")
        print(f"part={extra.get('part')}")
        print(f"synth_ok={extra.get('synth_ok')} impl_ok={extra.get('impl_ok')}")
        for n_ch in (1, 4, 8, 16):
            print(compact_resource_line(extra, n_ch, 64))
        return 0 if extra.get("synth_ok", 0) > 0 else 2
    return 2
