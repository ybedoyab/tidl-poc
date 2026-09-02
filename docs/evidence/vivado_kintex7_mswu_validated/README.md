# Kintex-7 MSWU-inspired structural evidence (Round 9 validated)

**Classification:** RTL/synthesis/implementation evidence.
**Part:** `xc7k160tffg676-2`. **Vivado:** 2026.1.

Round 8's nominal 1-channel preencoder LUT result was not a valid measure of the intended preencoder logic because benchmark outputs were not retained and only subregion 0 was selected. Round 9 corrects benchmark observability and exercises all MBD=5 regions.

Round 8 historical snapshot preserved at `docs\evidence\vivado_kintex7_mswu_structural/`.
Round 8 `mswu_structural_1ch_preencoder` LUT=3 is **superseded** for preencoder resource claims.

This is a project-authored structural/resource surrogate informed by published MSWU-B architecture. Vivado does not validate Wave Union pulse generation, picosecond bin widths, DNL, SSP, accuracy, or temperature behavior.

## Round 9 local cases

| case_id | role |
| --- | --- |
| `mswu_1ch_core_r9` | 1× TDL + 4 capture banks |
| `mswu_1ch_preenc_seq_r9` | + low-rate sequential MBD=5 scanner (all 5 regions) |
| `mswu_1ch_preenc_parallel_r9` | + parallel 4×5 region encoders (upper bound) |
| `mswu_lowrate_16ch_frontends_r9` | 16 independent front-ends + pipelined shared post |

## Comparison (structural resources only — not metrology)

| Architecture | Source | CARRY4 | FF | LUT | Slices | WNS | Route |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8-chain multichain R7 16ch | local Round 7 | 8192 | 32800 | 21547 | 13669 | 3.045 ns | fully_routed |
| MSWU validated 16ch | local Round 9 | 800 | 13112 | 1038 | 2935 | 0.162 | fully_routed |
| Kwiatkowski 2023 1ch complete | literature | n/a | 1165 | 2840 | 953 | n/a | n/a |

**No architecture selected solely from Vivado resource evidence.**

## Reproduce

```text
python -m tidl_poc vivado-mswu-validated
python -m tidl_poc vivado-mswu-validated --export-only
```

Raw Vivado trees: gitignored `outputs/vivado_kintex7_mswu_validated/`.
