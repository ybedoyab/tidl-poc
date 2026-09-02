// MBD=5 bubble-resistant pre-encoder SURROGATE (project-original).
//
// Partitions a 200-bit capture word into five 40-bit sub-TDL regions consistent
// with the paper's high-level MBD=5 concept. Output is 11 bits per invocation:
//   [10:6] first-set index within sub-TDL (0–39, capped)
//   [5:1]  last-set index within sub-TDL
//   [0]    any-bit-set in sub-TDL
//
// This is NOT bit-equivalent to the paper's 200→11 pre-encoder. Label:
// project surrogate. Invariants tested in Python unit tests.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module mswu_mbd5_preencoder_surrogate #(
    parameter int N_TAPS = 200,
    parameter int SUB_BITS = 40,
    parameter int N_SUB = 5,
    parameter int OUT_BITS = 11
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic [N_TAPS-1:0]       captured,
    input  logic [2:0]              sub_sel,
    output logic [OUT_BITS-1:0]     encoded,
    output logic                    valid
);

  logic [SUB_BITS-1:0] sub_word;
  logic [5:0]          first_idx;
  logic [5:0]          last_idx;
  logic                any_set;

  always_comb begin
    unique case (sub_sel)
      3'd0: sub_word = captured[39:0];
      3'd1: sub_word = captured[79:40];
      3'd2: sub_word = captured[119:80];
      3'd3: sub_word = captured[159:120];
      3'd4: sub_word = captured[199:160];
      default: sub_word = '0;
    endcase
  end

  always_comb begin
    first_idx = 6'd63;
    last_idx  = 6'd0;
    any_set   = 1'b0;
    for (int i = 0; i < SUB_BITS; i++) begin
      if (sub_word[i]) begin
        any_set = 1'b1;
        if (i < first_idx) first_idx = i[5:0];
        if (i > last_idx) last_idx = i[5:0];
      end
    end
    if (!any_set) begin
      first_idx = 6'd0;
      last_idx  = 6'd0;
    end
  end

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      encoded <= '0;
      valid   <= 1'b0;
    end else begin
      valid   <= 1'b1;
      encoded <= {first_idx[4:0], last_idx[4:0], any_set};
    end
  end

endmodule
