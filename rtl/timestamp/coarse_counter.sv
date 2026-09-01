// Signed coarse counter.
// WIDTH is arithmetic feasibility only. Clock accuracy over ±1 s is a
// reference-stability problem (NIST SP 1065 / IEEE 1139), not a bit width.
//
// Suggested WIDTH vs coarse clock for ±1 s (two's complement):
//   100 MHz -> 28 bits
//   200 MHz -> 29 bits
//   400 MHz -> 30 bits
//   500 MHz -> 30 bits

`timescale 1ns/1ps

module coarse_counter #(
    parameter int WIDTH = 28
) (
    input  logic                      clk,
    input  logic                      rst_n,
    input  logic                      enable,
    input  logic                      load,
    input  logic signed [WIDTH-1:0]   load_value,
    output logic signed [WIDTH-1:0]   count,
    output logic                      wrapping  // high for one cycle on signed overflow
);
  logic signed [WIDTH-1:0] next_count;
  logic                    ovf;

  always_comb begin
    next_count = count + 1'sd1;
    ovf = enable && (count == {1'b0, {(WIDTH-1){1'b1}}});
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count    <= '0;
      wrapping <= 1'b0;
    end else if (load) begin
      count    <= load_value;
      wrapping <= 1'b0;
    end else if (enable) begin
      count    <= next_count;
      wrapping <= ovf;
    end else begin
      wrapping <= 1'b0;
    end
  end
endmodule
