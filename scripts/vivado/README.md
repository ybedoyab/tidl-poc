# Vivado Kintex-7 structural baseline

These scripts do **not** run in CI and do not assume Vivado is installed.

Classification: **RTL/synthesis/implementation evidence**. Not physical TDC bins,
not 1 ps resolution, not DNL/SSP/accuracy. No bitstreams. No board pins.

## Evidence snapshots

| Directory | Content |
| --- | --- |
| `docs/evidence/vivado_kintex7/` | Round-6: 12-case matrix, wide parity observability |
| `docs/evidence/vivado_kintex7_timing_clean/` | Round-7: 1/4/8/16 @ 64 CARRY4, timing-clean observability |

Raw Vivado output stays gitignored under `outputs/vivado_kintex7/` and
`outputs/vivado_kintex7_timing_clean/`.

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

Constraints are unchanged: 4.000 ns `clk`, narrow false paths on `hit[*]` and
`rst_n` only. No broad false paths. No relaxed clock.

Wave Union / MSWU-B is not part of this flow.
