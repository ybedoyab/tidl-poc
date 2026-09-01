// Architectural interface for a fine TDC channel.
// THIS IS NOT A 1 ps TIME-TO-DIGITAL CONVERTER.
// Physical interpolators require device-specific carry primitives, placement
// constraints, bubble-resistant encoding, and measured calibration.

`timescale 1ns/1ps

module tdc_chain_if_stub #(
    parameter int CODE_W = 16
) (
    input  logic              clk,
    input  logic              rst_n,
    input  logic              hit,
    output logic              valid,
    output logic [CODE_W-1:0] code
);
  // Protocol-only stub. Do not interpret `code` as time.
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid <= 1'b0;
      code  <= '0;
    end else begin
      valid <= hit;
      code  <= '0;
    end
  end
endmodule
