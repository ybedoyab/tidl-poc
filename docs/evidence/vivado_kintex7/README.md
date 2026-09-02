# Kintex-7 structural implementation evidence

This directory is a **tracked, compact snapshot** of the first Vivado 2026.1
Kintex-7 CARRY4 TDL matrix. Raw tool output stays gitignored under
`outputs/vivado_kintex7/` (logs, journals, `.runs`, `.cache`, `.Xil`,
checkpoints, and generated project internals). Reviewers can read the derived
tables and figures here without importing a machine-specific Vivado tree.

**Classification:** RTL/synthesis/implementation evidence.
**Part:** `xc7k160tffg676-2`. **Architecture:** 8 chains/channel, CARRY4-based.
No bitstream. No board pins assigned.

No physical timing measurement. No claim of 1 ps resolution, DNL, SSP,
accuracy, or temperature performance.

## Figures

- `resource_scaling.png` — LUT / FF / slice / CARRY4 counts versus channel
  count for the 32/48/64 CARRY4-per-chain sweep.
- `carry4_length_effect.png` — mapped CARRY4 versus channels and TDL length.
- `placement_1ch_64.png` — 1-channel, 64 CARRY4/chain LOC plot (8 vertical
  carry runs, no scatter). Generated from Vivado LOC text, not a GUI
  screenshot.
- `placement_16ch_64.png` — 16-channel, 64 CARRY4/chain LOC plot (128 chains,
  128 vertical runs, 0 scattered).

## Reproduce

From a machine with Vivado 2026.1 and the Kintex-7 device files:

```text
python -m tidl_poc vivado-baseline
```

or `python scripts/vivado/run_kintex7_baseline.py`. The runner synthesizes 12
cases (channels {1,4,8,16} × CARRY4 {32,48,64}) and place/routes the default
implementation subset (1-channel at 32/48/64 plus 1/4/8/16-channel at 64).

To rebuild this snapshot from already-completed local reports without
re-launching place/route:

```text
python -m tidl_poc vivado-baseline --export-only
```

Export fails if any mapped CARRY4 count differs from
`channels × 8 × carry4_per_chain`.

## 16×64 structural conclusion

The 16-channel × 8-chain × 64-CARRY4 topology mapped 8192 CARRY4 primitives
and fully routed on XC7K160T, using 10,980 slices (43.3% of device slices).
Resource scaling is approximately linear. That lowers implementation-capacity
risk. It does **not** prove metrological performance and does **not** select
multichain versus MSWU-B.

## WNS caveat

Negative WNS from the 1-channel / 64-CARRY4 case onward is synchronous
capture/control timing against the 4 ns benchmark clock. It is not a TDC-bin
measurement.

## Runner timeout anomaly (documented, then fixed)

The original 16×64 job used a 10800 s Python `subprocess.run` timeout. The
Python parent returned −1 while the Vivado child continued and later wrote
complete synthesis and implementation reports (`TIDL_SYNTH_STATUS=ok`,
`TIDL_IMPL_STATUS=ok`, CARRY4=8192). The first aggregate `summary.json`
incorrectly recorded `synth_status=failed` for that case.

The runner now:

1. uses `Popen` and, on timeout, kills the full process tree (`taskkill /T /F`
   on Windows) so jobs are not orphaned;
2. derives final status from **both** the subprocess outcome and validated
   report markers (utilization, `TIDL_*_STATUS=ok`, and mapped CARRY4 count);
3. can label a completed child as `recovered_after_timeout` instead of
   inventing a false `failed`.

A leftover report file is never treated as success by itself.
