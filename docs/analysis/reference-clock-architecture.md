# Reference-clock architecture (POC candidate)

Status: **TRL 2**. Classification: **external component evidence** +
architectural definition. Not a measured ADEV/MDEV result. Not a closed
250 MHz phase-noise configuration.

## Primary candidate: TI LMK05318B

Manufacturer facts (product / datasheet literature; **external component
evidence**):

| Item | Value |
| --- | --- |
| Status | ACTIVE |
| Architecture | One DPLL + two APLLs |
| DPLL reference inputs | Two |
| Reference input range | 1 Hz (1 PPS) to 800 MHz |
| XO/TCXO/OCXO input | 10–100 MHz |
| Outputs | Eight |
| Output formats | LVDS / LVPECL / CML / HCSL / LVCMOS |
| Features | Holdover / hitless switching; EEPROM |
| Temperature | −40 °C to +85 °C |
| APLL | BAW-based low-jitter |
| Jitter example | ~50 fs typical / ~80 fs max RMS at 312.5 MHz under specified manufacturer integration conditions |

**Do not** claim 50 fs for a future ~250 MHz FPGA clock without a TICS Pro /
phase-noise configuration result for that exact plan.

## POC reference architecture

```text
external 10 MHz, 50 Ω
  → low-jitter input conditioning
  → LMK05318B primary reference
  → low-jitter synchronous FPGA clock candidate (target ~250 MHz initially)
  → FPGA coarse counter / capture clock
```

- **External 10 MHz** remains the normal-operation frequency authority (S1).
- An onboard qualified **TCXO/OCXO** is a holdover / loop-support **candidate**;
  no specific oscillator part is selected unless manufacturer data and budget
  close that choice.
- Exact **250 MHz** LMK frequency plan (input mux, DPLL bandwidth, APLL VCO,
  output format to Kintex-7) remains a **POC action**.

## Relation to S14 / long intervals

Intervals up to 1 s make reference stability first-class
([reference-stability.md](reference-stability.md)). Literature (e.g. Kwiatkowski
2023) notes that for long intervals the reference, not the fine TDC, can dominate
precision — qualitative only; do not derive ADEV from it.

## Flags (behavioural model)

See `python -m tidl_poc sim reference-clock` and
[utc-timestamp-architecture.md](utc-timestamp-architecture.md):

- reference-loss alarm
- holdover flag
- invalid-UTC when PPS absent or epoch not armed

## Open risks

- No TICS Pro configuration for the POC clock plan yet.
- Onboard holdover oscillator not selected.
- Distribution skew from LMK to 16 TDC channels is unmeasured.
- Manufacturer jitter numbers apply only under stated integration conditions.
