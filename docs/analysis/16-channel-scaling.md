# 16-channel scaling

Preferred: simultaneous timestamping of all 16 channels (S7).
Alternate: switching, including hot switching, with a documented settle time.

`python -m tidl_poc sim channel-scaling`:

- one static per-channel offset realisation, **reused** at activity 1, 2, 4, 8, 16
- common-mode and independent random precision
- crosstalk as a **sensitivity sweep**, not a single privileged coefficient
- metrics split: static offset/skew vs precision RMS after removing channel means

Coefficients are engineering allocations (see [assumptions.md](../assumptions.md)
A7). They are not FPGA crosstalk measurements.

First Vivado resource scaling is 1 → 4 → 8 → 16 channels on Kintex-7 / 8-chain
TDL ([vivado-baseline-decision.md](vivado-baseline-decision.md)).
