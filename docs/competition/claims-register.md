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
| C09 | Front-end jitter ≈ σ_v / slew | standard analog | engineering model | yes (formula) | simulated | as a **model**, not hardware | No comparator selected. No SPICE. |
| C10 | 16-channel covariance / crosstalk numbers | this repo `channel-scaling` | model-based simulation | yes | simulated | as a **model** | Offsets shared across activity; crosstalk is a sweep. |
| C11 | Code-density reduces reconstruction error on a 512-bin synthetic TDL | this repo `calibration` | model-based simulation | yes | simulated | as a **synthetic** result | Not an FPGA TDL. |
| C12 | PVT residual vs cal interval | this repo `pvt` | model-based simulation | yes | simulated | as a **time-domain state** + TC sweep | Residual is zero at each cal epoch. Does not use C04 as residual error. |
| C13 | UDP loss ≠ measurement loss if internal log intact | this repo `packet-logging` | model-based simulation | yes | simulated | as **data-path** evidence | Not a network certification. |
| C14 | UTC-valid / holdover flags | this repo `reference-clock` | model-based simulation | yes | simulated | as **state-machine** evidence | No UTC accuracy claim. |
| C15 | FPGA TDC <10 ps RMS, 48 channels | Bayer and Traxler 2011 | literature evidence | no | experimental (authors) | no | Different device generation. |
| C16 | 19 ps precision, 170 MSa/s FPGA TDC | Zhang et al. 2022 | literature evidence | no | experimental (authors) | no | |
| C17 | Subpicosecond WU type B on 28 nm FPGA | Kwiatkowski et al. 2023 | literature evidence | no | experimental (authors) | no | High implementation complexity. |
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

Update this register when a number is added to `docs/` or a paper is quoted.
