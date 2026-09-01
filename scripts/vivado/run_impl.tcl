# Implementation. Not used in CI.

set root [file normalize [file join [file dirname [info script]] ../..]]
set proj [file join $root vivado_proj tidl_poc.xpr]

if {![file exists $proj]} {
  puts "ERROR: $proj not found. Run create_project.tcl and run_synth.tcl first."
  exit 1
}

open_project $proj
launch_runs impl_1
wait_on_run impl_1
puts "impl_1 complete. Carry-chain placement still requires dedicated constraints."
