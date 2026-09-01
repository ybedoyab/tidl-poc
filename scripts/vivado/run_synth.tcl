# Synthesis. Open the project created by create_project.tcl.
# Not used in CI. Results are not timing-closure evidence for a TDC.

set root [file normalize [file join [file dirname [info script]] ../..]]
set proj [file join $root vivado_proj tidl_poc.xpr]

if {![file exists $proj]} {
  puts "ERROR: $proj not found. Run create_project.tcl first."
  exit 1
}

open_project $proj
reset_run synth_1
launch_runs synth_1
wait_on_run synth_1
puts "synth_1 complete. Classify any numbers as RTL/synthesis evidence, not measurement."
