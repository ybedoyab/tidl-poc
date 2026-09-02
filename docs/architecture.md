# Architecture (hypothesis)

This document describes a **baseline hypothesis**, not a frozen implementation.
The trade study in [analysis/architecture-trade-study.md](analysis/architecture-trade-study.md)
must be allowed to change the fine-TDC candidate.

## Context

- Challenge: 16-channel Time Interval Data Logger (TIDL).
- Maturity: TRL 2. A future ≤12-month funded POC is aimed at TRL 6.
- Radio: none. Ethernet only.

## Block flow

```text
50 ohm SMA front-end (10 MHz, 1 PPS ref, 16x 1 PPS meas)
        -> per-channel fine timing engine (candidate A/B/C)
        -> bubble-resistant encoder
        -> code-density / bin-width calibration
        -> continuous or periodic PVT calibration
        -> coarse timestamp counter (10 MHz-derived)
        -> per-channel timestamp combiner
        -> UTC-referenced timing subsystem (qualify / lock / holdover flags)
        -> internal logger
        -> Ethernet: configurable UDP + SNMPv3
```

### Fine-TDC candidates

| ID | Candidate | Role |
| --- | --- | --- |
| A | Parallel multi-chain FPGA tapped delay line | Current baseline to *test* |
| B | Wave Union / multisampling TDC | High-upside alternative |
| C | Hybrid multi-chain + Wave Union | Highest 12-month implementation risk |
| Aux | DDMTD | Periodic-clock characterisation only |

DDMTD must not be assumed to replace the event TDC. Measurement inputs are 1 PPS
events (S5).

### What is intentionally not specified here

Carry-chain tap maps, encoder polynomials, and device-specific placement recipes
stay in RTL modules and, if needed, in gitignored `docs/ip/private-notes.md`.
Tracked docs describe interfaces and calibration *roles*, not a copyable layout.

## Clocking concept

- External 10 MHz (S1/S2) is the frequency reference to be qualified.
- External 1 PPS (S3/S4) is the UTC epoch.
- Coarse counter width is an arithmetic problem (see coarse+fine simulation).
- Meeting 20 ps over intervals up to 1 s is a **reference stability** problem
  (first-order `delta_t = y * tau`; NIST SP 1065 / IEEE 1139 once data exist),
  not a bit-width problem. See [analysis/reference-stability.md](analysis/reference-stability.md).

## Channel concept

Preferred: 16 simultaneous independently timestamped channels (S7, S15).
Alternate: switching, including hot switching, with an explicit settle budget.
No channel sharing of a single TDC is assumed until the trade study and
resource estimates (after a device is selected) say otherwise.

## Data path

Every record carries UTC/coarse context, channel, fine time, sequence, quality
bits, calibration version, and an integrity field. UDP is the export path;
the internal log is the measurement of record (S10, S13).

## Families and first Vivado baseline

Kintex-7 / CARRY4 with **8 parallel chains per channel** is the first synthesis
branch ([analysis/vivado-baseline-decision.md](analysis/vivado-baseline-decision.md)).
Vivado 2026.1 mapped and fully routed 1 / 4 / 8 / 16 channels at 64
CARRY4/chain on XC7K160T (16×64: 8192 CARRY4, 10,980 slices / 43.3%).
Tracked snapshot: [evidence/vivado_kintex7/](evidence/vivado_kintex7/).
MSWU type B remains a **high-upside second branch**, not a replacement.
Any MSWU-B RTL must be original (no copied paper HDL). See
[analysis/architecture-trade-study.md](analysis/architecture-trade-study.md)
and [analysis/low-rate-16-channel-datapath.md](analysis/low-rate-16-channel-datapath.md).

Other families remain candidates, not selected: low-end Kintex UltraScale
(XCKU025 / XCKU035); basic Kintex UltraScale+ (XCKU3P / XCKU5P).
`scripts/vivado/run_kintex7_baseline.py` discovers an installed Kintex-7 part
(prefer XC7K160T-2). Reports are RTL/synthesis/implementation evidence, not
1 ps resolution. The older `tidl_top` Tcl flow still needs `TIDL_PART` if used.
