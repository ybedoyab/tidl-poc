# PVT strategy

Required operating range: 10–40 °C. Laboratory nominal: 20–23 °C.

`python -m tidl_poc sim pvt` is a **time-domain calibration state** model:

- no calibration (LUT frozen at T_ref)
- periodic calibration (LUT stores current drift at each epoch; residual is
  identically zero at those samples)
- continuous/online calibration (causal lag)

Profiles: static soak, ramp, and step. Delay-bin scale drift and channel-offset
drift are **swept engineering allocations**. Mao et al. 2022 quote 0.0002 ps/°C
as a **resolution** temperature coefficient; it is **not** the residual used here.

**Additional literature-anchored scenario** (not this board): Kwiatkowski et al.
2023 report 21 ps channel-offset change over 0–40 °C = 0.525 ps/°C. The PVT
model reports uncompensated movement over 10–40 °C using that coefficient and
a temperature-specific-recalibration residual of 0 ps at each static
temperature. The paper's observation that temperature-specific recalibration
kept split-signal interval precision <3 ps over 0–40 °C is cited, not
interpolated. Classification: literature evidence plus model-based arithmetic.

On a static soak, the first periodic epoch zeros the residual for the rest of
the dwell. Interval sensitivity is therefore a ramp/step result, reported as
worst-case and RMS residual versus interval.

See also `python -m tidl_poc sim mswu-literature`.

## POC

Temperature chamber 10–40 °C, static dwells, ramps, and a step. Record
calibration-version changes. Acceptance: residual inside the error-budget PVT
allocation once that allocation is frozen (TBD).
