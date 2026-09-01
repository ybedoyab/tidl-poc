# Reliability and maintainability plan (TRL 2)

Design **target**: ≥10 years full-time operation. That is not demonstrated MTBF
and not a life-test result.

## What exists now

- Requirement capture (dual AC, IEC 61000 intent, no radio, internal log).
- Conceptual quality bits so a field unit can flag holdover, calibration version,
  and UTC validity.

## What must exist by end of POC (TRL 5/6)

| Topic | Evidence needed |
| --- | --- |
| Dual AC failover | Tested switchover without false timestamps beyond allocation |
| Surge/burst | IEC 61000-4-4 / 4-5 plan and lab report |
| Thermal | 10–40 °C with calibration policy |
| Maintainability | Field replaceable PSU/fan/SFP as applicable; SMA service access in 3U |
| Wear-out | Flash/log media endurance; electrolytic capacitor policy |
| Firmware | Signed update path; SNMPv3 authPriv; no undocumented debug radios |
| Calibration | Interval or continuous; versioned LUTs; stale-cal flag |
| Logging | Replay after power cycle; CRC fail isolation |

Until those exist, submissions may state the 10-year figure only as a design
target. See [claims-register.md](../competition/claims-register.md) C24.
