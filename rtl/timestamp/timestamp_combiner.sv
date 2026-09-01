// Combine signed coarse count with a non-negative fine time.
// delta_ps = coarse * T_REF_PS + fine_ps
//
// Fine quantization (for example 1 ps digital LSB) is not physical resolution.
// Negative intervals use a negative coarse count plus a fine remainder in
// [0, T_REF_PS). See src/tidl_poc/models/coarse_fine.py for the software twin.

`timescale 1ns/1ps

module timestamp_combiner #(
    parameter int COARSE_W   = 32,
    parameter int FINE_W     = 16,
    parameter int OUT_W      = 64,
    parameter int T_REF_PS   = 10000  // 10 ns @ 100 MHz; parameter, not a measured period
) (
    input  logic                      clk,
    input  logic                      rst_n,
    input  logic                      valid_i,
    input  logic signed [COARSE_W-1:0] coarse,
    input  logic        [FINE_W-1:0]  fine_ps,
    output logic                      valid_o,
    output logic signed [OUT_W-1:0]   delta_ps
);
  logic signed [OUT_W-1:0] coarse_ps;
  logic signed [OUT_W-1:0] fine_ext;

  always_comb begin
    coarse_ps = $signed(coarse) * $signed(OUT_W'(T_REF_PS));
    fine_ext  = $signed({1'b0, fine_ps});
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_o  <= 1'b0;
      delta_ps <= '0;
    end else begin
      valid_o  <= valid_i;
      if (valid_i) begin
        delta_ps <= coarse_ps + fine_ext;
      end
    end
  end
endmodule
