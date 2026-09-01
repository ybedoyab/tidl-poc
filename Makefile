PYTHON ?= python

.PHONY: help test sim-fast sim-all

help:
	@echo "Targets:"
	@echo "  make test      Run pytest"
	@echo "  make sim-fast  Run CI-safe simulations"
	@echo "  make sim-all   Run full simulations (includes optional 1e7 calibration)"
	@echo "Windows without GNU make: python -m tidl_poc sim --fast"

test:
	$(PYTHON) -m pytest

sim-fast:
	$(PYTHON) -m tidl_poc sim --fast

sim-all:
	$(PYTHON) -m tidl_poc sim --all
