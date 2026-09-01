# Front-end jitter

`python -m tidl_poc sim frontend-jitter`

Model (units stated):

- `sigma_t (s) ≈ sigma_v (V) / slew_rate (V/s)`
- RSS with threshold uncertainty converted the same way, plus comparator
  additive jitter (ps) and time-walk residual (ps)

No comparator is **selected**. ADCMP580 is a tracked candidate
([frontend-candidate-adcmp580.md](frontend-candidate-adcmp580.md)).
Datasheet random jitter (200 fs RMS) is much smaller than the 5 ps allocation;
deterministic jitter (10 ps) and overdrive/slew-rate dispersion (quote 15–25 ps
from the relevant ADCMP580 table row) are not that 200 fs figure and can be
comparable to the 20 ps system target.

LTspice workflow: `python scripts/ltspice/run_adcmp580.py`. Successful output is
**SPICE/front-end simulation**, not laboratory data.

The design-space figure contours 5, 10, and 15 ps RMS allocations versus input
noise and slew. Those allocations are budgets to be negotiated with the TDC and
clock terms, not demonstrated hardware. Challenge amplitude, rise time, and
threshold remain unspecified.

50 ohm / SMA (S2, S4, S6, S16) constrain the analog implementation but are not
modelled as S-parameters here.

POC: freeze a comparator after datasheet + SPICE + measured 1 PPS edge, then
measure with a fast oscilloscope. Until then, front-end terms in the error
budget remain assumptions.
