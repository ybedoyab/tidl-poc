# Time Interval Data Logger (TIDL) concept evidence

TRL-2 engineering package for an Innovate UK / NPNTO Time Interval Data Logger
challenge. This repository holds a **technology concept**, literature tracking,
and **model-based simulations**. It does not contain laboratory measurements.

Current maturity: **TRL 2** (technology concept formulated).
A future 12-month funded POC is the path to **TRL 6** (demonstration in a
relevant environment). This repository does **not** claim TRL 3 or higher.

## Challenge objective

Measure 16 channels of 1 PPS against a 10 MHz + 1 PPS UTC-referenced timing
subsystem in a 19-inch rack (max 3U), with Ethernet management (SNMPv3) and
configurable UDP data transfer. Target signed range ±1 s, 1 ps resolution,
20 ps precision, and 20 ps accuracy. No Bluetooth. No Wi-Fi.

## Evidence classification

Every numerical result must be one of:

1. literature evidence
2. model-based simulation
3. RTL/synthesis/implementation evidence
4. SPICE/front-end simulation
5. physical POC measurement

At this stage, classes 1–2 exist. Class 3 is an original Kintex-7 CARRY4 TDL
plus Vivado 2026.1 OOC matrices on `xc7k160tffg676-2`:
[docs/evidence/vivado_kintex7/](docs/evidence/vivado_kintex7/) (Round-6 wide-parity),
[docs/evidence/vivado_kintex7_timing_clean/](docs/evidence/vivado_kintex7_timing_clean/)
(timing-clean multichain @ 64 CARRY4),
[docs/evidence/vivado_kintex7_mswu_structural/](docs/evidence/vivado_kintex7_mswu_structural/)
(Round 8 MSWU structural; preencoder LUT=3 superseded), and
[docs/evidence/vivado_kintex7_mswu_validated/](docs/evidence/vivado_kintex7_mswu_validated/)
(Round 9 validated MSWU). Resource, placement, and route evidence only — not 1 ps
resolution, not Wave Union pulse physics, and not physical timing. Multichain
16×8×64: 8192 CARRY4, 13,669 slices (53.92%), WNS +3.045 ns. MSWU Round 9 16ch:
800 CARRY4, 2935 slices (11.58%), WNS +0.162 ns. Class 4 is an LTspice
workflow plus local batch results when `scripts/ltspice/run_adcmp580.py`
succeeds (SPICE/front-end simulation, not lab data). Class 5 does not exist.

POC electrical / clock / UTC candidates (not built hardware):
[docs/architecture.md](docs/architecture.md),
[docs/analysis/frontend-electrical-baseline.md](docs/analysis/frontend-electrical-baseline.md),
[docs/analysis/reference-clock-architecture.md](docs/analysis/reference-clock-architecture.md),
[docs/analysis/utc-timestamp-architecture.md](docs/analysis/utc-timestamp-architecture.md).
Submission outline: [docs/competition/submission-outline.md](docs/competition/submission-outline.md).

Claims tracking: [docs/competition/claims-register.md](docs/competition/claims-register.md).
Requirement matrix: [docs/requirements/S1-S16-evidence-matrix.md](docs/requirements/S1-S16-evidence-matrix.md).

## S1–S16 requirements (abbreviated)

| ID | Requirement |
| --- | --- |
| S1 | Frequency reference 10 MHz |
| S2 | Frequency-reference impedance 50 ohm |
| S3 | Time reference 1 PPS |
| S4 | Time-reference impedance 50 ohm |
| S5 | Measurement signal 1 PPS |
| S6 | Measurement-signal impedance 50 ohm |
| S7 | 16 measurement channels (preferred: simultaneous; alternate: switching, including hot switching) |
| S8 | Dual-redundant AC inputs; inlet designed toward IEC 61000 surge/burst |
| S9 | Ethernet monitoring/control, SNMP v3+ |
| S10 | Configurable UDP data transfer |
| S11 | 19-inch rack, maximum 3U |
| S12 | All data timestamped to a UTC source |
| S13 | Internal data logging as backup |
| S14 | Signed range −1 s to +1 s; accuracy 20 ps; resolution 1 ps; precision 20 ps |
| S15 | Channels independently timestamped (flexible reference selection) |
| S16 | SMA female connectors |

Operating temperature: laboratory 20–23 °C; required 10–40 °C.

Resolution, precision, and accuracy are distinct. A 1 ps digital LSB does not
prove 1 ps physical resolution. A ±1 s range makes 10 MHz / UTC reference
stability first-class, not a counter-width footnote.

## Baseline architecture (hypothesis)

This is a hypothesis to be tested, not a selected design:

50 ohm input front-end → per-channel fine timing engine (candidate A: parallel
multi-chain FPGA TDL TDC; B: Wave Union / multisampling; C: hybrid) → coarse
timestamp counter → bubble-resistant encoder → code-density calibration →
PVT calibration → per-channel combiner → common 10 MHz + 1 PPS UTC subsystem
→ internal logger → Ethernet / UDP / SNMPv3.

DDMTD may be evaluated as an auxiliary periodic-clock characterisation mode.
It does not replace the event TDC path.

See [docs/architecture.md](docs/architecture.md) and
[docs/analysis/architecture-trade-study.md](docs/analysis/architecture-trade-study.md).

## Quick start

Python 3.11+:

```text
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
python -m tidl_poc sim --fast
```

Unix-like systems can use `make test` and `make sim-fast`. `--all` adds the
optional 1e7-sample calibration case. Generated files under `outputs/` are
gitignored. Each run writes CSV/JSON, PNG/SVG, and a metadata JSON that
labels the result as model-based simulation.

Vivado is not required for CI. Kintex-7 structural TDL:
`python -m tidl_poc vivado-baseline` (12-case matrix) or
`python -m tidl_poc vivado-timing-clean` (64 CARRY4/channel scaling).
Re-parse with `--export-only`. Raw trees stay gitignored under `outputs/`.

## Repository map

- `docs/` requirements, analysis, competition evidence
- `docs/evidence/vivado_kintex7/` Round-6 structural snapshot (wide parity observability)
- `docs/evidence/vivado_kintex7_timing_clean/` timing-clean @64 CARRY4/channel
- `references/` bibliography (no paywalled PDFs)
- `simulations/` experiment entry points
- `src/tidl_poc/` models and CLI
- `spice/` LTspice testbench + runner (results under gitignored `outputs/spice_adcmp580/`)
- `rtl/` original Kintex-7 CARRY4 TDL under `rtl/tdc/kintex7/` plus scaffolding
- `tb/` arithmetic/protocol testbenches
- `constraints/` family folders (no fake timing numbers)
- `tests/` unit tests

## Licence and safety

All rights reserved: [LICENSE-NOTICE.md](LICENSE-NOTICE.md). Do not commit
credentials, personal data, challenge screenshots, or paper PDFs.
