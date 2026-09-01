# Evidence summary

Project status: **TRL 2**. Not TRL 3. No laboratory validation.

| Class | Present? |
| --- | --- |
| 1 literature evidence | Yes — bibliography and claims register |
| 2 model-based simulation | Yes — `python -m tidl_poc sim --fast` |
| 3 RTL/synthesis/implementation | Scaffolding only; no timing/utilization numbers |
| 4 SPICE / front-end simulation | No |
| 5 physical POC measurement | No |

## What the models support (carefully)

- A literature-fitted multi-chain SSP model with a common-mode floor, including
  sensitivity to the Mao 2022 anchors.
- Synthetic code-density calibration behaviour on an illustrative TDL.
- Arithmetic feasibility of ±1 s at 1 ps digital quantization.
- An error-budget *framework* with precision vs accuracy tables; conservative and
  stress miss 20 ps; `target_allocation` is a labelled engineering allocation.
- PVT time-domain calibration state (residual zero at each epoch) for 10–40 °C.
- 16-channel covariance with shared offsets and a crosstalk sweep.
- First-order `delta_t = y * tau` reference allocation (not ADEV).
- Front-end slew/noise contours for 5/10/15 ps allocations.
- UTC flag state, and UDP vs internal-log reconciliation.

## What they do not support

Any statement that this project has achieved 20 ps precision, 1 ps resolution,
or UTC-timestamped field data.

Details: [claims-register.md](claims-register.md),
[S1–S16 matrix](../requirements/S1-S16-evidence-matrix.md).
