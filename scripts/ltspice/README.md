# LTspice runner

`python scripts/ltspice/run_adcmp580.py [--fast|--all] [--ltspice path]`

Discovers `LTspice.exe` under common Windows paths or `TIDL_LTSPICE`.
Batch flag is `-b` (LTspice 26 help). `-I` is last when a library path is
required.

Outputs: gitignored `outputs/spice_adcmp580/`.
Classification: SPICE/front-end simulation.
