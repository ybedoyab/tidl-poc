// Calibration LUT access. Version must be copied into every timestamp record.
// Physical bin widths come from on-instrument histograms, not from this interface.

interface calibration_lut_if #(
    parameter int ADDR_W = 9,
    parameter int DATA_W = 16,
    parameter int VER_W  = 16
);
  logic               req;
  logic [ADDR_W-1:0]  addr;
  logic [DATA_W-1:0]  width_ps_q;  // quantized width representation; not a claim of 1 ps physics
  logic [VER_W-1:0]   cal_version;
  logic               ack;

  modport host (output req, addr, input width_ps_q, cal_version, ack);
  modport mem  (input  req, addr, output width_ps_q, cal_version, ack);
endinterface
