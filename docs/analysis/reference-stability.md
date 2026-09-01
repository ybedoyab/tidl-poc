# Reference stability (first-order allocation)

S12 / S14 over intervals up to 1 s are limited by the 10 MHz / UTC source, not
by coarse-counter width.

`python -m tidl_poc sim reference-stability`

Model:

```text
delta_t = y * tau
```

Units: `delta_t` in seconds, `tau` in seconds, `y` dimensionless fractional
frequency. This is a **constant-offset accumulation**, not Allan deviation,
MDEV, or TDEV. NIST SP 1065 and IEEE 1139 apply when a measured series exists.

At tau = 1 s:

| Allowed interval error | First-order \|y\| |
| --- | --- |
| 5 ps | 5e-12 |
| 10 ps | 1e-11 |
| 20 ps | 2e-11 |

S14 20 ps at 1 s therefore allocates about 2×10⁻¹¹ if the error is modelled this
way. That allocation is **not** proof that a given oscillator is adequate.

Kwiatkowski et al. 2023 state that for intervals longer than hundreds of
microseconds, reference-clock (TCXO) stability, not the counter, became the
main precision limit. That is **qualitative literature evidence** supporting
keeping a 1 s reference allocation in this package. Do not derive an oscillator
ADEV, MDEV, or TDEV from that sentence.

