# Evidence summary

Project status: **TRL 2**. Not TRL 3. No laboratory validation.
Submission outline: [submission-outline.md](submission-outline.md).

| Class | Present? |
| --- | --- |
| 1 literature evidence | Yes — bibliography and claims register |
| 2 model-based simulation | Yes — `python -m tidl_poc sim --fast` |
| 3 RTL/synthesis/implementation | Yes — multichain R6/R7; MSWU R8 historical + R9 validated. Structural only |
| 4 SPICE / front-end simulation | ADCMP580-family macromodel workflow + local batch when run |
| 5 physical POC measurement | No |

## Frozen FPGA structural evidence (not metrology)

| Branch | 16ch | WNS @ 4 ns | Route |
| --- | --- | --- | --- |
| Multichain Round 7 | 8192 CARRY4, 32800 FF, 21547 LUT, 13669 slices (53.92%) | +3.045 ns | fully_routed |
| MSWU validated Round 9 | 800 CARRY4, 13112 FF, 1038 LUT, 2935 slices (11.58%); 16/16 vertical | +0.162 ns | fully_routed |

1ch sequential MSWU preencoder surrogate (R9): 434 LUT (Round 8 LUT=3 superseded).
**No fine-TDC architecture winner selected from Vivado alone.**

## POC electrical / clock / UTC candidates (not built)

- Front-end: ADCMP582 → PECL → DS15BR401 → Kintex-7 LVDS
  ([frontend-electrical-baseline.md](../analysis/frontend-electrical-baseline.md)).
  Direct VCCO=2.5 V → LVDS_25 is optional, not baseline.
- Reference: LMK05318B ([reference-clock-architecture.md](../analysis/reference-clock-architecture.md)).
- UTC: `SET_UTC_EPOCH_ON_NEXT_PPS` ([utc-timestamp-architecture.md](../analysis/utc-timestamp-architecture.md)).

## What the models support (carefully)

- Literature-fitted multi-chain SSP model (Mao anchors) — not this FPGA.
- Synthetic calibration, error-budget framework, PVT state, channel covariance,
  reference flags, UTC epoch arming behaviour, packet vs log reconciliation,
  datasheet-level PECL/LVDS/translator arithmetic.
- Kintex-7 structural fit/route for both architecture branches.

## What they do not support

Any statement that this project has achieved 20 ps precision, 1 ps resolution,
UTC-timestamped field data, or Wave Union physical pulse performance.

Details: [claims-register.md](claims-register.md),
[S1–S16 matrix](../requirements/S1-S16-evidence-matrix.md).
