# Calibration strategy

Two calibration layers are hypothesized:

1. **Code-density / bin-width** — statistical occupancy of the fine TDL, producing
   a width LUT and a reconstructed time.
2. **PVT** — periodic or continuous refresh of that LUT and of channel offsets
   as temperature, voltage, and ageing move.

Encoder bubbles are a third, digital, problem: a bubble-resistant encoder is
required before occupancy statistics are meaningful. The encoder is not specified
in this public note.

## Code-density (synthetic evidence only)

`python -m tidl_poc sim calibration` builds a 512-bin **illustrative** TDL with
non-uniform positive widths. It is not an FPGA carry chain.

Outputs: RMS/MAE/P95/P99/max reconstruction error; DNL/INL before vs after the
calibrated representation; convergence vs 1e4, 1e5, 1e6 (and optional 1e7)
calibration hits.

A large uniform sample estimates widths; an independent sample scores
reconstruction. Zero-count bins are given a tiny floor so the LUT stays
positive — a model detail, not a hardware recipe.

## What this does not show

- Physical resolution of 1 ps.
- INL after place-and-route on Kintex-7 or UltraScale.
- That 1e7 hits are available in the instrument’s dead-time budget.

Lusardi, Garzetti and Geraci (2019, sub-interpolation) and Zhang et al. (2022,
online calibration) are literature context only.

POC method (TBD hardware): histogram from a free-running or offset clock;
freeze a calibration version ID into every timestamp record (see packet schema).
