# Collect reports. Do not check generated reports into git.
# Intended set:
#   utilization synth/impl, timing summary, clock utilization,
#   methodology, DRC, TDC cell placement, power, route status.
# Resource scaling for 1/4/8/16 channels is a separate parameter sweep, not
# performed by this script.

set root [file normalize [file join [file dirname [info script]] ../..]]
set proj [file join $root vivado_proj tidl_poc.xpr]
set rpt_dir [file join $root outputs vivado_reports]

if {![file exists $proj]} {
  puts "ERROR: $proj not found."
  exit 1
}

file mkdir $rpt_dir
open_project $proj

open_run impl_1
report_utilization -file [file join $rpt_dir utilization_impl.rpt]
report_timing_summary -file [file join $rpt_dir timing_summary.rpt]
report_clock_utilization -file [file join $rpt_dir clock_utilization.rpt]
report_methodology -file [file join $rpt_dir methodology.rpt]
report_drc -file [file join $rpt_dir drc.rpt]
report_power -file [file join $rpt_dir power.rpt]
report_route_status -file [file join $rpt_dir route_status.rpt]
# TDC placement: filter once carry primitives are instantiated.
report_utilization -hierarchical -file [file join $rpt_dir utilization_hier.rpt]

puts "Reports written under $rpt_dir (gitignored via outputs/)."
