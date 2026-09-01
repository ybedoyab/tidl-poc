// Placeholder internal logger handshake. Record schema is defined in
// src/tidl_poc/models/packet_logging.py (software/data-path evidence).

`timescale 1ns/1ps

module logger_stub #(
    parameter int DATA_W = 128
) (
    input  logic              clk,
    input  logic              rst_n,
    input  logic              wr_valid,
    input  logic [DATA_W-1:0] wr_data,
    output logic              wr_ready,
    output logic              overflow
);
  assign wr_ready = rst_n;
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) overflow <= 1'b0;
    else if (wr_valid && !wr_ready) overflow <= 1'b1;
  end
endmodule
