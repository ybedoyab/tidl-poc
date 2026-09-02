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

See [architecture-trade-study.md](architecture-trade-study.md) and
`scripts/vivado/README.md`.
