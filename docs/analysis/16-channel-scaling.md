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
TDL, with CARRY4 length 32/48/64 swept
([vivado-baseline-decision.md](vivado-baseline-decision.md);
[docs/evidence/vivado_kintex7/](../evidence/vivado_kintex7/)).
The 16×8×64 topology mapped 8192 CARRY4 and fully routed on XC7K160T
(10,980 slices, 43.3%). Those reports are structural/resource evidence, not
16-channel metrology.

Naive replication of the Kwiatkowski 2023 complete measurement channel is
**not** this architecture. At 16 × 1 PPS the paper's deep FIFOs are not
required by event rate
([low-rate-16-channel-datapath.md](low-rate-16-channel-datapath.md)).
`python -m tidl_poc sim mswu-literature` reports that arithmetic without
claiming a fit or a final BRAM number.

