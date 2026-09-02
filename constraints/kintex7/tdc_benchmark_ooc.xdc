# Out-of-context benchmark constraints. No board package pins.
#
# clk is a *control/capture* benchmark clock only. Meeting this period does
# not mean asynchronous CARRY4 taps are picosecond-accurate TDC bins.

create_clock -period 4.000 -name clk [get_ports clk]

# hit is an asynchronous event input, not synchronous datapath.
# Narrow: from the hit ports only. Do not disable all timing.
set_false_path -from [get_ports {hit[*]}]

# Asynchronous reset into FDRE.R. Narrow: rst_n port only.
set_false_path -from [get_ports rst_n]
