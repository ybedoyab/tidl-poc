# First Vivado baseline (Kintex-7 structural TDC)

Status: **TRL 2**. Classification: **RTL/synthesis/implementation evidence**.

This is not laboratory timing, not TDC bin widths, not 1 ps resolution, not DNL,
not SSP, and not accuracy. Meeting a 4 ns capture-clock period does **not**
prove asynchronous CARRY4 taps are picosecond-accurate.

## Decision (unchanged architecture branch)

| Item | Choice | Why now |
| --- | --- | --- |
| FPGA family / carry primitive | Kintex-7 / CARRY4 | Lowest 12-month implementation risk; Mao 2022 literature anchors are Kintex-7 MCS, used only as a fitted model |
| Fine TDC | 8 parallel chains per channel | First branch; chain count is parameterized |
| Channel scaling | 1 → 4 → 8 → 16 | Matches S7 preferred simultaneous path |
| TDL length | Sweep 32 / 48 / 64 CARRY4 per chain | Must cover a coarse-clock phase window; route/cell delays are device-dependent; no local measurement exists. No length is claimed sufficient for a 1 ps TDC |
| Wave Union / MSWU-B | High-upside **second** branch | After 1/4/8/16 multichain reports; original structural RTL only |

Part used for this study: **`xc7k160tffg676-2`**, Vivado **2026.1**.
The runner still queries installed Kintex-7 parts (`get_parts`) and prefers
speed-grade `-2` / XC7K160 for literature comparability with Kwiatkowski 2023.

Runner: `python scripts/vivado/run_kintex7_baseline.py` (not a CI dependency).
Machine paths stay in gitignored `outputs/vivado_kintex7/local_paths.json`.
Tracked claims quote [docs/evidence/vivado_kintex7/](../evidence/vivado_kintex7/).

## Local matrix (2026.1, XC7K160T)

12 synthesis cases attempted; all 12 mapped the expected CARRY4 count
(`channels × 8 × carry4_per_chain`). Implementation: 6 succeeded, 0 failed,
6 skipped (4/8/16-channel at 32 and 48 CARRY4/chain). No bitstream. No board
pins assigned.

| channels | CARRY4/chain | synth | impl | CARRY4 | FF | LUT | Slices | WNS ns | route |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 32 | ok | ok | 256 | 1027 | 218 | 416 | +0.144 | fully_routed |
| 1 | 48 | ok | ok | 384 | 1539 | 320 | 560 | +0.102 | fully_routed |
| 1 | 64 | ok | ok | 512 | 2051 | 416 | 711 | −0.116 | fully_routed |
| 4 | 32 | ok | skipped | 1024 | 4105 | 874 | n/a | n/a | n/a |
| 4 | 48 | ok | skipped | 1536 | 6153 | 1290 | n/a | n/a | n/a |
| 4 | 64 | ok | ok | 2048 | 8201 | 1658 | 2611 | −0.286 | fully_routed |
| 8 | 32 | ok | skipped | 2048 | 8209 | 1747 | n/a | n/a | n/a |
| 8 | 48 | ok | skipped | 3072 | 12305 | 2579 | n/a | n/a | n/a |
| 8 | 64 | ok | ok | 4096 | 16401 | 3322 | 5319 | −0.553 | fully_routed |
| 16 | 32 | ok | skipped | 4096 | 16417 | 3492 | n/a | n/a | n/a |
| 16 | 48 | ok | skipped | 6144 | 24609 | 5156 | n/a | n/a | n/a |
| 16 | 64 | ok | ok | 8192 | 32801 | 6635 | 10980 (43.3%) | −1.240 | fully_routed |

Placement from LOC text (not a GUI screenshot): 1-channel cases show 8
vertical carry chains, no scatter. The 16×64 case shows 128 chains, 128
vertical runs, 0 scattered.

## What the evidence is

- primitive count (CARRY4, FDRE)
- LUT / FF / slice usage vs independent structural formulas
- placement feasibility (vertical carry continuity vs scatter)
- routing completion
- control/capture timing under a 4 ns benchmark clock
- methodology / DRC notes related to carry and asynchronous hit

## What the evidence is not

Physical TDC bins, 1 ps resolution, DNL, SSP, accuracy, or temperature
behaviour. Post-route cell delays are not bin widths. Negative WNS from
1-channel / 64 CARRY4 onward is capture/control timing at the 4 ns
benchmark clock, not a TDC-bin measurement.

## Structural conclusion (not a metrology claim)

16 channels × 8 chains × 64 CARRY4 structurally fit and fully route in
XC7K160T. Resource scaling is approximately linear. 10,980 slices is 43.3%
of device slices. That **lowers implementation-capacity risk**. It does
**not** prove 1 ps resolution, DNL, SSP, accuracy, or temperature
performance. Do **not** select multichain vs MSWU-B from these results alone.

## Timing-clean benchmark (Round 7)

Round 6 exposed capture FFs through a **benchmark-only wide XOR parity tree**
(`chain_parity = ^captured_k`, hierarchical reduction to `tap_parity`). That
network is not part of the proposed metrology datapath and was the likely
source of negative 4 ns WNS from 1ch/64 upward in Round 6.

Round 7 removes the parity tree. Capture FFs are retained via `KEEP` /
`DONT_TOUCH`; the top registers one representative bit per channel. Same 4 ns
clock, same narrow false paths, timing-driven P&R for all channel counts.

Results: [docs/evidence/vivado_kintex7_timing_clean/](../evidence/vivado_kintex7_timing_clean/).
Round-6 snapshot is preserved in [docs/evidence/vivado_kintex7/](../evidence/vivado_kintex7/).

## Runner timeout anomaly

The first 16×64 Python parent hit a 10800 s `subprocess` timeout and recorded
`synth_status=failed` (returncode −1) while the Vivado child continued and
wrote complete reports (CARRY4=8192, implementation ok). The runner now kills
the process tree on timeout and reconciles status from both the subprocess
result and validated report markers. A leftover file is not treated as
success. See [docs/evidence/vivado_kintex7/README.md](../evidence/vivado_kintex7/README.md).

## Decision gate

Do **not** choose multichain or MSWU-B solely from synthesis. Resource and
implementation feasibility can lower 12-month risk. Metrological performance
still comes from literature until a physical POC.

## MSWU-inspired structural branch (second FPGA architecture)

Original project-authored RTL in `rtl/tdc/kintex7_mswu/`. Informed by
Kwiatkowski et al. 2023 (Measurement 209, 112510) at the architectural level
only — HDL is **not** copied from the paper or third parties. Wave Union pulse
generation is **not** validated by Vivado.

Runner: `python -m tidl_poc vivado-mswu-structural`.
Tracked snapshot: [docs/evidence/vivado_kintex7_mswu_structural/](../evidence/vivado_kintex7_mswu_structural/).

| case_id | CARRY4 | FF | LUT | Slices | WNS ns | Route | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `mswu_structural_1ch_core` | 50/50 | 801 | 3 | 155 (0.61%) | +3.536 | fully_routed | TDL + 4 capture banks |
| `mswu_structural_1ch_preencoder` | 50/50 | 849 | 3 | 155 (0.61%) | +3.536 | fully_routed | + MBD=5 pre-encoder surrogate |
| `mswu_lowrate_16ch_frontends` | 800/800 | 12835 | 1041 | 3002 (11.84%) | −1.109 | fully_routed | 16 independent front-ends; shared low-rate post; **timing not closed** |

Capture FF min: 800/channel (4×200 taps); 12800 @16ch — both met. CARRY4
formula: 50 per TDL (200 logical taps / 4 CO per CARRY4).

**Structural reading:** MSWU surrogate @16ch uses far fewer slices than
multichain Round 7 (3002 vs 13669), lowering resource extrapolation risk for
a single-TDL topology. The 16ch case failed the 4 ns synchronous benchmark;
that is not metrology but is an implementation-risk flag. Do **not** select
MSWU-B from these results alone.

See [architecture-trade-study.md](architecture-trade-study.md) and
`scripts/vivado/README.md`.
