# PVT strategy

Required operating range: 10–40 °C. Laboratory nominal: 20–23 °C.

`python -m tidl_poc sim pvt` compares:

- no calibration
- periodic calibration (interval sweep)
- continuous/online calibration (lag-limited)

Delay-bin scale drift and channel-offset drift are **swept assumptions**.
Mao et al. 2022 quote 0.0002 ps/°C as a **resolution** temperature coefficient
on 25–70 °C for their MCS TDC. That number is tracked as literature and is
**not** used as residual timestamp error.

## Qualitative result of the model

Without calibration, residual grows with |T − T_ref|. Periodic calibration is
limited by interval × ramp rate. Continuous calibration is limited by a lag
assumption (0.2 s) and the same ramp rate. Worst-case numbers over the sweep
are assumption-dominated; see generated `outputs/pvt/`.

## POC

Temperature chamber 10–40 °C, static dwells, ramps, and a step. Record
calibration-version changes. Acceptance: residual inside the error-budget PVT
allocation once that allocation is frozen (TBD).
