// Placeholder: LUT storage for code-density widths and version.

`timescale 1ns/1ps

module calibration_lut_stub #(
    parameter int ADDR_W = 9,
    parameter int DATA_W = 16
) (
    input  logic               clk,
    input  logic               rst_n,
    input  logic               req,
    input  logic [ADDR_W-1:0]  addr,
    output logic [DATA_W-1:0]  width_ps_q,
    output logic [15:0]        cal_version,
    output logic               ack
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      width_ps_q  <= '0;
      cal_version <= 16'd1;
      ack         <= 1'b0;
    end else begin
      ack        <= req;
      width_ps_q <= '0;
    end
  end
endmodule
