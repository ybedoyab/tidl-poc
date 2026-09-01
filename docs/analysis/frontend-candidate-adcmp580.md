# Front-end candidate: ADCMP580

Status: TRL 2. **External component evidence** from Analog Devices materials.
Not a selected BOM part. Not SPICE results. Not S14 compliance.

Product page: <https://www.analog.com/en/products/adcmp580.html>
Datasheet: ADCMP580/581/582 Rev. B.

Classification of every number below: datasheet / manufacturer literature,
not this project's measurement.

## Why it is a candidate

- 50 ohm high-speed threshold front-end (S2/S4/S6 class)
- Analog Devices states the ADCMP580 model is available in LTspice
- quoted random jitter is much smaller than the 5 ps front-end allocation in
  `target_allocation`

It is **not** claimed to close the 20 ps system budget.

## ADCMP580 facts (Rev. B / product page)

| Item | Value | Context |
| --- | --- | --- |
| Production status | In production | Product page |
| Output family | CML | Comparator output, not FPGA I/O |
| Propagation delay | 180 ps | Datasheet typical |
| Equivalent input bandwidth | 8 GHz | Datasheet |
| Minimum pulse width | 100 ps | Datasheet |
| Output rise/fall | 37 ps typical | Datasheet |
| Random jitter | 200 fs RMS | Datasheet; do not mix with DJ/dispersion |
| Deterministic jitter | 10 ps | Datasheet; separate from random jitter |
| Overdrive / slew-rate dispersion | roughly 15 ps to 25 ps depending on which datasheet table row is quoted | Keep the table context; **do not** collapse into the 200 fs RMS figure |
| Input range | −2 V to +3 V | With ±5 V supplies |
| Input termination | on-chip 50 ohm at both inputs | Datasheet |
| PSRR | >70 dB | Datasheet |
| LTspice | ADCMP580 model listed as available | Product page |

## Explicit flags (not solved)

- Deterministic jitter and overdrive/slew-rate dispersion can be comparable to
  the whole 20 ps challenge target. Random jitter of 200 fs RMS does not bound
  those terms.
- CML-to-Kintex-7 I/O must be designed and verified (level, common mode,
  termination). No interface evidence exists here.
- Challenge 1 PPS amplitude, rise time, and threshold remain unspecified.
  Do not assume a challenge waveform.
- No compliance claim. No SPICE result until the owner runs LTspice and the
  output is classified as SPICE/front-end simulation.

Workflow (no schematic committed yet): [../../spice/adcmp580/README.md](../../spice/adcmp580/README.md).

## ADCMP572 datasheet-level comparison (not a required LTspice model)

Source: Analog Devices ADCMP572/ADCMP573 datasheet facts as given for this
package. External component evidence only. An LTspice model is **not** required
for ADCMP572.

| Item | ADCMP580 | ADCMP572 |
| --- | --- | --- |
| Propagation delay | 180 ps | 150 ps |
| Random jitter | 200 fs RMS | 200 fs RMS |
| Deterministic jitter | 10 ps | 10 ps |
| Overdrive/slew-rate dispersion | quote 15–25 ps from the relevant ADCMP580 table row | 15 ps |
| Input termination | 50 ohm both inputs | 50 ohm input |

Faster delay does not imply a closed error budget. Dispersion and deterministic
jitter remain first-class versus a 20 ps system target.

See also [frontend-jitter.md](frontend-jitter.md).
