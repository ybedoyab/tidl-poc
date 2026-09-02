# Vivado Kintex-7 structural baseline

These scripts do **not** run in CI and do not assume Vivado is installed.

Classification: **RTL/synthesis/implementation evidence**. Not physical TDC bins,
not 1 ps resolution, not DNL/SSP/accuracy. No bitstreams. No board pins.

## Evidence snapshots

| Directory | Content |
| --- | --- |
| `docs/evidence/vivado_kintex7/` | Round-6: 12-case matrix, wide parity observability |
| `docs/evidence/vivado_kintex7_timing_clean/` | Round-7: 1/4/8/16 @ 64 CARRY4, timing-clean observability |
| `docs/evidence/vivado_kintex7_mswu_structural/` | Round-8 MSWU structural (historical; preencoder LUT superseded) |
| `docs/evidence/vivado_kintex7_mswu_validated/` | Round-9 validated MSWU: observability fix, placement parser, pipelined 16ch |

Raw Vivado output stays gitignored under `outputs/vivado_kintex7/`,
`outputs/vivado_kintex7_timing_clean/`, `outputs/vivado_kintex7_mswu_structural/`,
and `outputs/vivado_kintex7_mswu_validated/`.

## Runners

**12-case matrix (Round 6 style parity benchmark on legacy RTL in `legacy/`):**

```text
python -m tidl_poc vivado-baseline
python -m tidl_poc vivado-baseline --export-only
```

**Timing-clean 64 CARRY4/channel scaling (current RTL):**

```text
python -m tidl_poc vivado-timing-clean
python scripts/vivado/run_kintex7_timing_clean.py
python -m tidl_poc vivado-timing-clean --export-only
```

The timing-clean flow synthesizes and place/routes channels {1,4,8,16} at
64 CARRY4/chain with timing-driven P&R. It validates mapped CARRY4 =
`channels × 8 × 64` and mapped FDRE ≥ `channels × 8 × 256`.

Round-6 negative WNS on larger cases was likely the benchmark-only wide parity
reduction tree, not the CARRY4 TDL structure. Round-7 removes that tree; see
the timing-clean evidence README for comparison.

**MSWU-inspired structural surrogate (second architecture branch):**

Round 8 (historical): `python -m tidl_poc vivado-mswu-structural`

Round 9 validated (corrected observability, placement parser, pipelined 16ch):

```text
python -m tidl_poc vivado-mswu-validated
python -m tidl_poc vivado-mswu-validated --export-only
```

RTL: `rtl/tdc/kintex7_mswu/`. Round 9 cases: `mswu_1ch_core_r9`,
`mswu_1ch_preenc_seq_r9`, `mswu_1ch_preenc_parallel_r9`,
`mswu_lowrate_16ch_frontends_r9`.
Wave Union pulse physics is **not** validated by Vivado.
Round 8 `mswu_structural_1ch_preencoder` LUT=3 is **superseded** — invalid
preencoder resource measurement.
