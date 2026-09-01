# Simulations

Entry point: `python -m tidl_poc sim --fast`.

Each subdirectory is an experiment. Implementations live in `src/tidl_poc/models/`.
Outputs are classified as model-based simulation and are not physical measurements.

`mswu-literature` transcribes Kwiatkowski et al. 2023 tables and applies
challenge arithmetic (16 events/s, naive 16-channel products). It is not an
MSWU physics simulation and not this project's FPGA result.

