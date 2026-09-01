# POC validation plan (path toward TRL 5/6)

Window: ≤12 months after funding. This is a plan, not evidence of TRL 5/6.

## Phases

1. **Device and front-end selection** — pick FPGA family/part and a comparator
   from datasheets; SPICE the 50 ohm SMA path; freeze an error-budget allocation.
2. **Single-channel TDC** — implement family-specific carry chain (7-series
   CARRY4 or UltraScale CARRY8), encoder, code-density; measure SSP vs a
   traceable delay. Classify results as physical POC measurement.
3. **PVT** — 10–40 °C on that channel; choose periodic vs online calibration.
4. **Scale to 16 channels** — simultaneous preferred; switching only if resources
   fail. Pairwise skew matrix.
5. **UTC subsystem** — 10 MHz + 1 PPS lock/holdover; ADEV (NIST SP 1065).
6. **Data path** — UDP + SNMPv3 + internal log replay.
7. **Packaging** — 19-inch ≤3U, dual AC, IEC 61000 inlet tests, SMA panel.
8. **Field-test readiness** — reliability/maintainability package
   ([reliability-plan.md](../analysis/reliability-plan.md)).

## Exit criteria (end of POC, not now)

- TRL 5/6 evidence: instrument in a relevant lab/field-like environment.
- S14 demonstrated with classified measurements (not simulations).
- Independent channel timestamps (S15).
- Ready for field testing: logging, flags, maintainability, no radios.

Fine-TDC candidate remains a hypothesis until phase 2/3 data exist
([architecture-trade-study.md](../analysis/architecture-trade-study.md)).
