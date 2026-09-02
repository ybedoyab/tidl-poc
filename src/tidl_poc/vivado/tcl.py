"""Generate per-case Vivado Tcl for the Kintex-7 structural TDC baseline."""

from __future__ import annotations

from pathlib import Path


def _posix(path: Path) -> str:
    return path.resolve().as_posix()


def generate_wrap_sv(*, n_channels: int, n_chains: int, n_carry4: int) -> str:
    return f"""// Generated wrap. Not a board top. Parameters freeze one benchmark case.
`timescale 1ns/1ps
module tdc_benchmark_wrap (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic [{n_channels - 1}:0] hit,
    output logic                    tap_parity,
    output logic [{n_channels - 1}:0] channel_valid
);
  tdc_benchmark_top #(
      .N_CHANNELS({n_channels}),
      .N_CHAINS({n_chains}),
      .N_CARRY4({n_carry4})
  ) u_top (
      .clk          (clk),
      .rst_n        (rst_n),
      .hit          (hit),
      .tap_parity   (tap_parity),
      .channel_valid(channel_valid)
  );
endmodule
"""


def generate_case_tcl(
    *,
    part: str,
    rtl_dir: Path,
    xdc_path: Path,
    wrap_path: Path,
    out_dir: Path,
    do_impl: bool,
    n_carry4: int,
    place_guide: bool = True,
    fast_impl: bool = False,
) -> str:
    rtl = _posix(rtl_dir)
    xdc = _posix(xdc_path)
    wrap = _posix(wrap_path)
    out = _posix(out_dir)
    impl_flag = 1 if do_impl else 0
    place_flag = 1 if place_guide else 0
    fast_flag = 1 if fast_impl else 0
    synth_cmd = "synth_design -mode out_of_context -top tdc_benchmark_wrap -part $part"
    opt_cmd = "opt_design"
    place_cmd = "place_design"
    route_cmd = "route_design"
    if fast_impl:
        synth_cmd += " -directive RuntimeOptimized"
        opt_cmd = "opt_design -directive RuntimeOptimized"
        # Resource/P&R evidence only. 4 ns WNS is not TDL accuracy; skip timing-driven rip-up.
        place_cmd = "place_design -no_timing_driven"
        route_cmd = "route_design -no_timing_driven"
    return f"""# Generated. OOC structural benchmark. No bitstream. No board pins.
set_param general.maxThreads 8
set part {{{part}}}
set outdir {{{out}}}
set do_impl {impl_flag}
set do_place_guide {place_flag}
set do_fast_impl {fast_flag}
set n_carry4 {n_carry4}
file mkdir $outdir

read_verilog -sv [list \\
  {{{rtl}/carry4_tdl_chain.sv}} \\
  {{{rtl}/tdc_capture_bank.sv}} \\
  {{{rtl}/multi_chain_tdc_structural.sv}} \\
  {{{rtl}/tdc_benchmark_top.sv}} \\
  {{{wrap}}} \\
]
read_xdc [list {{{xdc}}}]

if {{[catch {{{synth_cmd}}} err]}} {{
  puts "TIDL_SYNTH_STATUS=failed"
  puts "TIDL_SYNTH_ERROR=$err"
  report_utilization -file [file join $outdir utilization_synth.rpt]
  exit 1
}}
puts "TIDL_SYNTH_STATUS=ok"

proc tidl_count_ref {{ref}} {{
  return [llength [get_cells -quiet -hierarchical -filter "REF_NAME == $ref"]]
}}

set carry_n [tidl_count_ref CARRY4]
set fdre_n  [tidl_count_ref FDRE]
set lut1_n  [tidl_count_ref LUT1]
set lut2_n  [tidl_count_ref LUT2]
set lut3_n  [tidl_count_ref LUT3]
set lut4_n  [tidl_count_ref LUT4]
set lut5_n  [tidl_count_ref LUT5]
set lut6_n  [tidl_count_ref LUT6]
puts "TIDL_CARRY4_COUNT=$carry_n"
puts "TIDL_FDRE_COUNT=$fdre_n"
puts "TIDL_LUT1_COUNT=$lut1_n"
puts "TIDL_LUT2_COUNT=$lut2_n"
puts "TIDL_LUT3_COUNT=$lut3_n"
puts "TIDL_LUT4_COUNT=$lut4_n"
puts "TIDL_LUT5_COUNT=$lut5_n"
puts "TIDL_LUT6_COUNT=$lut6_n"

set kv [open [file join $outdir metrics.txt] w]
puts $kv "TIDL_SYNTH_STATUS=ok"
puts $kv "TIDL_CARRY4_COUNT=$carry_n"
puts $kv "TIDL_FDRE_COUNT=$fdre_n"
puts $kv "TIDL_LUT1_COUNT=$lut1_n"
puts $kv "TIDL_LUT2_COUNT=$lut2_n"
puts $kv "TIDL_LUT3_COUNT=$lut3_n"
puts $kv "TIDL_LUT4_COUNT=$lut4_n"
puts $kv "TIDL_LUT5_COUNT=$lut5_n"
puts $kv "TIDL_LUT6_COUNT=$lut6_n"
close $kv

report_utilization -file [file join $outdir utilization_synth.rpt]
report_utilization -hierarchical -file [file join $outdir utilization_hier_synth.rpt]
report_drc -file [file join $outdir drc_synth.rpt]

proc tidl_place_carry4_vertical {{n_carry4}} {{
  set cells [get_cells -quiet -hierarchical -filter {{REF_NAME == CARRY4}}]
  puts "TIDL_PLACE_START=[llength $cells]"
  if {{[llength $cells] == 0}} {{
    puts "TIDL_PLACE=no_carry4"
    return
  }}
  array set groups {{}}
  foreach c $cells {{
    set name [get_property NAME $c]
    if {{[regexp {{^(.*gen_carry)\\[(\\d+)\\]}} $name -> prefix idx]}} {{
      lappend groups($prefix) [list $idx $c]
    }} else {{
      lappend groups(_ungrouped) [list 0 $c]
    }}
  }}
  array set col {{}}
  foreach s [get_sites -quiet -filter {{SITE_TYPE == SLICEL || SITE_TYPE == SLICEM}}] {{
    if {{[regexp {{SLICE_X(\\d+)Y(\\d+)}} $s -> x y]}} {{
      lappend col($x) $y
    }}
  }}
  set slots {{}}
  foreach x [lsort -integer [array names col]] {{
    foreach y [lsort -integer -unique $col($x)] {{
      lappend slots [list $x $y]
    }}
  }}
  set ns [llength $slots]
  puts "TIDL_PLACE_SLOTS=$ns"
  set placed_chains 0
  set unconstrained 0
  set off 0
  foreach prefix [lsort [array names groups]] {{
    set members [lsort -integer -index 0 $groups($prefix)]
    set n [llength $members]
    if {{$n < 1}} {{ continue }}
    set found 0
    for {{set i $off}} {{$i < $ns}} {{incr i}} {{
      if {{($i + $n) > $ns}} {{ break }}
      set xy [lindex $slots $i]
      set x0 [lindex $xy 0]
      set y0 [lindex $xy 1]
      set ok 1
      for {{set k 1}} {{$k < $n}} {{incr k}} {{
        set xy2 [lindex $slots [expr {{$i + $k}}]]
        if {{[lindex $xy2 0] != $x0 || [lindex $xy2 1] != ($y0 + $k)}} {{
          set ok 0
          break
        }}
      }}
      if {{!$ok}} {{ continue }}
      set j 0
      foreach m $members {{
        set cell [lindex $m 1]
        set y [expr {{$y0 + $j}}]
        if {{[catch {{set_property LOC "SLICE_X${{x0}}Y${{y}}" $cell}} err]}} {{
          puts "TIDL_PLACE_WARN=$cell SLICE_X${{x0}}Y${{y}} $err"
          set ok 0
          break
        }}
        incr j
      }}
      if {{$ok}} {{
        set off [expr {{$i + $n}}]
        incr placed_chains
        set found 1
        break
      }}
    }}
    if {{!$found}} {{
      incr unconstrained
      puts "TIDL_PLACE_UNCONSTRAINED=$prefix n=$n"
    }}
  }}
  puts "TIDL_PLACE_CHAINS=$placed_chains"
  puts "TIDL_PLACE_UNCONSTRAINED_N=$unconstrained"
}}

if {{$do_impl}} {{
  if {{$do_place_guide}} {{
    tidl_place_carry4_vertical $n_carry4
  }} else {{
    puts "TIDL_PLACE=skipped_large_case"
  }}
  if {{[catch {{{opt_cmd}}} err]}} {{
    puts "TIDL_IMPL_STATUS=failed"
    puts "TIDL_IMPL_STAGE=opt_design"
    puts "TIDL_IMPL_ERROR=$err"
    set kv [open [file join $outdir metrics.txt] a]
    puts $kv "TIDL_IMPL_STATUS=failed"
    puts $kv "TIDL_IMPL_STAGE=opt_design"
    close $kv
    exit 1
  }}
  if {{[catch {{{place_cmd}}} err]}} {{
    puts "TIDL_IMPL_STATUS=failed"
    puts "TIDL_IMPL_STAGE=place_design"
    puts "TIDL_IMPL_ERROR=$err"
    set kv [open [file join $outdir metrics.txt] a]
    puts $kv "TIDL_IMPL_STATUS=failed"
    puts $kv "TIDL_IMPL_STAGE=place_design"
    close $kv
    exit 1
  }}
  if {{[catch {{{route_cmd}}} err]}} {{
    puts "TIDL_IMPL_STATUS=failed"
    puts "TIDL_IMPL_STAGE=route_design"
    puts "TIDL_IMPL_ERROR=$err"
    set kv [open [file join $outdir metrics.txt] a]
    puts $kv "TIDL_IMPL_STATUS=failed"
    puts $kv "TIDL_IMPL_STAGE=route_design"
    close $kv
    exit 1
  }}
  puts "TIDL_IMPL_STATUS=ok"
  set kv [open [file join $outdir metrics.txt] a]
  puts $kv "TIDL_IMPL_STATUS=ok"
  close $kv

  report_utilization -file [file join $outdir utilization_impl.rpt]
  report_timing_summary -file [file join $outdir timing_summary.rpt]
  report_methodology -file [file join $outdir methodology.rpt]
  report_drc -file [file join $outdir drc_impl.rpt]
  report_route_status -file [file join $outdir route_status.rpt]
  report_clock_utilization -file [file join $outdir clock_utilization.rpt]

  set locf [open [file join $outdir carry_locs.txt] w]
  puts $locf "# cell loc bel"
  foreach c [lsort [get_cells -quiet -hierarchical -filter {{REF_NAME == CARRY4}}]] {{
    set loc [get_property LOC $c]
    set bel [get_property BEL $c]
    puts $locf "[get_property NAME $c] $loc $bel"
  }}
  close $locf
}} else {{
  puts "TIDL_IMPL_STATUS=skipped"
  set kv [open [file join $outdir metrics.txt] a]
  puts $kv "TIDL_IMPL_STATUS=skipped"
  close $kv
}}

puts "TIDL_DONE=1"
exit 0
"""
