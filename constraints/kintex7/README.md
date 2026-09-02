# Kintex-7 constraints

`tdc_benchmark_ooc.xdc` is an out-of-context resource/P&R file:

- 4 ns `clk` for capture/control FFs only (not TDL bin period)
- narrow false paths from asynchronous `hit[*]` and `rst_n`
- no board package pins

Vertical CARRY4 LOC assignment is generated at run time from the selected
part’s SLICE sites (`scripts/vivado/run_kintex7_baseline.py`). Do not invent
coordinates in this folder.

`tidl.xdc` remains a board-level placeholder.
