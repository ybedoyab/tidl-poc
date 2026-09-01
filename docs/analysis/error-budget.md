# Error budget

S14 precision target: 20 ps RMS. Accuracy 20 ps is a separate, traceable-mean
requirement. Resolution 1 ps is not this budget.

Model: `python -m tidl_poc sim error-budget`

Each term is one of:

- `random_precision` — RSS into the precision table
- `deterministic_calibratable_bias` — linear sum into the accuracy/worst-case table
- `correlated_common_mode` — included in precision RSS-with-common

Accuracy worst-case bound used here is `sum(|bias|) + precision_RSS_with_common`
(1-sigma style). It is not a laboratory k-factor.

Non-literature numbers are **engineering allocations, not evidence**. The FPGA
TDC SSP uses the Mao-fitted model (N=10 / N=1 / N=8 depending on scenario).

## Scenarios

1. **literature-informed illustrative** — analog terms not silently tiny.
2. **conservative** — intended to **fail** 20 ps precision until allocations improve.
3. **stress** — intended to fail clearly.
4. **target_allocation** — labelled design allocation: frontend 5 ps, time-walk
   bias 3 ps, 8-chain literature-fitted TDC, coarse/reference 4 ps, channel
   random 4 ps, calibration random 3 ps, PVT random 4 ps, supply 2 ps, clock
   distribution 3 ps, common-mode 2 ps. **Not evidence.** Kwiatkowski 2023 MSWU
   resolution/precision numbers are **not** substituted into this table.

If a submission quotes only scenario 1 or 4, that is incomplete.

## Gaps

No term is measured. Long intervals (→ 1 s) need the first-order reference
allocation in [reference-stability.md](reference-stability.md) and, later, ADEV
from NIST SP 1065. That is not folded into the picosecond RSS table as a
measured stability number.
