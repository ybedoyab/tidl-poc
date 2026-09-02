# Evidence summary

Project status: **TRL 2**. Not TRL 3. No laboratory validation.

| Class | Present? |
| --- | --- |
| 1 literature evidence | Yes — bibliography and claims register |
| 2 model-based simulation | Yes — `python -m tidl_poc sim --fast` |
| 3 RTL/synthesis/implementation | Yes — Kintex-7 CARRY4 TDL. Round 6: 12-case matrix (`docs/evidence/vivado_kintex7/`). Round 7 timing-clean @64: 4/4 impl met 4 ns WNS (`docs/evidence/vivado_kintex7_timing_clean/`). MSWU structural surrogate: 3 local cases (`docs/evidence/vivado_kintex7_mswu_structural/`). Resource/P&R only; not 1 ps / DNL / SSP / WU pulse physics |
| 4 SPICE / front-end simulation | Workflow + runner; results only after local LTspice batch |
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
- Kwiatkowski 2023 transcription plus challenge-rate / naive-resource arithmetic
  (`mswu-literature`); not MSWU physics and not this FPGA.
- Kintex-7 structural CARRY4 TDL synthesis/implementation reports
  ([docs/evidence/vivado_kintex7/](../evidence/vivado_kintex7/) Round 6;
  [docs/evidence/vivado_kintex7_timing_clean/](../evidence/vivado_kintex7_timing_clean/)
  Round 7 timing-clean @64;
  [docs/evidence/vivado_kintex7_mswu_structural/](../evidence/vivado_kintex7_mswu_structural/)
  MSWU structural surrogate). Multichain 16×8×64: 8192 CARRY4, fully routed,
  WNS +3.045 ns. MSWU 16ch low-rate: 800 CARRY4, 3002 slices, fully routed,
  WNS −1.109 ns (benchmark timing not closed). Neither is TDC-bin timing or S14.

## What they do not support

Any statement that this project has achieved 20 ps precision, 1 ps resolution,
or UTC-timestamped field data.

Details: [claims-register.md](claims-register.md),
[S1–S16 matrix](../requirements/S1-S16-evidence-matrix.md).
