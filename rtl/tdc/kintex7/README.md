# Kintex-7 structural CARRY4 TDL (original)

Classification: **RTL/synthesis/implementation evidence** only.

This directory is an original project implementation. It does not copy HDL
from Kwiatkowski, Mao, CERN, or other repositories.

| Module | Role |
| --- | --- |
| `carry4_tdl_chain.sv` | Parameterized CARRY4 sequence; every CO tap exported |
| `tdc_capture_bank.sv` | One FDRE per tap |
| `multi_chain_tdc_structural.sv` | N parallel chains per channel |
| `tdc_benchmark_top.sv` | OOC resource/P&R wrapper; dummy parity output |

Reserved, unimplemented: bubble encoder, calibration LUT.

Do **not** treat post-route delays, WNS, or LUT/FF counts as 1 ps resolution,
DNL, SSP, accuracy, or physical temperature behaviour.

TDL length is swept (32 / 48 / 64 CARRY4 per chain) because coverage of a
coarse-clock phase window is device- and placement-dependent. No length is
claimed sufficient for a real 1 ps TDC.
