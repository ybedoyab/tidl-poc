# Testbenches

`tb_coarse_counter.sv` and `tb_timestamp_combiner.sv` cover arithmetic and
protocol/state for the timestamp path. They are not TDC timing testbenches.

CI does not require iverilog or Vivado. The software twin is
`tests/test_coarse_fine.py`.
