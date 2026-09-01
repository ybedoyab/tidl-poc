# Claims register

Use this table before putting a number in a submission. **Safe for submission as this
project's result** is `no` unless the work was done in this repository *and* the
classification is honest.

Resolution ≠ precision ≠ accuracy. Simulations are not measurements.

| ID | Claim | Source | Source type | Reproduced locally | Experimental or simulated | Safe as this project's result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | 1-chain FPGA TDC SSP = 8.7 ps RMS | Mao et al. 2022 DOI 10.3390/s22062306 | literature evidence | no | experimental (authors) | no | Kintex-7 MCS paper; not this FPGA. |
| C02 | 10-chain FPGA TDC SSP = 4.6 ps RMS | Mao et al. 2022 | literature evidence | no | experimental (authors) | no | Same paper. MCS, not simple 1/N averaging. |
| C03 | 10-chain resolution = 1.3 ps; 1-chain = 11.4 ps | Mao et al. 2022 | literature evidence | no | experimental (authors) | no | Resolution is not precision. |
| C04 | Resolution TC = 0.0002 ps/°C (25–70 °C) | Mao et al. 2022 | literature evidence | no | experimental (authors) | no | Applies to *resolution*, not residual timestamp error. Temperature span is not 10–40 °C. |
| C05 | Fitted σ_common, σ_independent from C01/C02 | this repo `parallel-chains` | model-based simulation | yes (closed-form fit) | simulated | yes, as a **literature-fitted model** only | Do not call it FPGA data. Sensitivity bands are not a CI. |
| C06 | Digital fine quantization = 1 ps | S14 requirement | requirement | n/a | n/a | as a **design target** only | Does not prove 1 ps physical resolution. |
| C07 | Signed ±1 s is arithmetically representable at 100–500 MHz coarse clocks | this repo `coarse-fine` | model-based simulation | yes | simulated | yes, as arithmetic feasibility | Not clock accuracy. |
| C08 | Combined system precision ≤ 20 ps RMS | S14 + error-budget scenarios | mixed | n/a | simulated allocations | no | Illustrative/target_allocation can sit near/under 20 ps precision RSS; conservative and stress fail. Non-literature terms are engineering allocations, not evidence. |
| C09 | Front-end jitter ≈ σ_v / slew | standard analog | engineering model | yes (formula) | simulated | as a **model**, not hardware | ADCMP580 is a tracked candidate, not selected. No SPICE results. |
| C10 | 16-channel covariance / crosstalk numbers | this repo `channel-scaling` | model-based simulation | yes | simulated | as a **model** | Offsets shared across activity; crosstalk is a sweep. |
| C11 | Code-density reduces reconstruction error on a 512-bin synthetic TDL | this repo `calibration` | model-based simulation | yes | simulated | as a **synthetic** result | Not an FPGA TDL. |
| C12 | PVT residual vs cal interval | this repo `pvt` | model-based simulation | yes | simulated | as a **time-domain state** + TC sweep | Residual is zero at each cal epoch. Does not use C04 as residual error. |
| C13 | UDP loss ≠ measurement loss if internal log intact | this repo `packet-logging` | model-based simulation | yes | simulated | as **data-path** evidence | Not a network certification. |
| C14 | UTC-valid / holdover flags | this repo `reference-clock` | model-based simulation | yes | simulated | as **state-machine** evidence | No UTC accuracy claim. |
| C15 | FPGA TDC <10 ps RMS, 48 channels | Bayer and Traxler 2011 | literature evidence | no | experimental (authors) | no | Different device generation. |
| C16 | 19 ps precision, 170 MSa/s FPGA TDC | Zhang et al. 2022 | literature evidence | no | experimental (authors) | no | |
| C17 | Subpicosecond MSWU type B on Kintex-7 XC7K160 | Kwiatkowski et al. 2023 DOI 10.1016/j.measurement.2023.112510 | literature evidence | no | experimental (authors) | no | Mean MSWU resolution ~0.4 ps; TCL 10.5/10.51 ps; WU one register 2.15 ps. Manual P&R; aggressive timing usage is an implementation risk, not a default. |
| C18 | Carry-chain TDC vs DDMTD comparison | Huang et al. 2026 | literature evidence | no | experimental (authors) | no | Supports DDMTD as auxiliary mode. |
| C19 | Wave Union temperature stability (flash FPGA) | Ratners et al. 2026 | literature evidence | no | experimental (authors) | no | Not Kintex-7 / UltraScale. |
| C20 | UltraScale TDL implementation guidance | Morabito et al. 2024 | literature evidence | no | experimental (authors) | no | |
| C21 | 20 ps FPGA TDC with temperature correction | Pan et al. 2014 | literature evidence | no | experimental (authors) | no | Do not equate to S14 compliance. |
| C22 | This project is TRL 3+ | — | — | — | — | **no** | TRL 2 only. |
| C23 | This project has laboratory / FPGA timing data | — | — | — | — | **no** | None. |
| C24 | BOM prices, MTBF, 10-year demonstrated life | — | — | — | — | **no** | 10-year figure is a design target. |
| C25 | RTL TDC is accurate to 1 ps | rtl stubs | — | — | — | **no** | Family primitives are TODOs. A behavioural delay line is not a TDC. |
| C26 | 20 ps over 1 s ⇔ y = 2e-11 | this repo `reference-stability` | model-based simulation | yes | simulated | as a **first-order allocation** only | `delta_t = y * tau`. Not ADEV proof. |
| C27 | 8-chain literature-fitted SSP in `target_allocation` | Mao fit via `parallel-chains` | model-based simulation | yes (closed-form) | simulated | as a **literature-fitted model** only | Used as the first Vivado baseline chain count. Not this FPGA. |
| C28 | Ch1/Ch2 mean LSB 407/401 fs; eq. res. 546/494 fs; max bins 2.83/1.54 ps | Kwiatkowski et al. 2023 | literature evidence | no | experimental (authors) | no | Low LSB is not low INL (INL before correction ~89.25/80.76 ps). |
| C29 | Interval std generally <4 ps (1 ns–500 µs); up to 5.2 ps near 10 ns; best split 2.6 ps | Kwiatkowski et al. 2023 | literature evidence | no | experimental (authors) | no | SSP defined as interval std / sqrt(2). |
| C30 | Temp-specific recal: split <3 ps over 0–40 °C (SSP <2.1 ps); without recal, precision collapses | Kwiatkowski et al. 2023 | literature evidence | no | experimental (authors) | no | Do not interpolate between temperatures. |
| C31 | Channel offset 21 ps over 0–40 °C = 0.525 ps/°C | Kwiatkowski et al. 2023 | literature evidence | no | experimental (authors) | no | Extra PVT scenario only; not this board. |
| C32 | Table 1/2 XC7K160 resources (core, pre-encoders, 2840 LUT / 1165 FF / 953 slices / 21.5 BRAM per channel; 2-ch 6.22% LUT / 13.23% BRAM) | Kwiatkowski et al. 2023 | literature evidence | no | experimental (authors) | no | Do not treat as our architecture. High-rate FIFOs. |
| C33 | Naive 16 × paper channel: LUT/slices <100% inferred XC7K160; naive BRAM exceeds ~325 BRAM | this repo `mswu-literature` | model-based simulation | yes (arithmetic) | simulated | as **naive scaling arithmetic** only | Does **not** prove 16 channels cannot fit. Capacities derived from paper percentage rounding. |
| C34 | 16 events/s vs 140 MSa/s resource-saving pre-encoder | this repo `mswu-literature` vs Kwiatkowski Table 1 | mixed | arithmetic vs literature Fmax | simulated interpretation | as **challenge-rate interpretation** only | No fake final BRAM. FIFO reduction is a hypothesis. |
| C35 | For intervals longer than hundreds of µs, reference-clock stability dominated precision | Kwiatkowski et al. 2023 | literature evidence | no | experimental (authors) | no | Qualitative support for 1 s reference allocation. Do not derive ADEV. |
| C36 | ADCMP580: 200 fs RMS RJ, 10 ps DJ, ~15–25 ps overdrive/slew dispersion (table-dependent), 180 ps tpd, 50 ohm inputs | Analog Devices ADCMP580/581/582 Rev. B + product page | external component evidence | no | manufacturer datasheet | no | Candidate only. DJ/dispersion can consume the 20 ps target. No CML-to-Kintex-7 evidence. No SPICE results. |
| C37 | ADCMP572: 150 ps tpd, 200 fs RJ, 10 ps DJ, 15 ps overdrive/slew dispersion, 50 ohm input | Analog Devices ADCMP572 datasheet | external component evidence | no | manufacturer datasheet | no | Datasheet-level comparison only; LTspice not required. |

Update this register when a number is added to `docs/` or a paper is quoted.
