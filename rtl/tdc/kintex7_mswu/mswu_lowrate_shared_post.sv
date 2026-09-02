// Shared low-rate post-processing surrogate (16 events/s class).
//
// Sixteen independent TDL/capture front-ends are NOT shared. Only this
// post-capture pre-encoder FSM is shared across channels.

`timescale 1ns/1ps

module mswu_lowrate_shared_post #(
    parameter int N_CHANNELS = 16
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic [N_CHANNELS-1:0]   cap_valid,
    input  logic [199:0]            captured_flat [N_CHANNELS],
    output logic [10:0]             shared_code,
    output logic                    shared_valid,
    output logic [$clog2(N_CHANNELS)-1:0] active_channel
);

  localparam int CHW = (N_CHANNELS <= 1) ? 1 : $clog2(N_CHANNELS);

  logic [CHW-1:0] ch_idx;
  logic [2:0]     sub_idx;
  logic [199:0]   selected_cap;

  always_comb begin
    selected_cap = captured_flat[ch_idx];
  end

  mswu_mbd5_preencoder_surrogate u_pre (
      .clk      (clk),
      .rst_n    (rst_n),
      .captured (selected_cap),
      .sub_sel  (sub_idx),
      .encoded  (shared_code),
      .valid    (shared_valid)
  );

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

  assign active_channel = ch_idx;

endmodule
