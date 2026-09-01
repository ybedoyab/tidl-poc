# ADCMP580 SPICE characterization

Status: TRL 2. This document separates three evidence classes. It is **not**
S14 compliance and **not** laboratory measurement.

Command: `python scripts/ltspice/run_adcmp580.py --all`

Committed testbench: `spice/adcmp580/tidl_adcmp580_characterization.asc`
(original project schematic; references the locally installed ADCMP580 symbol
by name). Analog Devices model/library files are not in Git.

Latch disable/compare-mode wiring was taken from the **installed official
example** (`LE = 0.4 V`, `_LE = 0`, `VTT = GND`). HYS is left open (datasheet
zero-hysteresis). VTP and VTN go to GND so the internal 50 ohm terminations
are used. Q and QB each have 50 ohm to ground. No extra shunt 50 ohm on VP.

## 1. Manufacturer literature (not this project)

ADCMP580/581/582 Rev. B and the Analog Devices product page:

- Typical propagation delay 180 ps
- Detailed dispersion discussion: <25 ps over overdrive 5 mV to 500 mV and
  slew 1 V/ns to 10 V/ns
- Some overview text: typical <15 ps — do not collapse into one number
- Random jitter 200 fs RMS (not extracted from these deterministic transients)
- Deterministic jitter 10 ps
- CML intended to drive about 400 mV into 50 ohm to ground
- Input range −2 V to +3 V with ±5 V supplies

## 2. Local LTspice simulation result

Classification: **SPICE/front-end simulation**.
LTspice 26.0.2, project netlist/testbench, official ADCMP580 macromodel.

Gitignored machine copy: `outputs/spice_adcmp580/summary.json` (full grid, `--all`).

Dispersion grid (overdrive 5–500 mV, slew 1–10 V/ns, rise and fall; 56/56 cases
switched; Q−QB settled at ±0.4 V):

| Quantity | SPICE value |
| --- | --- |
| Mean tpd | 203.0 ps |
| Min tpd | 191.5 ps |
| Max tpd | 210.0 ps |
| max(tpd)−min(tpd) | 18.6 ps |
| Differential output 20–80% (Q−QB) | ~42.4 ps |

Cross-check vs literature (not forced to match):

- Datasheet typical tpd 180 ps. Sim mean − 180 ps = **+23.0 ps**.
- Detailed datasheet dispersion bound <25 ps over this overdrive/slew window:
  sim 18.6 ps is below that bound.
- Overview typical <15 ps: sim 18.6 ps is **above** that wording.
- Datasheet typical output rise/fall 37 ps; this bench measures ~42.4 ps on
  V(Q)−V(QB) 20–80%, a different definition.

Rise-time sensitivity at engineering amplitude 0.4 V / threshold 0 V (not a
challenge 1 PPS spec); 12/12 cases switched. tpd stayed near ~200 ps for
100 ps–1 ns edges and increased for 2 ns and 5 ns edges (about 225 ps rise /
257 ps fall at 5 ns). One 500 ps falling point was 165 ps; it is reported, not
discarded.

Random jitter was **not** inferred. 200 fs RMS remains manufacturer literature.

Macromodel limitations:

- No package, SMA, or PCB interconnect
- No CML-to-Kintex-7 receiver
- Deterministic transients only


## 3. Challenge-specific gaps

- Actual 1 PPS amplitude / edge is not given
- CML-to-Kintex-7 interface is not in this SPICE bench
  ([cml-to-kintex7-interface-options.md](cml-to-kintex7-interface-options.md))
- Connector/PCB/transmission-line parasitics are absent
- Hardware validation is absent
