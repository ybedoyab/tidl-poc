# Vivado Kintex-7 structural baseline

These scripts do **not** run in CI and do not assume Vivado is installed.

Classification of outputs: **RTL/synthesis/implementation evidence**.
Not physical TDC bins, not 1 ps resolution, not DNL/SSP/accuracy.
No bitstreams. No board package pins.

A compact tracked snapshot lives in `docs/evidence/vivado_kintex7/`.
Raw Vivado trees, logs, `.runs`, `.cache`, `.Xil`, and checkpoints stay
gitignored under `outputs/vivado_kintex7/`.

## Runner

```text
python scripts/vivado/run_kintex7_baseline.py
python -m tidl_poc vivado-baseline
python -m tidl_poc vivado-baseline --export-only
```

`--export-only` re-parses already-completed local reports and refreshes the
tracked snapshot. It does not relaunch place/route.

Optional: `--vivado <vivado.bat>`, environment `TIDL_VIVADO`.
The runner copies RTL/XDC to a comma-free staging directory under the system
temp folder before invoking Vivado. Some Vivado file commands split on commas
in Windows paths. Staging paths stay in gitignored `local_paths.json`.

The runner:

1. Discovers Vivado and queries installed Kintex-7 parts (`get_parts`)
2. Prefers speed-grade `-2`, then XC7K160 for Kwiatkowski 2023 comparability
3. Synthesizes 12 cases: channels {1,4,8,16} × 8 chains × CARRY4 {32,48,64}
4. Place/routes at least 1/4/8/16 channels at 64 CARRY4/chain plus 1-channel
   at each length (unless `--impl-all`)
5. Parses utilization/timing/DRC and compares CARRY4 counts to
   `channels × chains × carry4_per_chain`. Export fails on a mismatch.
   Vertical CARRY4 LOC guidance runs on 1-channel implementation cases only;
   larger cases let the placer choose sites and the runner still records
   post-route LOC scatter.
6. On Python timeout, kills the Vivado process tree (`taskkill /T /F` on
   Windows) and reconciles status from reports (`timeout`, `failed`,
   `succeeded`, or `recovered_after_timeout`). A leftover file is not success.

The first 16×64 job hit a 10800 s parent timeout while Vivado continued and
finished successfully (CARRY4=8192). That false `failed` label is documented
in the evidence README and must not be repeated.

Older project Tcl (`create_project.tcl`) still requires `TIDL_PART` if used.
There is no frozen production BOM part.

Wave Union / MSWU-B is not part of this first flow.

## Local 2026.1 result (structural only)

16-channel × 8-chain × 64-CARRY4 mapped 8192 CARRY4 and fully routed on
`xc7k160tffg676-2` at 10,980 slices (43.3%). Placement: 128/128 vertical
chains, 0 scattered. Negative WNS is 4 ns capture-clock timing, not a TDC
bin. This does not select multichain vs MSWU-B.
