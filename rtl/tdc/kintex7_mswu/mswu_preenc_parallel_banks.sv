// Per-bank fully parallel MBD=5 pre-encoder surrogate (upper-bound resource test).
//
// Four capture banks × five fixed subregion encoders (20 instances total).
// Project surrogate — not bit-equivalent to Kwiatkowski et al.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module mswu_preenc_parallel_banks #(
    parameter int N_BANKS = 4,
    parameter int N_SUB = 5,
    parameter int OUT_BITS = 11
) (
    input  logic                          clk,
    input  logic                          rst_n,
    input  logic [199:0]                  captured [N_BANKS],
    output logic [OUT_BITS-1:0]           bench_codes [N_BANKS][N_SUB],
    output logic                          bench_valid [N_BANKS][N_SUB]
);

  genvar b, s;
  generate
    for (b = 0; b < N_BANKS; b++) begin : gen_bank
      for (s = 0; s < N_SUB; s++) begin : gen_sub
        mswu_mbd5_preencoder_surrogate u_pre (
            .clk      (clk),
            .rst_n    (rst_n),
            .captured (captured[b]),
            .sub_sel  (s[2:0]),
            .encoded  (bench_codes[b][s]),
            .valid    (bench_valid[b][s])
        );
      end
    end
  endgenerate

endmodule
