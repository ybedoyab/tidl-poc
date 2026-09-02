# Kintex-7 MSWU-inspired structural branch

Original project-authored SystemVerilog informed by Kwiatkowski et al. 2023
(Measurement 209, 112510). **Not** copied HDL. **Not** validated Wave Union
pulse physics.

Classification: RTL/synthesis/implementation evidence only.

| Constant | Value | Note |
| --- | --- | --- |
| Logical TDL taps | 200 | Paper anchor |
| CARRY4 per TDL | 50 | 200 CO taps ÷ 4 per CARRY4 |
| Capture banks | 4 | Four 200-bit sampling registers |
| MBD partitions | 5 × 40 bits | Bubble-resistant decomposition surrogate |
| Pre-encoder output | 11 bits/bank | Project surrogate, not paper bit-equivalence |

Vivado benchmarks: `python -m tidl_poc vivado-mswu-structural`.

Tracked evidence: `docs/evidence/vivado_kintex7_mswu_structural/`.
