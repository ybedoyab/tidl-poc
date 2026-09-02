# S1–S16 evidence matrix

Status: **TRL 2** concept. No physical POC measurements exist.
Simulation rows are **model-based simulation**. Literature rows are **literature evidence**.
Implementation rows are **RTL/synthesis/implementation** or datasheet arithmetic only.

Resolution, precision, and accuracy are distinct (S14). A 1 ps digital LSB is not
1 ps physical resolution. **S14 is not complete.**

Operating temperature: laboratory 20–23 °C; required operating range 10–40 °C.
No Bluetooth. No Wi-Fi.

End-of-POC (not claimed now): TRL 5/6, ≤12 months, field-test ready.

Legend for **Architecture defined:** yes = POC candidate documented in this repo.

---

## Summary

| ID | Architecture defined | Model/sim | Local impl. evidence | Physical POC still required |
| --- | --- | --- | --- | --- |
| S1 | yes (LMK05318B candidate) | yes | no board | yes |
| S2 | yes (50 Ω) | partial | no | yes |
| S3 | yes (`SET_UTC_EPOCH_ON_NEXT_PPS`) | yes | no board | yes |
| S4 | yes (50 Ω) | no | no | yes |
| S5 | yes (event TDC path) | yes | FPGA structural only | yes |
| S6 | yes (ADCMP582 path) | datasheet arith. + SPICE family core | no board | yes |
| S7 | yes (16 simultaneous preferred) | yes | Vivado 16ch both branches | yes (metrology) |
| S8 | yes (dual AC concept) | no | no | yes |
| S9 | yes (SNMPv3 concept) | no | no | yes |
| S10 | yes (UDP + internal log) | yes | no | yes |
| S11 | yes (≤3U concept) | no | no | yes |
| S12 | yes (UTC flags + epoch arm) | yes | no | yes |
| S13 | yes (internal log of record) | yes | no | yes |
| S14 | architecture + budget framework | yes | structural FPGA only | **yes — not closed** |
| S15 | yes (independent channels) | yes | structural | yes |
| S16 | yes (SMA female) | no | no | yes |

**Architecture-defined count: 16 / 16.**  
**Requirements still requiring physical POC verification: S1–S16 (all).**  
**S14 status: not complete** (no physical bins, no measured closed budget).

---

## S1 Frequency reference: 10 MHz

| Field | Content |
| --- | --- |
| Architecture defined | External 10 MHz 50 Ω → conditioner → **LMK05318B** → ~250 MHz FPGA clock candidate ([reference-clock-architecture.md](../analysis/reference-clock-architecture.md)). |
| Model/simulation evidence | `reference-clock`, `reference-stability`. |
| Implementation evidence | None on hardware. |
| Physical verification still required | Yes — ADEV/MDEV, pin jitter, holdover. |
| POC closing test | Traceable frequency/stability at FPGA clock pin; reference-loss/reacquisition. |

## S2 Frequency-reference impedance: 50 ohm

| Field | Content |
| --- | --- |
| Architecture defined | 50 Ω SMA female inlet. |
| Model/simulation evidence | Not S11; front-end models are timing. |
| Implementation evidence | None. |
| Physical verification still required | Yes. |
| POC closing test | S11 / TDR at 10 MHz inlet. |

## S3 Time reference: 1 PPS

| Field | Content |
| --- | --- |
| Architecture defined | Matched low-jitter 1 PPS capture; `SET_UTC_EPOCH_ON_NEXT_PPS` ([utc-timestamp-architecture.md](../analysis/utc-timestamp-architecture.md)). |
| Model/simulation evidence | `reference-clock`, `utc-timestamp`. |
| Implementation evidence | None on hardware. |
| Physical verification still required | Yes. |
| POC closing test | Timestamp 1 PPS vs traceable UTC PPS; arm/apply epoch script. |

## S4 Time-reference impedance: 50 ohm

| Field | Content |
| --- | --- |
| Architecture defined | 50 Ω SMA female. |
| Model/simulation evidence | None. |
| Implementation evidence | None. |
| Physical verification still required | Yes. |
| POC closing test | S11 / TDR. |

## S5 Measurement signal: 1 PPS

| Field | Content |
| --- | --- |
| Architecture defined | Event TDC (not DDMTD); ADCMP582 electrical path. |
| Model/simulation evidence | Coarse+fine, error-budget, calibration, mswu-literature. |
| Implementation evidence | Kintex-7 structural TDC branches (not metrology). |
| Physical verification still required | Yes. |
| POC closing test | Calibrated delayed 1 PPS injection. |

## S6 Measurement-signal impedance: 50 ohm

| Field | Content |
| --- | --- |
| Architecture defined | SMA → ADCMP582 (47–53 Ω on-chip) → PECL → DS15BR401 → Kintex-7 LVDS ([frontend-electrical-baseline.md](../analysis/frontend-electrical-baseline.md)). |
| Model/simulation evidence | `frontend-electrical` datasheet arithmetic; ADCMP580-family SPICE core retained. |
| Implementation evidence | No board. |
| Physical verification still required | Yes. |
| POC closing test | S11/TDR; eye/levels into FPGA LVDS. |

## S7 Measurement channels: 16

| Field | Content |
| --- | --- |
| Architecture defined | Preferred simultaneous 16; independent timestamps. |
| Model/simulation evidence | `channel-scaling`. |
| Implementation evidence | Multichain R7 16ch 53.92% slices; MSWU R9 16ch 11.58% slices, WNS +0.162 ns. |
| Physical verification still required | Yes (simultaneous metrology / crosstalk). |
| POC closing test | 1-vs-16 active injection. |

## S8 Power: dual-redundant AC; IEC 61000 intent

| Field | Content |
| --- | --- |
| Architecture defined | Dual AC → redundant protected supplies (block diagram). |
| Model/simulation evidence | None. |
| Implementation evidence | None. |
| Physical verification still required | Yes. |
| POC closing test | Failover; surge/burst lab plan. |

## S9 Ethernet / SNMPv3+

| Field | Content |
| --- | --- |
| Architecture defined | Wired Ethernet; SNMPv3 authPriv; carries `SET_UTC_EPOCH_ON_NEXT_PPS`. |
| Model/simulation evidence | None. |
| Implementation evidence | None. |
| Physical verification still required | Yes. |
| POC closing test | MIB walk/set; auth negative tests. |

## S10 Configurable UDP

| Field | Content |
| --- | --- |
| Architecture defined | UDP export; internal log is measurement of record. |
| Model/simulation evidence | `packet-logging`. |
| Implementation evidence | None. |
| Physical verification still required | Yes. |
| POC closing test | Drop packets; recover from log. |

## S11 Rack ≤3U

| Field | Content |
| --- | --- |
| Architecture defined | 19-inch, ≤3U concept. |
| Model/simulation evidence | None. |
| Implementation evidence | None. |
| Physical verification still required | Yes. |
| POC closing test | Fit / thermal at 10–40 °C. |

## S12 UTC-timestamped data

| Field | Content |
| --- | --- |
| Architecture defined | UTC_second + coarse + calibrated fine; quality bits; no NTP/PTP for ps phase. |
| Model/simulation evidence | `utc-timestamp`, `reference-clock`. |
| Implementation evidence | None. |
| Physical verification still required | Yes. |
| POC closing test | Traceable UTC comparison; holdover behaviour. |

## S13 Internal logging

| Field | Content |
| --- | --- |
| Architecture defined | On-instrument log with sequence / quality / cal version / integrity. |
| Model/simulation evidence | `packet-logging`. |
| Implementation evidence | None. |
| Physical verification still required | Yes. |
| POC closing test | Power-cycle replay. |

## S14 ±1 s / 20 ps accuracy / 1 ps resolution / 20 ps precision

| Field | Content |
| --- | --- |
| Architecture defined | Coarse+fine + calibration + front-end + reference plan; **not claimed met**. |
| Model/simulation evidence | Error-budget scenarios; literature-fitted TDC SSP; synthetic calibration; Vivado **not** metrology. |
| Implementation evidence | Structural FPGA fit/route only. |
| Physical verification still required | **Yes — S14 incomplete.** |
| POC closing test | Start-stop stats; DNL/INL; 10–40 °C; reference ADEV; amplitude/slew sweeps. |

## S15 Independently timestamped channels

| Field | Content |
| --- | --- |
| Architecture defined | Per-channel fine path + cal offsets; flexible start reference. |
| Model/simulation evidence | `channel-scaling`; UTC model with channel_cal_offset. |
| Implementation evidence | 16ch structural front-ends (MSWU); 16×8 multichain. |
| Physical verification still required | Yes. |
| POC closing test | Pairwise residual skew after calibration. |

## S16 SMA female

| Field | Content |
| --- | --- |
| Architecture defined | SMA female for 10 MHz, 1 PPS ref, 16 measurement. |
| Model/simulation evidence | None. |
| Implementation evidence | None. |
| Physical verification still required | Yes. |
| POC closing test | Mechanical/electrical inspection. |

## Cross-cutting

| Topic | Status |
| --- | --- |
| Fine TDC winner | **No** — not selected from Vivado alone |
| ≥10 year operation | Design target only |
| TRL 5/6 ≤12 months | Plan only ([poc-validation-plan.md](../competition/poc-validation-plan.md)) |
| No Bluetooth / Wi-Fi | Architecture constraint |
