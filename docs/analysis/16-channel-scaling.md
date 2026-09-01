# 16-channel scaling

Preferred: simultaneous timestamping of all 16 channels (S7).
Alternate: switching, including hot switching, with a documented settle time.

`python -m tidl_poc sim channel-scaling` is a covariance model:

- per-channel offset
- common-mode timing noise (rank-1)
- independent noise
- optional crosstalk growing with simultaneous activity

Outputs: 16×16 covariance heatmap, pairwise skew distribution, worst-channel and
worst-pair metrics, single-active vs 16-active RMS.

All coefficients are assumptions (see [assumptions.md](../assumptions.md) A7).
They are not FPGA crosstalk measurements.

Resource scaling (LUTs, carry chains, RAM for LUTs) needs Vivado reports after a
part is chosen. Scripts in `scripts/vivado/` list the intended reports; CI does
not run them.

If the selected FPGA cannot host 16 simultaneous fine engines, the alternate
switching concept becomes in-scope. That would add a hot-switch transient term
to the error budget and would need an explicit S7 acceptance rewrite.
