# UTC / 10 MHz / 1 PPS reference

S1, S3, S12. Flags, not a time-error claim.

`python -m tidl_poc sim reference-clock` is a behavioural state machine:

SEARCH → QUALIFYING → LOCKED → HOLDOVER → REACQUIRE → LOCKED

Quality bits on each record (concept): 10 MHz present/qualified, 1 PPS
present/aligned, UTC valid, holdover.

UTC valid is asserted only in LOCKED in this model. Holdover is a **flag**.
No OCXO/Cs holdover specification is implied.

## Clock accuracy vs arithmetic

Coarse+fine arithmetic can represent ±1 s. That is not UTC accuracy.
Over 1 s, 20 ps is 2×10⁻¹¹ fractional frequency under `delta_t = y * tau`
([reference-stability.md](reference-stability.md)). That allocation belongs to the
10 MHz source, distribution, and traceability chain. Methodology once data exist:
NIST SP 1065 and IEEE 1139. This repository has no ADEV dataset.

POC: qualify 10 MHz at the FPGA, align 1 PPS, log flags, and only then assign a
numeric UTC error budget that still leaves room for the TDC and front-end.

Kwiatkowski et al. 2023: for intervals longer than hundreds of microseconds
their TCXO stability, not the counter, dominated precision. Qualitative
literature only; see [reference-stability.md](reference-stability.md). No ADEV
is derived from that statement.
