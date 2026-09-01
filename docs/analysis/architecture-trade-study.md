# Architecture trade study

Classification of scores below: **literature evidence** and **engineering judgement
at TRL 2**. No local FPGA implementation evidence exists.

Scoring is 1 (poor for this challenge) to 5 (strong for this challenge). Scores
are not measurements.

## Candidates

1. Single-chain TDL
2. Parallel multi-chain TDL (averaging and/or segmentation; Mao MCS is a published variant)
3. Wave Union / multisampling
4. Multi-chain + Wave Union hybrid
5. DDMTD (auxiliary periodic-clock mode only)

Measurement inputs are 1 PPS **events** (S5). A periodic-only interpolator cannot
be the primary path.

## Criteria

| Criterion | Why it matters |
| --- | --- |
| Resolution potential | S14 1 ps is a physical-resolution target, not a counter LSB |
| Single-shot precision | S14 20 ps precision; front-end still extra |
| DNL/INL sensitivity | Code-density calibration load |
| Temperature sensitivity | 10–40 °C required |
| Placement complexity | 12-month POC risk |
| Calibration complexity | Online/periodic PVT |
| FPGA resource use | 16 channels in a basic-tier Kintex |
| 16-channel scalability | S7 simultaneous preferred |
| Throughput | 1 PPS is easy; calibration traffic is not |
| Maturity in literature | What can be cited honestly |
| Arbitrary events | S5 |
| Periodic clock characterisation | Optional factory/self-test |
| 12-month POC implementation risk | TRL 6 path |

## Scores

| Criterion | Single TDL | Multi-chain | Wave Union | Hybrid | DDMTD |
| --- | --- | --- | --- | --- | --- |
| Resolution potential | 2 | 4 | 5 | 5 | 3 |
| Single-shot precision | 2 | 4 | 4 | 5 | 2 |
| DNL/INL sensitivity | 2 | 3 | 3 | 3 | 4 |
| Temperature sensitivity | 2 | 4 | 3 | 4 | 3 |
| Placement complexity | 4 | 3 | 2 | 1 | 3 |
| Calibration complexity | 3 | 3 | 2 | 1 | 3 |
| FPGA resource use | 5 | 3 | 3 | 2 | 4 |
| 16-channel scalability | 4 | 3 | 3 | 2 | 2 |
| Throughput | 4 | 4 | 3 | 3 | 2 |
| Maturity in literature | 5 | 4 | 4 | 2 | 4 |
| Arbitrary events | 5 | 5 | 5 | 5 | 1 |
| Periodic clock characterisation | 3 | 3 | 3 | 3 | 5 |
| 12-month POC risk (5 = lower risk) | 5 | 4 | 3 | 2 | 4 |

Notes behind scores:

- Single-chain: Mao 2022 8.7 ps SSP / 11.4 ps resolution on Kintex-7 is **authors'
  result**, already eating a large fraction of a 20 ps *system* budget once
  front-end and PVT are added (see error-budget conservative scenario).
- Multi-chain: Mao 2022 4.6 ps SSP / 1.3 ps resolution (literature) plus a
  common-mode floor in the 1/N fit. Huang 2026 also reports parallel carry
  chains beating single-chain and beating DDMTD on their periodic tests.
  Resource cost scales with N × channels.
- Wave Union: Kwiatkowski 2023 shows subpicosecond *quoted resolution* on 28 nm;
  Ratners 2026 shows WU temperature behaviour on **flash** FPGAs, not Kintex.
  Placement and bubble handling are harder (Wu; Kwiatkowski bubble-proof work).
- Hybrid: literature maturity of a *combined* 16-channel instrument in 12 months
  is weak. Highest placement and calibration risk. Not scored as the winner.
- DDMTD: Huang 2026 error ranges on their periodic test were tens of picoseconds
  for DDMTD versus a few picoseconds for the TDC. DDMTD also needs a periodic
  beat. Score 1 for arbitrary 1 PPS events.

## 12-month weighted reading

If 16-channel event timestamping, calibration, and a rack POC dominate, **parallel
multi-chain TDL is the baseline hypothesis to implement first**. Wave Union remains
the main alternative if measured single-chain/multi-chain SSP cannot close the
20 ps system budget. Hybrid is a research path, not the first POC architecture.
DDMTD is retained as an auxiliary mode for 10 MHz characterisation and factory
test, not as the measurement path.

This recommendation follows the table. It is not a claim that multi-chain meets
S14 on the unselected FPGA.

**First Vivado baseline (decision, not evidence):** Kintex-7 / CARRY4, 8 chains
per channel, synthesis scaling 1 → 4 → 8 → 16. Wave Union is a second branch
after resource/timing reports. Details:
[vivado-baseline-decision.md](vivado-baseline-decision.md).

## What would change the recommendation

- Resource estimates after a part is selected showing 16 × N-chain TDL does not
  fit the 3U board’s FPGA.
- A measured front-end already consuming >10 ps RMS, forcing a finer TDC.
- POC staffing that already includes Wave Union place-and-route expertise.

RTL in this repository keeps family-specific carry primitives behind interfaces
so A/B/C can still be swapped without rewriting the combiner, logger, or UTC
block.
