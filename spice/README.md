# SPICE / LTspice workflow

Status: TRL 2. This directory documents how the owner will run Analog Devices
macromodels. **No SPICE results exist in this repository.**

Do not invent `.asc` files unless the installed LTspice model pin interface is
known. Official macromodels stay in the local LTspice library; do not vendor
copyrighted model text into git unless Analog Devices licensing explicitly
allows redistribution (it is not assumed here).

Classification:

- Until the owner runs LTspice and returns output: **no class-4 evidence**.
- After a real run: label artefacts `SPICE/front-end simulation`.
- Never label SPICE as physical POC measurement.

## ADCMP580

See [adcmp580/README.md](adcmp580/README.md).

## What this project will add after a schematic exists

Sweeps are defined as intent only. No numbers are fabricated.

Related analysis: [../docs/analysis/frontend-candidate-adcmp580.md](../docs/analysis/frontend-candidate-adcmp580.md).
