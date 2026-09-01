"""Command-line entry: python -m tidl_poc sim --fast"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable

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
    utc_reference,
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
    "packet-logging": packet_logging.run,
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
    return 2
