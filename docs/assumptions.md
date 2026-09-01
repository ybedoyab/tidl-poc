# Assumptions

Assumptions are not measurements. Each simulation tags parameters as
`literature` or `engineering_allocation` (formerly also `assumption`).

## Evidence rules

1. Simulations are model-based simulation, never physical POC measurement.
2. Literature numbers remain the original authors' results.
3. Digital 1 ps quantization is not 1 ps physical resolution.
4. Mao et al. 2022 resolution TC (0.0002 ps/°C) is not a residual timing-error TC.
5. Mao 10-chain SSP used MCS, not independent-chain averaging. The 1/N model is a fit.
6. No PSU is selected. ADCMP580 is a **tracked front-end candidate**, not a frozen comparator. First Vivado **branch** is Kintex-7 / CARRY4 / 8 chains; that is not a measured part qualification. MSWU-B is a second branch, not a replacement.
7. No Bluetooth or Wi-Fi.
8. TRL is 2. TRL 6 is a future funded-POC target.
9. Kwiatkowski 2023 numbers (including 0.525 ps/°C) are authors' results. They are not this board.
10. Naive 16 × paper measurement-channel resources are not our architecture.

## Cross-cutting engineering assumptions (review required)

| ID | Assumption | Used by | Reviewer action |
| --- | --- | --- | --- |
| A1 | Illustrative coarse period 4 ns (250 MHz) for the synthetic TDL | calibration | Replace with the real sampling period after clocking is chosen |
| A2 | 512-bin synthetic TDL with sinusoidal + random DNL | calibration | Replace with measured bin histogram |
| A3 | Parallel-chain noise is common + independent / N | parallel-chains | Validate vs MCS / WU architecture actually built |
| A4 | Error-budget term values in four named scenarios | error-budget | Replace every `engineering_allocation` with measurement; do not quote `target_allocation` as evidence |
| A5 | Offset TC sweep 0.2–2.0 ps/°C; bin scale 1e-4–1e-3 / °C | pvt | Measure channel offset and LSB vs 10–40 °C |
| A6 | Enclosure ramp 0.05 °C/s; online-cal lag 0.2 s | pvt | Measure thermal time constants |
| A7 | Channel offset 8 ps, common 4 ps, independent 6 ps RMS; crosstalk sweep 0–1.6 ps per extra active channel | channel-scaling | Measure pairwise covariance with 1 vs 16 active |
| A8 | 0.8 V illustrative swing; 0.5 mV threshold uncertainty; 2 ps comparator; 3 ps walk | frontend-jitter | SPICE + datasheet once a part is chosen; ADCMP580 is a candidate, not a substitute for this allocation |
| A9 | 3 PPS epochs to qualify 10 MHz + 1 PPS | reference-clock | Define a real qualification metric (frequency, jitter, missing pulses) |
| A10 | UDP drop 8%, duplicate 3%, reorder 5% | packet-logging | Replace with LAN profile |
| A11 | Dual-redundant AC and IEC 61000 can be deferred to POC mechanical/EMC design | S8 | Do not treat as solved |
| A12 | ≥10 year full-time operation is a design target, not MTBF evidence | reliability-plan | Needs parts stress, wear-out, and maintenance concept |
| A13 | Simultaneous 16-channel is preferred over switching | S7 | Revisit if FPGA resources fail |
| A14 | First-order `delta_t = y * tau` for 5/10/20 ps at 1 s | reference-stability | Replace with ADEV/MDEV/TDEV on measured 10 MHz |
| A15 | 0.525 ps/°C channel-offset TC from Kwiatkowski 2023 used as an extra literature scenario | pvt / mswu-literature | Do not treat as this board; do not interpolate recalibration between temperatures |
| A16 | Paper per-channel FIFOs / 21.5 BRAM can be reduced at 16 events/s | low-rate datapath | Hypothesis only; needs Vivado. Do not invent a final BRAM number |
| A17 | CML-to-Kintex-7 from ADCMP580 is feasible | frontend candidate | Must be designed and verified; see cml-to-kintex7-interface-options.md; no path selected |

## Explicitly not assumed

- UTC time error is within 20 ps.
- Kintex-7 literature transfers to UltraScale+.
- Hybrid Wave Union + multi-chain will win the trade study.
- MSWU-B will win after the first Vivado branch.
- A behavioural SystemVerilog delay line is a 1 ps TDC.
- Naive 16-channel BRAM overflow proves 16 channels cannot fit.
- Direct ADCMP580 CML into Kintex-7 LVDS meets DS182 VICM without a translator.
