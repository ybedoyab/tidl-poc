// Pipelined shared low-rate post-processing surrogate (16 events/s class).
//
// Sixteen independent TDL/capture front-ends are NOT shared. Only this
// post-capture pre-encoder path is shared across channels.
// Pipeline stages break wide mux / encoder fanout for 4 ns benchmark closure.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module mswu_lowrate_shared_post #(
    parameter int N_CHANNELS = 16
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic [N_CHANNELS-1:0]   cap_valid,
    input  logic [199:0]            captured_flat [N_CHANNELS],
    output logic [10:0]             shared_code,
    output logic                    shared_valid,
    output logic [$clog2(N_CHANNELS)-1:0] active_channel,
    output logic [10:0]             bench_codes [5],
    output logic                    bench_valid [5]
);

  localparam int CHW = (N_CHANNELS <= 1) ? 1 : $clog2(N_CHANNELS);

  logic [CHW-1:0] ch_idx;
  logic [2:0]     sub_idx;
  logic [CHW-1:0] ch_idx_r;
  logic [2:0]     sub_idx_r;
  logic [199:0]   selected_cap_r;
  logic [10:0]    enc_raw;
  logic           enc_valid;

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      ch_idx_r       <= '0;
      sub_idx_r      <= '0;
      selected_cap_r <= '0;
    end else begin
      ch_idx_r       <= ch_idx;
      sub_idx_r      <= sub_idx;
      selected_cap_r <= captured_flat[ch_idx];
    end
  end

  mswu_mbd5_preencoder_surrogate u_pre (
      .clk      (clk),
      .rst_n    (rst_n),
      .captured (selected_cap_r),
      .sub_sel  (sub_idx_r),
      .encoded  (enc_raw),
      .valid    (enc_valid)
  );

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      shared_code    <= '0;
      shared_valid   <= 1'b0;
      for (int s = 0; s < 5; s++) begin
        bench_codes[s] <= '0;
        bench_valid[s] <= 1'b0;
      end
    end else begin
      shared_valid <= enc_valid;
      shared_code  <= enc_raw;
      if (enc_valid) begin
        bench_codes[sub_idx_r] <= enc_raw;
        bench_valid[sub_idx_r] <= 1'b1;
      end
    end
  end

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      ch_idx  <= '0;
      sub_idx <= '0;
    end else begin
      if (sub_idx == 3'd4) begin
        sub_idx <= '0;
        if (ch_idx == N_CHANNELS - 1) ch_idx <= '0;
        else ch_idx <= ch_idx + 1'b1;
      end else begin
        sub_idx <= sub_idx + 1'b1;
      end
    end
  end

  assign active_channel = ch_idx_r;

endmodule
