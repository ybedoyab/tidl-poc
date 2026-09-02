# Error budget

S14 precision target: 20 ps RMS. Accuracy 20 ps is a separate, traceable-mean
requirement. Resolution 1 ps is not this budget.

Model: `python -m tidl_poc sim error-budget`

Each term is one of:

- `random_precision` — RSS into the precision table
- `deterministic_calibratable_bias` — linear sum into the accuracy/worst-case table
- `correlated_common_mode` — included in precision RSS-with-common

Accuracy worst-case bound used here is `sum(|bias|) + precision_RSS_with_common`
(1-sigma style). It is not a laboratory k-factor.

Non-literature numbers are **engineering allocations, not evidence**. The FPGA
TDC SSP uses the Mao-fitted model (N=10 / N=1 / N=8 depending on scenario).

**Do not** convert peak-to-peak DJ to RMS. **Do not** claim total hardware accuracy.

## Random manufacturer anchors (external component evidence only)

| Anchor | Value | Conditions / caveat |
| --- | --- | --- |
| ADCMP582 RJ | 0.2 ps RMS | Under stated datasheet conditions; not a 1 PPS system guarantee |
| DS15BR400/401-family RJ | 0.5 ps typ (1.5 ps max) | Under stated 750 MHz family test; translator path adds a budget line |
| LMK05318B-class jitter | ~50 fs typ / ~80 fs max RMS @ 312.5 MHz | Only under manufacturer integration conditions; **not** claimed for ~250 MHz POC plan without TICS Pro |

These anchors are **not** silently substituted as the sole front-end / clock terms
in the RSS scenarios below. Scenario allocations remain conservative until board
measurements exist.

## Systematic / calibration-sensitive terms

| Term class | Examples |
| --- | --- |
| Temperature | ADCMP582 0.25 ps/°C propagation-delay TC; translator temp behaviour where specified |
| Amplitude / slew | Overdrive / slew / common-mode dispersion (DJ figures are pattern-specific, not 1 PPS guarantees) |
| Interconnect | PCB trace mismatch; FPGA channel offset |
| Calibration | Code-density LUT residual; stale LUT after PVT |
| Reference | 10 MHz stability over the interval ([reference-stability.md](reference-stability.md)) |

## Scenarios

1. **literature-informed illustrative** — analog terms not silently tiny.
2. **conservative** — intended to **fail** 20 ps precision until allocations improve.
3. **stress** — intended to fail clearly.
4. **target_allocation** — labelled design allocation: frontend 5 ps, time-walk
   bias 3 ps, 8-chain literature-fitted TDC, coarse/reference 4 ps, channel
   random 4 ps, calibration random 3 ps, PVT random 4 ps, supply 2 ps, clock
   distribution 3 ps, common-mode 2 ps. **Not evidence.** Kwiatkowski 2023 MSWU
   resolution/precision numbers are **not** substituted into this table.

If a submission quotes only scenario 1 or 4, that is incomplete.

## POC calibration plan (required before claiming S14)

1. Per-channel zero-delay / cable-delay characterization.
2. Code-density (or equivalent) TDL / encoder calibration.
3. Temperature sweep **10–40 °C** with recalibration policy documented.
4. Input amplitude / slew sweep on the ADCMP582 path.
5. All-16 simultaneous injection vs single-active crosstalk check.
6. Reference-loss and reacquisition scripts (flags must not silently relabel UTC).
7. Recalibration interval vs residual budget (see [pvt-strategy.md](pvt-strategy.md)).

## Gaps

No term is measured on this project's hardware. Long intervals (→ 1 s) need the
first-order reference allocation in [reference-stability.md](reference-stability.md)
and, later, ADEV from NIST SP 1065. That is not folded into the picosecond RSS
table as a measured stability number.

