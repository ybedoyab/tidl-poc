# UTC / 1 PPS timestamp architecture

Status: **TRL 2**. Classification: architectural definition +
**model-based simulation** of control behaviour. Not physical UTC accuracy.
**Do not** use NTP/PTP for picosecond phase alignment.

## Principles

- External **1 PPS**, 50 Ω, receives a matched low-jitter front-end and FPGA
  capture (same electrical class as measurement channels where practical).
- Physical **1 PPS** defines each UTC-second **boundary**.
- Coarse counter runs from the disciplined frequency domain
  ([reference-clock-architecture.md](reference-clock-architecture.md)).
- Fine TDC supplies sub-cycle phase (multichain or MSWU-inspired branch;
  **no winner selected from Vivado alone**).
- All **16 channels** have independent timestamps and calibration offsets (S15).

## Conceptual timestamp

```text
timestamp = UTC_second + coarse_phase + calibrated_fine_phase
```

Signed **±1 s** interval arithmetic remains required (S14 range).

## Control operation: `SET_UTC_EPOCH_ON_NEXT_PPS`

| Step | Behaviour |
| --- | --- |
| 1 | Authenticated management delivers an **integer UTC-second label** |
| 2 | FPGA arms the label (`armed`, UTC still invalid until apply) |
| 3 | On the **next captured physical 1PPS**, apply that integer exactly |
| 4 | Hardware increments the second on subsequent PPS edges |

NTP/PTP may assist **only** with obtaining the coarse second label for the
operator/management plane. They must **not** be used to claim S14 phase.

## Flags and integrity

| Flag / rule | Meaning |
| --- | --- |
| Reference-loss alarm | 10 MHz (or derived) missing / unqualified |
| Invalid-UTC | PPS absent **or** epoch never armed / not yet applied |
| Holdover | Frequency domain degraded; timestamps not UTC-valid |
| Monotonic sequence | Sequence numbers increase; no silent relabel after discontinuity |
| No silent relabel | After a gap or re-arm, quality bits must show the discontinuity |

## Model evidence

```text
python -m tidl_poc sim utc-timestamp
python -m tidl_poc sim reference-clock
```

Unit tests cover: epoch arm, rollover, missing PPS, channel calibration offset,
signed ±1 s limits, monotonic timestamps, UTC-valid / holdover flags.

## Open risks

- No physical 1 PPS ↔ UTC accuracy allocation closed.
- Management-plane authentication for `SET_UTC_EPOCH_ON_NEXT_PPS` is a POC
  software/security deliverable.
- Leap-second policy is TBD (integer label must be defined for the operational
  timescale in use).
