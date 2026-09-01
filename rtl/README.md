# RTL scaffold

Original SystemVerilog. Not copied from papers.

These modules are **not** a 1 ps TDC. A behavioural delay line is not a physical
interpolator. Family-specific carry primitives (`CARRY4`, `CARRY8`) must be
instantiated later behind `rtl/tdc/` and constrained with device-specific
placement. Until then, there is **no** RTL/synthesis performance evidence.

Arithmetic and protocol logic in `timestamp/` is intended to be testable without
Vivado. CI does not run Vivado.
