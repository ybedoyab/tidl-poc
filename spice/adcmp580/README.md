# ADCMP580 LTspice (owner workflow)

No `.asc` is committed. The pin interface of the installed official model is
not assumed here.

Datasheet: ADCMP580/581/582 Rev. B.
Product page: <https://www.analog.com/en/products/adcmp580.html>
(Analog Devices states the ADCMP580 model is available in LTspice.)

## Exact local steps for the owner

1. Open LTspice.
2. Press F2 (component search).
3. Search `ADCMP580`.
4. If the official model is present, place it.
5. Save the schematic into this directory (`spice/adcmp580/`).
6. After that file exists, the project will add (still as a schematic, not as
   invented results):
   - 50 ohm source / input case
   - differential threshold
   - input rise-time sweep
   - amplitude / overdrive sweep
   - source-noise sweep
   - propagation-delay measurement
   - output threshold-crossing measurement

If F2 does not find ADCMP580, stop. Do not substitute a guessed symbol.

## Intended sweeps (parameters only; no results)

Edge rise time: 100 ps, 250 ps, 500 ps, 1 ns, 2 ns, 5 ns.

Input amplitude: choose only after validating the ADCMP580 input range
(−2 V to +3 V with ±5 V supplies, datasheet) against the challenge 1 PPS
signal. If the challenge amplitude is unknown, **parameterize** it. Do not
assume a challenge amplitude.

Threshold offsets: sweep around the nominal threshold once that nominal is
defined.

Monte Carlo noise remains a separate analytical model
(`python -m tidl_poc sim frontend-jitter`) unless the official macromodel is
shown to support noise correctly.

## Classification

Outputs from a real LTspice run are `SPICE/front-end simulation` only after the
owner actually runs the tool and returns the output. They are not laboratory
measurements and are not S14 compliance.
