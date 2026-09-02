# S1–S16 evidence matrix

Status: TRL 2 concept. No physical POC measurements exist.
Simulation rows are **model-based simulation**. Literature rows are **literature evidence**.
Cells marked TBD are not yet justified.

Resolution, precision, and accuracy are distinct (S14). A 1 ps digital LSB is not
1 ps physical resolution. Front-end jitter and channel distribution are first-class
contributors, not afterthoughts.

Operating temperature: laboratory 20–23 °C; required operating range 10–40 °C.
No Bluetooth. No Wi-Fi.

End-of-POC (not claimed now): TRL 5/6, ≤12 months, field-test ready, reliability
and maintainability evidence, design target ≥10 years full-time operation.

---

## S1 Frequency reference: 10 MHz

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | Common 10 MHz input, 50 ohm, SMA female, distributed to coarse counter and TDC sampling clock after qualification. |
| Literature support | Huang 2026 (periodic characterisation context); NIST SP 1065 / IEEE 1139 (stability methodology). |
| Current simulation evidence | Behavioural qualification / loss / holdover flags: `python -m tidl_poc sim reference-clock`. |
| Current gap | No oscillator, no ADEV, no measured 10 MHz jitter allocation. Kwiatkowski 2023 notes that for intervals longer than hundreds of µs their TCXO, not the counter, limited precision — qualitative literature only; do not derive ADEV from it. |
| POC validation method | Measure 10 MHz presence, frequency, and short-term stability at the FPGA clock pin with a traceable counter/phase-noise setup. |
| Pass/fail acceptance criterion | TBD: qualified 10 MHz detected; holdover flag on loss; stability allocation vs 20 ps over the required interval (TBD) met. |

## S2 Frequency-reference impedance: 50 ohm

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | 50 ohm terminated analog front-end to SMA female. |
| Literature support | Standard RF practice; no TDC paper substitutes for a front-end design. |
| Current simulation evidence | Front-end jitter model is voltage-noise/slew, not S11. ADCMP580 is a datasheet candidate with on-chip 50 ohm inputs (external component evidence). |
| Current gap | No S11/TDR. ADCMP580 SPICE is comparator timing, not inlet impedance. |
| POC validation method | S11 / return-loss and TDR at the 10 MHz inlet. |
| Pass/fail acceptance criterion | TBD (target 50 ohm system; numeric VSWR limit not yet set). |

## S3 Time reference: 1 PPS

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | 1 PPS UTC epoch input, independently timestamped like a measurement channel (S15). |
| Literature support | Multi-channel FPGA TDC instruments (Lusardi 2019; Bayer and Traxler 2011). |
| Current simulation evidence | Epoch alignment and UTC-valid flags in the reference-clock model. |
| Current gap | No physical 1 PPS front-end; no UTC accuracy allocation. |
| POC validation method | Timestamp the 1 PPS input against a traceable UTC-aligned PPS. |
| Pass/fail acceptance criterion | TBD once UTC error budget is allocated. |

## S4 Time-reference impedance: 50 ohm

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | Same 50 ohm SMA female class as S2/S6. |
| Literature support | RF interconnect practice. |
| Current simulation evidence | None. |
| Current gap | No SPICE. |
| POC validation method | S11 / TDR at the 1 PPS reference inlet. |
| Pass/fail acceptance criterion | TBD. |

## S5 Measurement signal: 1 PPS

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | Event TDC path (not DDMTD). Arbitrary 1 PPS edges, not a continuous beat-note. |
| Literature support | Huang 2026: DDMTD is weaker for the authors' periodic phase tests than a multi-chain TDC and is not an event interpolator. Kwiatkowski 2023 timestamp architecture is event-capable (literature). |
| Current simulation evidence | Coarse+fine range model; error budget; calibration synthetic TDL; `mswu-literature` 16 events/s vs 140 MSa/s encoder Fmax (interpretation). |
| Current gap | No FPGA event capture; comparator not selected (ADCMP580 is a candidate). Challenge amplitude/rise/threshold unspecified. |
| POC validation method | Inject calibrated 1 PPS / delayed 1 PPS into measurement channels. |
| Pass/fail acceptance criterion | S14 on the injected interval (after front-end and TDC are built). |

## S6 Measurement-signal impedance: 50 ohm

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | 50 ohm SMA female per channel. |
| Literature support | RF practice. |
| Current simulation evidence | Front-end jitter uses slew and voltage noise, not impedance. ADCMP580 datasheet: on-chip 50 ohm at both inputs. Local LTspice characterization: `scripts/ltspice/run_adcmp580.py` (SPICE/front-end simulation). |
| Current gap | No laboratory 1 PPS edge. Direct DC ADCMP580 CML → Kintex-7 LVDS is not a valid baseline (CM ≈ −0.2 V vs LVDS VICM min ≈ +0.3 V); see [cml-to-kintex7-interface-options.md](../analysis/cml-to-kintex7-interface-options.md). Challenge amplitude/rise unspecified. |
| POC validation method | S11 / TDR per channel. |
| Pass/fail acceptance criterion | TBD. |

## S7 Measurement channels: 16

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | Preferred: 16 simultaneous independently timestamped channels. Alternate: analog/digital switching, including hot switching. |
| Literature support | Bayer and Traxler 2011 (48 ch); Lusardi 2019; Garzetti 2021; Kwiatkowski 2023 two-channel XC7K160 resources (literature, high-rate instrument). Resource scaling is device-specific (Morabito 2024). |
| Current simulation evidence | 16-channel covariance/skew model (`channel-scaling`). RTL top parameter `N_CHANNELS=16`. Naive 16 × paper-channel arithmetic in `mswu-literature` (not a fit claim). Kintex-7 structural TDL: multichain 16×8×64 @ 13,669 slices / 53.92% (`docs/evidence/vivado_kintex7_timing_clean/`); MSWU surrogate 16ch @ 3002 slices / 11.84% (`docs/evidence/vivado_kintex7_mswu_structural/`). Neither is S14. |
| Current gap | Switching path not designed; crosstalk coefficient assumed. Paper FIFOs are not our architecture. Vivado utilization is resource evidence, not simultaneous 16-channel metrology. |
| POC validation method | Simultaneous 16-channel injection vs single-active; if switching is chosen, hot-switch transient test. |
| Pass/fail acceptance criterion | 16 channels meet S14 simultaneously (preferred) or documented switch/settle budget (alternate). TBD numerically until error budget is closed. |

## S8 Power: dual-redundant AC; IEC 61000 surge/burst intent

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | Dual AC inlets, OR-ing / redundant PSU, inlet filtering toward IEC 61000-4-4 / 4-5. |
| Literature support | EMC standards (not TDC literature). |
| Current simulation evidence | None. |
| Current gap | No PSU, no inlet filter, no BOM, no EMC plan beyond a placeholder. |
| POC validation method | Dual-feed failover; surge/burst test plan at a qualified lab. |
| Pass/fail acceptance criterion | TBD: survive specified surge/burst without false timestamps beyond S14 (criterion not yet written). |

## S9 Monitoring/control: Ethernet, SNMP v3+

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | Wired Ethernet only. SNMPv3 (authPriv) for monitoring/control. |
| Literature support | IETF SNMPv3; not timing literature. |
| Current simulation evidence | None (protocol not implemented). |
| Current gap | No stack, no MIB, no threat model beyond “no radio”. |
| POC validation method | SNMPv3 walk/set against a frozen MIB; negative test that v2c is disabled if required. |
| Pass/fail acceptance criterion | TBD MIB and security profile. |

## S10 Data transfer: configurable UDP

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | Configurable UDP export of timestamp records; internal log is the measurement of record. |
| Literature support | None required for the concept. |
| Current simulation evidence | Packet drop/reorder/duplicate vs internal-log replay (`packet-logging`). Software/data-path only. |
| Current gap | No FPGA/software implementation; no rate/MTU study. Specified 1 PPS × 16 = 16 events/s does not need hundreds of MS/s host transfer ([low-rate-16-channel-datapath.md](../analysis/low-rate-16-channel-datapath.md)). |
| POC validation method | Inject known sequences; drop packets on the LAN; recover from internal log. |
| Pass/fail acceptance criterion | External UDP loss does not imply measurement loss while the internal log is intact. |

## S11 Rack: 19 inch, maximum 3U

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | 19-inch chassis, height ≤ 3U, SMA bulkhead density TBD. |
| Literature support | EIA-310 rack practice. |
| Current simulation evidence | None. |
| Current gap | No mechanical design, thermal CFD, or connector map. |
| POC validation method | Fit check; thermal rise at 10–40 °C ambient. |
| Pass/fail acceptance criterion | Height ≤ 3U; 16+3 SMA females accessible; thermal design keeps FPGA in the calibrated envelope (TBD). |

## S12 All data timestamped to a UTC source

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | Coarse epoch from 10 MHz aligned to 1 PPS; UTC-valid and holdover quality bits on every record. |
| Literature support | NIST SP 1065, IEEE 1139 (how to *state* stability; not a UTC time-error budget). |
| Current simulation evidence | Flag/state model only. No UTC accuracy number. |
| Current gap | No UTC error allocation vs S14 over 1 s and over operating temperature. |
| POC validation method | Compare timestamps to a traceable UTC PPS; report holdover behaviour on reference loss. |
| Pass/fail acceptance criterion | TBD after allocating reference-clock error. Do not claim UTC accuracy now. |

## S13 Internal data logging as backup

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | On-instrument circular log with sequence, quality, calibration version, CRC. |
| Literature support | None required. |
| Current simulation evidence | Record schema + reconciliation model. |
| Current gap | No media endurance, no filesystem, no 10-year retention design. Buffer sizing deferred until record format and outage-retention are fixed. |
| POC validation method | Fill, power-cycle, replay, compare to injected sequences. |
| Pass/fail acceptance criterion | Zero measurement loss on replay when the log is intact; UDP-only path may lose packets. |

## S14 Measurement: ±1 s, accuracy 20 ps, resolution 1 ps, precision 20 ps

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | Signed coarse counter + fine TDC; code-density and PVT calibration; front-end slew control. |
| Literature support | Mao 2022 (SSP/resolution on Kintex-7 MCS, **literature only**); Kwiatkowski 2023 (MSWU-B on XC7K160: ~0.4 ps mean resolution, interval std generally <4 ps / up to 5.2 ps near 10 ns, **authors' FPGA**, not this project; low LSB is not low INL); Pan 2014 (20 ps TDC with temperature correction, **authors' FPGA**, not this project). |
| Current simulation evidence | Coarse+fine arithmetic; parallel-chain SSP model; synthetic calibration; error-budget scenarios; PVT sweeps including a 0.525 ps/°C literature offset scenario; front-end slew contours; `mswu-literature` calculator. Kintex-7 structural P&R: Round 6, Round 7 timing-clean multichain, and MSWU structural surrogate (`docs/evidence/vivado_kintex7_mswu_structural/`) are **not** S14. |
| Current gap | No physical TDC bins, no closed error budget with measured terms. Vivado WNS on the 4 ns benchmark is capture/control timing, not 1 ps resolution. Round 7 multichain met 4 ns; MSWU 16ch did not (WNS −1.109 ns) — still not metrology. |
| POC validation method | Start-stop statistical tests; code-density DNL/INL; temperature sweep 10–40 °C; ADEV of the reference (NIST SP 1065). |
| Pass/fail acceptance criterion | Precision: RMS of repeated intervals ≤ 20 ps under stated conditions. Accuracy: \|mean error vs traceable interval\| ≤ 20 ps. Resolution: demonstrated physical LSB / effective resolution ≤ 1 ps **without** equating digital quantization to physics. Range: represent and measure −1 s to +1 s. All TBD until hardware exists. |

## S15 Independently timestamped channels

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | Per-channel fine engine and combiner; software may designate any channel (or the 1 PPS ref) as the interval start. |
| Literature support | Multi-channel FPGA TDC papers above. |
| Current simulation evidence | Channel covariance model; RTL `channel_event_if`. |
| Current gap | No measured channel-to-channel skew residual. |
| POC validation method | Pairwise interval matrix; residual after calibration. |
| Pass/fail acceptance criterion | Any pair usable as start/stop; residual skew inside the S14 allocation (TBD). |

## S16 Cabling/connectors: SMA female

| Field | Content |
| --- | --- |
| Proposed subsystem/technique | SMA female bulkheads for 10 MHz, 1 PPS ref, and 16 measurement inputs. |
| Literature support | Connector practice. |
| Current simulation evidence | None. |
| Current gap | No connector BOM or panel drawing. |
| POC validation method | Mechanical/electrical inspection. |
| Pass/fail acceptance criterion | Specified ports are SMA female; 50 ohm system intent (S2/S4/S6). |

## Cross-cutting (not numbered, still in scope)

| Topic | Current evidence | Gap |
| --- | --- | --- |
| Dual AC / IEC 61000 | Requirement captured | Design TBD |
| ≥10 year full-time operation | Design *target* only | No reliability data |
| TRL 5/6 in ≤12 months | Plan in `docs/competition/poc-validation-plan.md` | Not started |
| No Bluetooth / Wi-Fi | Stated architecture constraint | Review every interface addition |
