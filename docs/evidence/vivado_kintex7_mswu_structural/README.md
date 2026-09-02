# Kintex-7 MSWU-inspired structural evidence

**Classification:** RTL/synthesis/implementation evidence.
**Part:** `xc7k160tffg676-2`. **Vivado:** 2026.1.

Original project-authored structural surrogate informed by Kwiatkowski et al. 2023
(Measurement 209, 112510). HDL is **not** copied from the paper or third parties.
Wave Union pulse generation is **not** validated by Vivado.

This is a project-authored structural/resource surrogate informed by published MSWU-B architecture. Vivado does not validate Wave Union pulse generation, picosecond bin widths, DNL, SSP, accuracy, or temperature behavior.

## Local cases

| case_id | role |
| --- | --- |
| `mswu_structural_1ch_core` | 1× TDL + 4 capture banks |
| `mswu_structural_1ch_preencoder` | + MBD=5 pre-encoder surrogate |
| `mswu_lowrate_16ch_frontends` | 16 independent front-ends + shared low-rate post |

Front-ends are never shared between simultaneous channels; only post-capture
processing may be serialized at 16 events/s.

## Comparison (structural resources only — not metrology)

| Architecture | Source | CARRY4 | FF | LUT | Slices | WNS | Route |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8-chain multichain R7 16ch | local Round 7 | 8192 | 32800 | 21547 | 13669 | 3.045 ns | fully_routed |
| MSWU surrogate 16ch | local this snapshot | 800 | 12835 | 1041 | 3002 | -1.109 | fully_routed |
| Kwiatkowski 2023 1ch complete | literature | n/a | 1165 | 2840 | 953 | n/a | n/a |

**No architecture selected solely from Vivado resource evidence.**

## Round 9 supersession

Round 9 validated evidence supersedes the Round 8 **1-channel preencoder LUT=3**
result for preencoder resource claims. See
[docs/evidence/vivado_kintex7_mswu_validated/](../vivado_kintex7_mswu_validated/).

Round 8 `mswu_structural_1ch_preencoder` had benchmark observability issues
(outputs open; `sub_sel` hardwired to 0). Historical numbers remain in this
directory unchanged.

## Reproduce

```text
python -m tidl_poc vivado-mswu-structural
python -m tidl_poc vivado-mswu-structural --export-only
```

Raw Vivado trees: gitignored `outputs/vivado_kintex7_mswu_structural/`.
