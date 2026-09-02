# Architecture trade study

Classification of scores below: **literature evidence** and **engineering judgement
at TRL 2**. Local Kintex-7 CARRY4 work is **RTL/synthesis/implementation
evidence** only (resource, placement, route, control-clock timing). It is not
physical timing measurement and does not choose the architecture on metrology.

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

Do not force either branch to win. Do **not** choose multichain or MSWU-B
solely from synthesis. Resource and place/route feasibility can lower
12-month risk. Metrological performance (resolution, DNL, SSP, accuracy)
still comes from literature until a physical POC.

The first 1 / 4 / 8 / 16 **multichain** Vivado 2026.1 reports exist
([docs/evidence/vivado_kintex7/](../evidence/vivado_kintex7/) Round 6;
[docs/evidence/vivado_kintex7_timing_clean/](../evidence/vivado_kintex7_timing_clean/)
Round 7). A 16-channel, eight-chain, 64-CARRY4 topology mapped 8192 CARRY4
and fully routed on XC7K160T at 13,669 slices (53.92% in Round 7). That is
structural/resource feasibility only.

An **original MSWU-inspired structural branch** now exists
([docs/evidence/vivado_kintex7_mswu_structural/](../evidence/vivado_kintex7_mswu_structural/),
RTL in `rtl/tdc/kintex7_mswu/`). HDL is project-authored; Wave Union pulse
physics is **not** validated by Vivado. Do not freeze TDL length as
“enough for 1 ps”. Do not pick a branch from these reports alone.

### Local structural comparison (not metrology)

| Architecture | Evidence class | Channels | CARRY4 | FF | LUT | Slices | BRAM | Route | WNS (local) | Metrology claim allowed? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8-chain multichain Round 7 | local RTL/synth/impl | 16 | 8192 | 32800 | 21547 | 13669 (53.92%) | 0 | fully_routed | +3.045 ns | **no** — structural only |
| MSWU structural surrogate 16ch low-rate | local RTL/synth/impl R8 | 16 | 800 | 12835 | 1041 | 3002 (11.84%) | 0 | fully_routed | −1.109 ns | **no** — R8; timing not closed |
| MSWU validated 16ch low-rate R9 | local RTL/synth/impl R9 | 16 | 800 | 13112 | 1038 | 2935 (11.58%) | 0 | fully_routed | +0.162 ns | **no** — pipelined post; WU pulse not validated |
| MSWU validated 1ch seq preenc R9 | local RTL/synth/impl R9 | 1 | 50 | 1274 | 434 | 396 (1.56%) | 0 | fully_routed | +0.221 ns | **no** — project surrogate |
| MSWU structural 1ch + pre-encoder | local RTL/synth/impl R8 | 1 | 50 | 849 | **3** | 155 (0.61%) | 0 | fully_routed | +3.536 ns | **no** — **superseded** (LUT=3 invalid) |
| Kwiatkowski 2023 complete channel | literature | 1 | n/a | 1165 | 2840 | 953 | 21.5 | n/a | n/a | **no** — authors' FPGA, manual P&R |
| Kwiatkowski 2023 two-channel full | literature | 2 | n/a | 2998 | 6304 | 2184 | 43 | n/a | n/a | **no** |

**Reading:** Round 8 MSWU 1ch preencoder LUT=3 is **invalid** (outputs open;
`sub_sel` hardwired to 0). Round 9 sequential preencoder: **434 LUT** (all five
MBD regions exercised). At 16 channels MSWU validated uses far fewer slices than
multichain Round 7 (2935 vs 13669), lowering resource extrapolation risk. Round 9
pipelined shared post **closes** the 4 ns synchronous benchmark (WNS +0.162 ns);
that reduces synchronous post-processing implementation risk but does **not**
reduce Wave Union physical launcher, calibration, or manual placement risk.
**No architecture selected solely from Vivado resource evidence.**

### Decision-oriented reading (not a winner)

| Branch | Structural resource | 16ch 4 ns benchmark | Complexity / risk |
| --- | --- | --- | --- |
| Multichain R7 | Higher (13669 slices, 8192 CARRY4) | Closed (+3.045 ns) | Lower pulse-launch / algorithmic complexity; eight chains per channel |
| MSWU validated R9 | Lower (2935 slices, 800 CARRY4) | Closed (+0.162 ns) | Literature sub-ps precedent; Wave Union launcher, calibration, manual P&R sensitivity remain |

Multichain remains the lower-complexity baseline hypothesis. MSWU-inspired
structural evidence lowers FPGA resource extrapolation risk and (after Round 9)
shows synchronous post-processing can close at 16 channels — still not metrology.

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

**First Vivado baseline:** Kintex-7 / CARRY4, 8 chains per channel, channel
scaling 1 → 4 → 8 → 16, TDL length sweep 32/48/64 CARRY4 per chain.
Vivado 2026.1 on `xc7k160tffg676-2` mapped and fully routed the 16×8×64
topology (10,980 slices, 43.3%). Implementation evidence is structural
only. Details: [vivado-baseline-decision.md](vivado-baseline-decision.md).

## What would change the recommendation

- Resource estimates after a part is selected showing 16 × N-chain TDL does not
  fit the 3U board’s FPGA.
- A measured front-end already consuming >10 ps RMS, forcing a finer TDC.
- POC staffing that already includes Wave Union place-and-route expertise.
- The decision-gate comparison after 1/4/8/16 multichain reports plus the
  MSWU structural surrogate (done); physical POC metrology still required.

RTL in this repository keeps family-specific carry primitives behind interfaces
so A/B/C can still be swapped without rewriting the combiner, logger, or UTC
block.
