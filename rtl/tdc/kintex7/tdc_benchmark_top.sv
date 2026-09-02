// Out-of-context resource / place-route benchmark top for Kintex-7 TDL.
//
// Dummy tap_parity exists only to keep capture FFs alive. It is not a TDC
// code, not DNL, and not 1 ps resolution. No board package pins are implied.

`timescale 1ns/1ps

module tdc_benchmark_top #(
    parameter int N_CHANNELS = 1,
    parameter int N_CHAINS   = 8,
    parameter int N_CARRY4   = 32
) (
    input  logic                     clk,
    input  logic                     rst_n,
    input  logic [N_CHANNELS-1:0]    hit,
    output logic                     tap_parity,
    output logic [N_CHANNELS-1:0]    channel_valid
);

  localparam int N_TAPS_CHAIN = 4 * N_CARRY4;

  logic [N_CHANNELS-1:0] ch_parity;
  logic [N_CHANNELS-1:0] encoder_ready_unused;
  logic [N_CHANNELS-1:0] cal_strobe_unused;

  genvar c;
  generate
    for (c = 0; c < N_CHANNELS; c++) begin : gen_ch
      logic [N_CHAINS*N_TAPS_CHAIN-1:0] captured_unused;
      logic [N_CHAINS-1:0]              chain_parity;

      multi_chain_tdc_structural #(
          .N_CHAINS(N_CHAINS),
          .N_CARRY4(N_CARRY4)
      ) u_ch (
          .clk          (clk),
          .rst_n        (rst_n),
          .hit          (hit[c]),
          .captured     (captured_unused),
          .chain_parity (chain_parity),
          .encoder_ready(encoder_ready_unused[c]),
          .cal_strobe   (cal_strobe_unused[c])
      );

      assign ch_parity[c] = ^chain_parity;
    end
  endgenerate

  // Two-stage register so the dummy observability net is synchronous control
  // logic, separate from the asynchronous carry structure.
  logic [N_CHANNELS-1:0] ch_parity_q;

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      ch_parity_q   <= '0;
      tap_parity    <= 1'b0;
      channel_valid <= '0;
    end else begin
      ch_parity_q   <= ch_parity;
      tap_parity    <= ^ch_parity_q;
      channel_valid <= hit;
    end
  end

endmodule
