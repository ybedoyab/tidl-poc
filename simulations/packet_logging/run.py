"""Shim. Prefer: python -m tidl_poc sim packet-logging"""

from tidl_poc.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["sim", "packet-logging"]))
