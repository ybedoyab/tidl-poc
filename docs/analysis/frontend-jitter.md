# Front-end jitter

`python -m tidl_poc sim frontend-jitter`

Model (units stated):

- `sigma_t (s) ≈ sigma_v (V) / slew_rate (V/s)`
- RSS with threshold uncertainty converted the same way, plus comparator
  additive jitter (ps) and time-walk residual (ps)

No comparator is selected. No SPICE exists (evidence class 4 is empty).

The design-space figure contours 5, 10, and 15 ps RMS allocations versus input
noise and slew. Those allocations are budgets to be negotiated with the TDC and
clock terms, not demonstrated hardware.

50 ohm / SMA (S2, S4, S6, S16) constrain the analog implementation but are not
modelled as S-parameters here.

POC: pick a comparator from a datasheet, SPICE the threshold crossing with the
real 1 PPS edge, then measure with a fast oscilloscope. Until then, front-end
terms in the error budget remain assumptions.
