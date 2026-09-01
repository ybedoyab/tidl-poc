# Vivado preparation

These scripts do **not** run in CI and do not assume Vivado is installed.

Set the part explicitly. There is no default production part.

```text
set TIDL_PART=xcku035-ffva1156-1-e
vivado -mode batch -source scripts/vivado/create_project.tcl
```

Candidate families for the initial trade study (not a selection):

- Kintex-7
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
- resource scaling estimate for 1, 4, 8, 16 channels

Generated Vivado trees are gitignored.
