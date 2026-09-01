# Contributing

This repository is all-rights-reserved concept evidence. Contributions do not
grant you or any third party a license to the work.

## Rules

1. Do not imply that simulations are physical measurements.
2. Label every numerical result as one of:
   - literature evidence
   - model-based simulation
   - RTL/synthesis/implementation evidence
   - SPICE/front-end simulation
   - physical POC measurement (none exist at TRL 2)
3. Do not fabricate FPGA performance, measurement data, citations, hardware
   validation, TRL claims, BOM prices, or test results.
4. Do not copy HDL or code from papers or third-party repositories unless the
   license is explicitly compatible and attribution is included.
5. Do not commit paywalled or copyrighted paper PDFs. Place locally obtained
   papers in `references/private/` (gitignored).
6. Do not commit credentials, personal data, license keys, serial numbers, API
   keys, challenge screenshots, or local filesystem paths.
7. Keep potentially patentable implementation detail modular. Do not add
   speculative patent claims to tracked documentation.
8. Keep `docs/ip/private-notes.md` out of Git.

## Development

Python 3.11 or later:

```text
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m tidl_poc sim --fast
pytest
```

On Unix-like systems, `make test` and `make sim-fast` wrap the same commands.

CI must not require Vivado and must not commit generated outputs.
