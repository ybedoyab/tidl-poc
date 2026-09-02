"""Generate Vivado Tcl for MSWU-inspired structural benchmarks."""

from __future__ import annotations

from pathlib import Path


def _posix(path: Path) -> str:
    return path.resolve().as_posix()


def generate_mswu_wrap_sv(
    *,
    case_id: str,
    n_channels: int,
    include_preencoder: bool,
    shared_post: bool,
) -> str:
    pre = 1 if include_preencoder else 0
    shared = 1 if shared_post else 0
    return f"""// Generated MSWU structural wrap — {case_id}
`timescale 1ns/1ps
module mswu_benchmark_wrap (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic [{n_channels - 1}:0] hit,
    input  logic [{n_channels - 1}:0] wu_arm,
    output logic [{n_channels - 1}:0] bench_status,
    output logic [10:0]             shared_code,
    output logic                    shared_valid
);
  mswu_benchmark_top #(
      .N_CHANNELS({n_channels}),
      .INCLUDE_PREENCODER({pre}),
      .SHARED_POST({shared})
  ) u_top (
      .clk          (clk),
      .rst_n        (rst_n),
      .hit          (hit),
      .wu_arm       (wu_arm),
      .bench_status (bench_status),
      .shared_code  (shared_code),
      .shared_valid (shared_valid)
  );
endmodule
"""


def generate_mswu_case_tcl(
    *,
    part: str,
    rtl_dir: Path,
    kintex7_rtl_dir: Path,
    xdc_path: Path,
    wrap_path: Path,
    out_dir: Path,
    n_carry4_per_tdl: int,
    expected_capture_ff: int,
    place_guide: bool = True,
) -> str:
    rtl = _posix(rtl_dir)
    k7 = _posix(kintex7_rtl_dir)
    xdc = _posix(xdc_path)
    wrap = _posix(wrap_path)
    out = _posix(out_dir)
    place_flag = 1 if place_guide else 0
    return f"""# Generated MSWU structural benchmark. No bitstream. No board pins.
set_param general.maxThreads 8
set part {{{part}}}
set outdir {{{out}}}
set do_impl 1
set do_place_guide {place_flag}
set n_carry4_per_tdl {n_carry4_per_tdl}
set expected_capture_ff {expected_capture_ff}
file mkdir $outdir

read_verilog -sv [list \\
  {{{k7}/carry4_tdl_chain.sv}} \\
  {{{k7}/tdc_capture_bank.sv}} \\
  {{{rtl}/mswu_launcher_boundary.sv}} \\
  {{{rtl}/mswu_tdl_200.sv}} \\
  {{{rtl}/mswu_capture_quad.sv}} \\
  {{{rtl}/mswu_mbd5_preencoder_surrogate.sv}} \\
  {{{rtl}/mswu_channel_core.sv}} \\
  {{{rtl}/mswu_lowrate_shared_post.sv}} \\
  {{{rtl}/mswu_benchmark_top.sv}} \\
  {{{wrap}}} \\
]
read_xdc [list {{{xdc}}}]

if {{[catch {{synth_design -mode out_of_context -top mswu_benchmark_wrap -part $part}} err]}} {{
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
set bram_n  [tidl_count_ref RAMB36E1]
if {{$bram_n == 0}} {{ set bram_n [tidl_count_ref RAMB18E1] }}

puts "TIDL_CARRY4_COUNT=$carry_n"
puts "TIDL_FDRE_COUNT=$fdre_n"
puts "TIDL_BRAM_COUNT=$bram_n"

set kv [open [file join $outdir metrics.txt] w]
puts $kv "TIDL_SYNTH_STATUS=ok"
puts $kv "TIDL_CARRY4_COUNT=$carry_n"
puts $kv "TIDL_FDRE_COUNT=$fdre_n"
puts $kv "TIDL_BRAM_COUNT=$bram_n"
puts $kv "TIDL_CAPTURE_FF_EXPECTED=$expected_capture_ff"
if {{$fdre_n < $expected_capture_ff}} {{
  puts $kv "TIDL_CAPTURE_FF_SHORTFALL=1"
}} else {{
  puts $kv "TIDL_CAPTURE_FF_SHORTFALL=0"
}}
close $kv

report_utilization -file [file join $outdir utilization_synth.rpt]
report_utilization -hierarchical -file [file join $outdir utilization_hier_synth.rpt]
report_drc -file [file join $outdir drc_synth.rpt]

proc tidl_place_carry4_vertical {{n_carry4}} {{
  set cells [get_cells -quiet -hierarchical -filter {{REF_NAME == CARRY4}}]
  if {{[llength $cells] == 0}} {{ return }}
  array set groups {{}}
  foreach c $cells {{
    set name [get_property NAME $c]
    if {{[regexp {{^(.*gen_carry)\\[(\\d+)\\]}} $name -> prefix idx]}} {{
      lappend groups($prefix) [list $idx $c]
    }}
  }}
  array set col {{}}
  foreach s [get_sites -quiet -filter {{SITE_TYPE == SLICEL || SITE_TYPE == SLICEM}}] {{
    if {{[regexp {{SLICE_X(\\d+)Y(\\d+)}} $s -> x y]}} {{ lappend col($x) $y }}
  }}
  set slots {{}}
  foreach x [lsort -integer [array names col]] {{
    foreach y [lsort -integer -unique $col($x)] {{ lappend slots [list $x $y] }}
  }}
  set ns [llength $slots]
  set off 0
  foreach prefix [lsort [array names groups]] {{
    set members [lsort -integer -index 0 $groups($prefix)]
    set n [llength $members]
    for {{set i $off}} {{$i < $ns}} {{incr i}} {{
      if {{($i + $n) > $ns}} {{ break }}
      set xy [lindex $slots $i]
      set x0 [lindex $xy 0]
      set y0 [lindex $xy 1]
      set ok 1
      for {{set k 1}} {{$k < $n}} {{incr k}} {{
        set xy2 [lindex $slots [expr {{$i + $k}}]]
        if {{[lindex $xy2 0] != $x0 || [lindex $xy2 1] != ($y0 + $k)}} {{ set ok 0; break }}
      }}
      if {{!$ok}} {{ continue }}
      set j 0
      foreach m $members {{
        set cell [lindex $m 1]
        if {{[catch {{set_property LOC "SLICE_X${{x0}}Y${{y0 + $j}}" $cell}} err]}} {{ set ok 0; break }}
        incr j
      }}
      if {{$ok}} {{ set off [expr {{$i + $n}}]; break }}
    }}
  }}
}}

if {{$do_place_guide}} {{ tidl_place_carry4_vertical $n_carry4_per_tdl }}

if {{[catch {{opt_design}} err]}} {{
  puts "TIDL_IMPL_STATUS=failed"
  exit 1
}}
if {{[catch {{place_design}} err]}} {{
  puts "TIDL_IMPL_STATUS=failed"
  exit 1
}}
if {{[catch {{route_design}} err]}} {{
  puts "TIDL_IMPL_STATUS=failed"
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
report_timing -max_paths 10 -path_type full -file [file join $outdir timing_paths.rpt]

set locf [open [file join $outdir carry_locs.txt] w]
puts $locf "# cell loc bel"
foreach c [lsort [get_cells -quiet -hierarchical -filter {{REF_NAME == CARRY4}}]] {{
  puts $locf "[get_property NAME $c] [get_property LOC $c] [get_property BEL $c]"
}}
close $locf

puts "TIDL_DONE=1"
exit 0
"""
