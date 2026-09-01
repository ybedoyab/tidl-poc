# Error budget

S14 precision target: 20 ps RMS. Accuracy 20 ps is a separate, traceable-mean
requirement. Resolution 1 ps is not this budget.

Model: `python -m tidl_poc sim error-budget`

Combination: RSS of independent terms plus an optional common/correlated term.
Monte Carlo is a Gaussian check of the same model.

## Terms

| Term | Role |
| --- | --- |
| Front-end threshold jitter | σ_t ≈ σ_v / slew |
| Time-walk residual | Amplitude-dependent leftover |
| FPGA fine TDC SSP | Fine interpolator |
| Coarse / reference jitter | 10 MHz short-term |
| Channel-skew residual | After S15 calibration |
| Calibration residual | Finite code-density / stale LUT |
| PVT residual | 10–40 °C leftover |
| Supply noise | Rails into TDC and comparator |
| Clock distribution | On-board / on-chip |
| Common/correlated | Shared among channels |

Every numeric value in the three scenarios is tagged `literature` or
`assumption` in `outputs/error_budget/terms.csv` (generated, gitignored).
The FPGA SSP in the illustrative scenario uses the Mao-fitted N=10 model
(literature-fitted simulation, not this FPGA).

## Scenarios

1. **literature-informed illustrative** — not silently optimistic on the analog
   terms; TDC SSP from literature fit. May sit near or under 20 ps RSS.
2. **conservative** — intended to **fail** 20 ps until allocations improve.
3. **stress** — intended to fail clearly.

If a submission quotes only scenario 1, that is incomplete. The conservative and
stress cases exist to stop silent favourable defaults.

## Gaps

No term is measured. Closing S14 requires replacing assumptions with SPICE,
FPGA, and clock-reference data. Long intervals (→ 1 s) move error into the
reference-clock stability allocation (NIST SP 1065), which is **not** folded
into the picosecond RSS table as an ADEV number because none has been measured.
