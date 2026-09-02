# Kintex-7 structural TDL (original)

Classification: **RTL/synthesis/implementation evidence** only.

| Module | Role |
| --- | --- |
| `carry4_tdl_chain.sv` | Parameterized CARRY4 sequence; every CO tap exported |
| `tdc_capture_bank.sv` | One FDRE per tap (`KEEP` / `DONT_TOUCH` on captured bus) |
| `multi_chain_tdc_structural.sv` | N parallel chains; chain_sample = tap 0 per chain |
| `tdc_benchmark_top.sv` | Timing-clean OOC wrapper; `bench_status` per channel |
| `legacy/` | Round-6 wide parity observability (historical reference) |

Round-6 tracked snapshot: `docs/evidence/vivado_kintex7/`.
Timing-clean @64 CARRY4/chain: `docs/evidence/vivado_kintex7_timing_clean/`.

Do **not** treat post-route delays, WNS, or LUT/FF counts as 1 ps resolution,
DNL, SSP, accuracy, or physical temperature behaviour.
