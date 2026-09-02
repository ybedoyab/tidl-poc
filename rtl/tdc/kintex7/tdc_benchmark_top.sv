// Out-of-context resource / place-route benchmark top for Kintex-7 TDL.
//
// Timing-clean observability: the full capture FF bank is retained via
// KEEP / DONT_TOUCH on the structural capture path. Only one registered bit
// per channel (chain-0 tap 0) is exposed as bench_status. There is no wide
// XOR parity tree. This is not a TDC code, not DNL, and not 1 ps resolution.
//
// Round-6 used wide parity reduction (see legacy/ and docs/evidence/vivado_kintex7/).

`timescale 1ns/1ps

module tdc_benchmark_top #(
    parameter int N_CHANNELS = 1,
    parameter int N_CHAINS   = 8,
    parameter int N_CARRY4   = 32
) (
    input  logic                     clk,
    input  logic                     rst_n,
    input  logic [N_CHANNELS-1:0]    hit,
    output logic [N_CHANNELS-1:0]    bench_status,
    output logic [N_CHANNELS-1:0]    channel_valid
);

  localparam int N_TAPS_CHAIN = 4 * N_CARRY4;

  logic [N_CHANNELS-1:0] ch_sample;
  logic [N_CHANNELS-1:0] encoder_ready_unused;
  logic [N_CHANNELS-1:0] cal_strobe_unused;

  genvar c;
  generate
    for (c = 0; c < N_CHANNELS; c++) begin : gen_ch
      (* KEEP = "TRUE", DONT_TOUCH = "TRUE" *)
      logic [N_CHAINS*N_TAPS_CHAIN-1:0] captured_bus;
      logic [N_CHAINS-1:0]              chain_sample;

      multi_chain_tdc_structural #(
          .N_CHAINS(N_CHAINS),
          .N_CARRY4(N_CARRY4)
      ) u_ch (
          .clk          (clk),
          .rst_n        (rst_n),
          .hit          (hit[c]),
          .captured     (captured_bus),
          .chain_sample (chain_sample),
          .encoder_ready(encoder_ready_unused[c]),
          .cal_strobe   (cal_strobe_unused[c])
      );

      // One representative bit per channel (chain 0, tap 0).
      assign ch_sample[c] = chain_sample[0];
    end
  endgenerate

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      bench_status  <= '0;
      channel_valid <= '0;
    end else begin
      bench_status  <= ch_sample;
      channel_valid <= hit;
    end
  end

endmodule
