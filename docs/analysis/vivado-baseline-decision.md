# First Vivado baseline (design decision, not implementation evidence)

Status: TRL 2. This is an engineering decision for the **first synthesis
branch**. It is not a claim that Kintex-7 meets S14, and it is not laboratory
or P&R evidence.

## Decision

| Item | Choice | Why now |
| --- | --- | --- |
| FPGA family / carry primitive | Kintex-7 / CARRY4 | Lowest 12-month implementation risk; Mao 2022 literature anchors are Kintex-7 MCS, used only as a fitted model |
| Fine TDC | 8 parallel chains per channel | Literature-fitted SSP is 4.76 ps RMS (model); resource cost still TBD in Vivado |
| Channel scaling to report | 1 → 4 → 8 → 16 | Matches S7 preferred simultaneous path; stop/switch if utilization fails |
| Wave Union / hybrid | Deferred to a second branch | Until resource and timing reports exist for the 8-chain TDL |

Tcl still requires `TIDL_PART` to be set. Suggested first part class: a Kintex-7
device, still not a frozen BOM selection. UltraScale / UltraScale+ remain
candidates after the Kintex-7 resource/timing picture exists.

Wave Union stays in the trade study as the high-upside alternative. It is not
the first P&R job.

See [architecture-trade-study.md](architecture-trade-study.md) and
`scripts/vivado/README.md`.
