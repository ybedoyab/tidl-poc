// Low-rate sequential MBD=5 pre-encoder scanner (project surrogate).
//
// Scans four capture banks × five 40-bit subregions over multiple cycles.
// All encoded results are registered and retained for benchmark observability.
// NOT bit-equivalent to Kwiatkowski et al. pre-encoder.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module mswu_preenc_seq_scanner #(
    parameter int N_BANKS = 4,
    parameter int N_SUB = 5,
    parameter int OUT_BITS = 11
) (
    input  logic                          clk,
    input  logic                          rst_n,
    input  logic [199:0]                  captured [N_BANKS],
    output logic [2:0]                    bank_sel,
    output logic [2:0]                    sub_sel,
    output logic [OUT_BITS-1:0]           encoded,
    output logic                          valid,
    output logic                          scan_complete,
    output logic [OUT_BITS-1:0]           bench_codes [N_BANKS][N_SUB],
    output logic                          bench_valid [N_BANKS][N_SUB]
);

  logic [2:0] bank_r;
  logic [2:0] sub_r;
  logic [199:0] cap_r;
  logic [OUT_BITS-1:0] enc_raw;
  logic enc_valid;

  assign bank_sel = bank_r;
  assign sub_sel  = sub_r;

  always_ff @(posedge clk) begin
    if (!rst_n) cap_r <= '0;
    else cap_r <= captured[bank_r];
  end

  mswu_mbd5_preencoder_surrogate u_pre (
      .clk      (clk),
      .rst_n    (rst_n),
      .captured (cap_r),
      .sub_sel  (sub_r),
      .encoded  (enc_raw),
      .valid    (enc_valid)
  );

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      encoded       <= '0;
      valid         <= 1'b0;
      scan_complete <= 1'b0;
      bank_r        <= '0;
      sub_r         <= '0;
      for (int b = 0; b < N_BANKS; b++) begin
        for (int s = 0; s < N_SUB; s++) begin
          bench_codes[b][s] <= '0;
          bench_valid[b][s] <= 1'b0;
        end
      end
    end else begin
      valid         <= enc_valid;
      encoded       <= enc_raw;
      scan_complete <= 1'b0;
      if (enc_valid) begin
        bench_codes[bank_r][sub_r] <= enc_raw;
        bench_valid[bank_r][sub_r] <= 1'b1;
      end
      if (enc_valid) begin
        if (sub_r == N_SUB - 1) begin
          sub_r <= '0;
          if (bank_r == N_BANKS - 1) begin
            bank_r        <= '0;
            scan_complete <= 1'b1;
          end else begin
            bank_r <= bank_r + 1'b1;
          end
        end else begin
          sub_r <= sub_r + 1'b1;
        end
      end
    end
  end

endmodule
