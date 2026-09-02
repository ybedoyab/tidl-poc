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

| Pre-encoder modes | seq (1 scanner) / parallel (4×5) | Round 9 validated observability |

Vivado benchmarks: `python -m tidl_poc vivado-mswu-validated` (Round 9).

Tracked evidence:
- Round 8 historical: `docs/evidence/vivado_kintex7_mswu_structural/`
- Round 9 validated: `docs/evidence/vivado_kintex7_mswu_validated/`

Round 8 `mswu_structural_1ch_preencoder` LUT=3 was invalid (outputs open;
sub_sel hardwired to 0). Round 9 exercises all five MBD regions.
