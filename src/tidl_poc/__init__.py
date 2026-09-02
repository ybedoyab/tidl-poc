"""TRL-2 TIDL concept-evidence models.

Nothing in this package is a physical measurement. Simulation outputs are
classified as model-based simulation unless a caller explicitly labels otherwise.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("tidl-poc")
except PackageNotFoundError:
    __version__ = "0.1.0"

DEFAULT_SEED = 42
RESULT_CLASSIFICATION = "model-based simulation"
SPICE_RESULT_CLASSIFICATION = "SPICE/front-end simulation"
RTL_RESULT_CLASSIFICATION = "RTL/synthesis/implementation evidence"
MEASUREMENT_DISCLAIMER = (
    "This output is a model-based simulation. It is not a physical measurement, "
    "FPGA characterisation, SPICE result, or laboratory POC dataset."
)
SPICE_DISCLAIMER = (
    "This output is a SPICE/front-end simulation. It is not a physical measurement, "
    "FPGA characterisation, or laboratory POC dataset. It is not S14 compliance."
)
RTL_DISCLAIMER = (
    "This output is RTL/synthesis/implementation evidence. It is not a physical measurement, "
    "not TDC bin widths, not 1 ps resolution, not DNL/SSP/accuracy, and not laboratory POC data."
)

__all__ = [
    "__version__",
    "DEFAULT_SEED",
    "RESULT_CLASSIFICATION",
    "SPICE_RESULT_CLASSIFICATION",
    "RTL_RESULT_CLASSIFICATION",
    "MEASUREMENT_DISCLAIMER",
    "SPICE_DISCLAIMER",
    "RTL_DISCLAIMER",
]
