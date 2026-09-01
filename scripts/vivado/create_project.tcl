# Create a Vivado project. Requires Vivado on PATH. Not used in CI.
# Part must be provided:  set TIDL_PART <part>   or  set ::env(TIDL_PART)
#
# Candidates (not a selection):
#   Kintex-7 example:            xc7k325tffg900-2
#   Kintex UltraScale:           xcku025-ffva1156-1-e / xcku035-ffva1156-1-e
#   Kintex UltraScale+:          xcku3p-ffvb676-1-e / xcku5p-ffvb676-2-e

set root [file normalize [file join [file dirname [info script]] ../..]]

if {[info exists ::env(TIDL_PART)] && $::env(TIDL_PART) ne ""} {
  set part $::env(TIDL_PART)
} elseif {[info exists TIDL_PART] && $TIDL_PART ne ""} {
  set part $TIDL_PART
} else {
  puts "ERROR: set TIDL_PART to a device. No default part is defined."
  exit 1
}

set proj_dir [file join $root vivado_proj]
set proj_name tidl_poc

create_project $proj_name $proj_dir -part $part -force

set rtl_files [list \
  [file join $root rtl timestamp coarse_counter.sv] \
  [file join $root rtl timestamp timestamp_combiner.sv] \
  [file join $root rtl tdc tdc_chain_if.sv] \
  [file join $root rtl tdc tdc_carry4_7series.sv] \
  [file join $root rtl tdc tdc_carry8_ultrascale.sv] \
  [file join $root rtl calibration calibration_lut_stub.sv] \
  [file join $root rtl logging logger_stub.sv] \
  [file join $root rtl top tidl_top.sv] \
]

add_files -norecurse $rtl_files
set_property top tidl_top [current_fileset]

# Constraints are family folders; pick one explicitly when a board exists.
puts "Project created for part $part. Add the matching constraints/*.xdc before impl."
puts "This is not TDC performance evidence."
