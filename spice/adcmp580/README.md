# ADCMP580 LTspice (owner + automation)

Official model remains in the local LTspice library. Do not commit `.sub`,
`.asy`, or Analog Devices example schematics.

Project testbench (original): `tidl_adcmp580_characterization.asc`

## Automation

```text
python scripts/ltspice/run_adcmp580.py --all
```

`--fast` is a reduced grid. Classification of successful output:
`SPICE/front-end simulation`.

If LTspice.exe or ADCMP580.sub cannot be resolved, the script exits without
inventing numbers.

## Manual GUI step (only if batch cannot see the model)

1. Open LTspice, F2, confirm ADCMP580 is listed.
2. Re-run the script.

Latch compare-mode used in the testbench: `LE = 0.4 V`, `_LE = GND`, `VTT = GND`
as in the installed official example. HYS left open.

## Sweeps

Datasheet-domain: overdrive 5–500 mV, slew 1–10 V/ns, both edges.
Challenge-oriented: rise 100 ps–5 ns at an engineering amplitude (0.4 V),
**not** a challenge 1 PPS specification.

Random jitter is not inferred from these transients.
