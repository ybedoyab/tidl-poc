# Architecture trade study

Classification of scores below: **literature evidence** and **engineering judgement
at TRL 2**. No local FPGA implementation evidence exists.

Scoring is 1 (poor for this challenge) to 5 (strong for this challenge). Scores
are not measurements.

## Candidates

1. Single-chain TDL
2. Parallel multi-chain TDL (averaging and/or segmentation; Mao MCS is a published variant)
3. Wave Union / multisampling (MSWU type B as a named high-upside branch)
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
- Wave Union / MSWU-B: Kwiatkowski et al. 2023 report a working Kintex-7
  (XC7K160) MSWU type B timestamp interpolator with ~0.4 ps mean resolution
  and interval standard deviation generally <4 ps over the authors' 1 ns to
  500 µs tests (up to 5.2 ps near 10 ns). Those figures are **literature
  evidence**, not this project's FPGA result. Placement, Wave Union launchers,
  bubble handling, and aggressive timing usage raise 12-month risk.
- Hybrid: literature maturity of a *combined* 16-channel instrument in 12 months
  is weak. Highest placement and calibration risk. Not scored as the winner.
- DDMTD: Huang 2026 error ranges on their periodic test were tens of picoseconds
  for DDMTD versus a few picoseconds for the TDC. DDMTD also needs a periodic
  beat. Score 1 for arbitrary 1 PPS events.

## Two-branch comparison (neither forced to win)

Keep the first Vivado baseline. Add MSWU-B as a **high-upside second branch**.

### Branch A — 8-chain multichain TDL (first Vivado baseline)

Kintex-7 / CARRY4, 8 parallel chains per channel, synthesis scaling
1 → 4 → 8 → 16. Decision record:
[vivado-baseline-decision.md](vivado-baseline-decision.md).

Pros:

- lower architectural risk than Wave Union launchers and multisampling
- straightforward event path
- good first resource-scaling baseline

This branch is **not** claimed to meet S14.

### Branch B — MSWU type B (high-upside second branch)

Backed by Kwiatkowski et al. 2023 (DOI 10.1016/j.measurement.2023.112510),
**literature evidence only**. The paper implements MSWU type B as a fine
interpolator in a timestamp architecture (`TS = N * Tclk − Tfine`; intervals are
timestamp differences) on XC7K160, 710 MHz from a 10 MHz TCXO via a frequency
synthesizer. Each MSWU TDC uses a 200-mux carry TDL, four 200-bit sampling
registers, Wave Union launcher B in START and launcher A in STOP. Manual
placement **and** routing were crucial. The authors intentionally operated at or
beyond some manufacturer-recommended timing usage; that is an implementation
risk, not a recommended default for this project.

Pros (authors' results, not ours):

- directly demonstrated ~0.4 ps mean resolution on Kintex-7
- <5.2 ps interval precision across the reported test range
- temperature-specific recalibration kept split-signal interval precision <3 ps
  over 0–40 °C
- exact Table 1 / Table 2 resource numbers from a working implementation

Risks:

- manual place-and-route is critical
- Wave Union launcher behaviour
- bubble handling (paper: MBD=5; five 40-bit sub-TDLs) and post-encoding
- intentionally aggressive / nonstandard FPGA timing usage
- resource scaling to 16 channels requires redesign (do not copy the paper's
  high-rate FIFOs; see [low-rate-16-channel-datapath.md](low-rate-16-channel-datapath.md)
  and `python -m tidl_poc sim mswu-literature`)
- calibration sensitivity (100,000-hit code density; without recalibration,
  MSWU precision deteriorated rapidly with temperature)

Do **not** copy the paper HDL. Any second-branch RTL must be an original
implementation or closest legally original structural approximation.

### Decision gate

Do not force either branch to win.

After the first 1 / 4 / 8 / 16 **multichain** Vivado reports exist, implement
**one** MSWU-B single-channel resource-only / structural branch (or the closest
legally original approximation), then compare resource use and implementation
risk.

Naive 16 × paper-channel BRAM arithmetic can exceed the XC7K160 total inferred
from Table 2 percentages. That does **not** prove 16 channels cannot fit.

## 12-month weighted reading

If 16-channel event timestamping, calibration, and a rack POC dominate,
**parallel multi-chain TDL remains the baseline hypothesis to implement first**.
MSWU-B remains the high-upside second branch if measured single-chain /
multi-chain SSP cannot close the 20 ps system budget, or if the post-Vivado
comparison favours it. Hybrid is a research path, not the first POC
architecture. DDMTD is retained as an auxiliary mode for 10 MHz characterisation
and factory test, not as the measurement path.

This recommendation follows the table and the two-branch gate. It is not a claim
that multi-chain or MSWU-B meets S14 on an unselected FPGA.

**First Vivado baseline (decision, not evidence):** Kintex-7 / CARRY4, 8 chains
per channel, synthesis scaling 1 → 4 → 8 → 16. Details:
[vivado-baseline-decision.md](vivado-baseline-decision.md).

## What would change the recommendation

- Resource estimates after a part is selected showing 16 × N-chain TDL does not
  fit the 3U board’s FPGA.
- A measured front-end already consuming >10 ps RMS, forcing a finer TDC.
- POC staffing that already includes Wave Union place-and-route expertise.
- The decision-gate comparison after 1/4/8/16 multichain reports plus one
  original MSWU-B structural channel.

RTL in this repository keeps family-specific carry primitives behind interfaces
so A/B/C can still be swapped without rewriting the combiner, logger, or UTC
block.
