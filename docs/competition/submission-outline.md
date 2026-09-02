# Submission outline (InnoCentive / NPNTO TIDL)

Status: **TRL 2** technology concept. Not TRL 3+. Not laboratory-validated hardware.

Use this outline with [evidence-summary.md](evidence-summary.md) and
[claims-register.md](claims-register.md). Prefer conservative wording.

## Safe claim classes

### A) Literature feasibility (not this project's measurement)

Published Kintex-7 TDC / MSWU evidence (e.g. Mao 2022 multi-chain SSP;
Kwiatkowski 2023 MSWU-B on XC7K160) supports **feasibility in principle**, with
authors' calibration / temperature / manual P&R caveats. Numbers remain the
**original authors' results**.

### B) Local implementation evidence (structural only)

Both 16-channel FPGA architecture branches were synthesized / placed / routed
on XC7K160T (Vivado 2026.1):

| Branch | CARRY4 | FF | LUT | Slices | WNS @ 4 ns |
| --- | --- | --- | --- | --- | --- |
| Multichain Round 7 | 8192 | 32800 | 21547 | 13669 (53.92%) | +3.045 ns |
| MSWU validated Round 9 | 800 | 13112 | 1038 | 2935 (11.58%) | +0.162 ns |

Validated sequential MSWU preencoder surrogate (1ch): 434 LUT (Round 8 LUT=3
**superseded**). **No fine-TDC architecture winner** from Vivado alone.
Wave Union pulse physics is **not** validated by Vivado.

### C) Local SPICE (family core)

Retain exact existing ADCMP580-family macromodel results
(`scripts/ltspice/run_adcmp580.py` / `docs/analysis/frontend-adcmp580-spice.md`).
SPICE ≠ lab. Does not close PECL→FPGA I/O.

### D) Architecture candidates (manufacturer-supported, not built)

- Front-end: **ADCMP582** + PECL termination + **DS15BR401** → Kintex-7 LVDS
  ([frontend-electrical-baseline.md](../analysis/frontend-electrical-baseline.md)).
- Direct ADCMP582 VCCO=2.5 V → LVDS_25: optional; worst-corner not closed.
- Reference: **LMK05318B** with external 10 MHz authority
  ([reference-clock-architecture.md](../analysis/reference-clock-architecture.md)).
- UTC: `SET_UTC_EPOCH_ON_NEXT_PPS`
  ([utc-timestamp-architecture.md](../analysis/utc-timestamp-architecture.md)).
  NTP/PTP must not be used for picosecond phase.

### E) Maturity

**TRL 2 now.** Funded POC target: **TRL 5/6** within ≤12 months
([poc-validation-plan.md](poc-validation-plan.md)).

## Must not claim

- 0.4 ps / 1 ps / DNL / SSP / accuracy / temperature performance from Vivado
- 50 fs LMK jitter for an unconfigured ~250 MHz plan
- High-speed DJ figures as 1 PPS guarantees
- Total hardware accuracy from RSS of datasheet RJ alone
- S14 compliance

## Suggested narrative order

1. Challenge requirements S1–S16 and TRL honesty.
2. System block diagram ([architecture.md](../architecture.md)).
3. Literature anchors (A).
4. Local FPGA structural evidence (B) — two branches, no winner.
5. Front-end / clock / UTC candidates (D) + SPICE (C).
6. Error-budget framework and calibration plan — open risks explicit.
7. POC verification plan and TRL 5/6 path (E).
