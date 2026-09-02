# MSWU-inspired structural OOC benchmark. No board pins.
#
# clk times synchronous capture/control only. Not TDC bin accuracy.

create_clock -period 4.000 -name clk [get_ports clk]

set_false_path -from [get_ports {hit[*]}]
set_false_path -from [get_ports {wu_arm[*]}]
set_false_path -from [get_ports rst_n]
