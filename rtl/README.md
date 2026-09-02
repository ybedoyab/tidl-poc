# RTL scaffold

Original SystemVerilog. Not copied from papers.

Family-specific Kintex-7 CARRY4 TDL lives in `rtl/tdc/kintex7/`. That RTL is
**structural**. Vivado synthesis/implementation of it is
`RTL/synthesis/implementation evidence`, not 1 ps resolution and not physical
bin widths. There is no behavioural `#1ps` delay line.

Arithmetic and protocol logic in `timestamp/` is intended to be testable without
Vivado. CI does not run Vivado.
