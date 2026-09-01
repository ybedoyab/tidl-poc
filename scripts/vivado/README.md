# Vivado preparation

These scripts do **not** run in CI and do not assume Vivado is installed.

Set the part explicitly. There is no default production part. The first
intended baseline (decision only) is Kintex-7 / CARRY4; see
[docs/analysis/vivado-baseline-decision.md](../../docs/analysis/vivado-baseline-decision.md).

```text
set TIDL_PART=xc7k325tffg900-2
vivado -mode batch -source scripts/vivado/create_project.tcl
```

Candidate families (not a frozen BOM):

- Kintex-7 (first synthesis branch)
- Kintex UltraScale: XCKU025 / XCKU035
- Kintex UltraScale+: XCKU3P / XCKU5P

Intended reports (none are checked in):

- synthesis utilization
- post-place utilization
- timing summary
- clock utilization
- methodology checks
- DRC
- placement of carry-chain / TDC cells
- power estimate if available
- route status
- resource scaling for 1, 4, 8, 16 channels with 8 parallel chains per channel

Wave Union / MSWU-B is not part of this first Tcl flow. After those scaling
reports exist, a later original single-channel structural MSWU-B branch may be
added for comparison (no copied paper HDL).

Generated Vivado trees are gitignored.
