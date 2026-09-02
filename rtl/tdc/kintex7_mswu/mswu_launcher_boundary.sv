// MSWU launcher boundary (structural surrogate only).
//
// Wave Union pulse generation and transient behavior are NOT validated by
// Vivado. This module does not reproduce the paper's 3.5 GHz launcher or
// pulse widths. No #delay picosecond tricks.

`timescale 1ns/1ps

module mswu_launcher_boundary (
    input  logic clk,
    input  logic rst_n,
    input  logic wu_arm,
    input  logic hit,
    output logic launch_sample
);

  logic armed_q;

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      armed_q       <= 1'b0;
      launch_sample <= 1'b0;
    end else begin
      armed_q       <= wu_arm;
      // Registered surrogate strobe: structural placeholder only.
      launch_sample <= armed_q & hit;
    end
  end

endmodule
