// OOC MSWU-inspired structural benchmark top.
//
// Variants (parameters frozen in generated wrap):
//   CORE_ONLY     — TDL + 4 capture banks per channel
//   WITH_PREENC   — + per-channel MBD=5 pre-encoder surrogate
//   LOWRATE_MULTI — N independent front-ends + one shared post FSM

`timescale 1ns/1ps

module mswu_benchmark_top #(
    parameter int  N_CHANNELS = 1,
    parameter bit  INCLUDE_PREENCODER = 1'b0,
    parameter bit  SHARED_POST = 1'b0
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic [N_CHANNELS-1:0]   hit,
    input  logic [N_CHANNELS-1:0]   wu_arm,
    output logic [N_CHANNELS-1:0]   bench_status,
    output logic [10:0]             shared_code,
    output logic                    shared_valid
);

  genvar c;
  generate
    if (!SHARED_POST) begin : gen_per_channel
      for (c = 0; c < N_CHANNELS; c++) begin : gen_ch
        mswu_channel_core #(
            .INCLUDE_PREENCODER(INCLUDE_PREENCODER)
        ) u_ch (
            .clk          (clk),
            .rst_n        (rst_n),
            .hit          (hit[c]),
            .wu_arm       (wu_arm[c]),
            .bank_alive   (),
            .preenc_code  (),
            .preenc_valid (),
            .bench_status (bench_status[c])
        );
      end
      assign shared_code  = '0;
      assign shared_valid = 1'b0;
    end else begin : gen_lowrate
      logic [199:0] captured_flat [N_CHANNELS];
      logic [N_CHANNELS-1:0] cap_valid;

      for (c = 0; c < N_CHANNELS; c++) begin : gen_fe
        logic [199:0] taps_k;
        logic [199:0] cap_k [4];
        logic [3:0]   alive_k;

        mswu_tdl_200 u_tdl (
            .hit (hit[c]),
            .taps(taps_k)
        );
        mswu_capture_quad u_cq (
            .clk        (clk),
            .rst_n      (rst_n),
            .tdl_taps   (taps_k),
            .captured   (cap_k),
            .bank_alive (alive_k)
        );
        assign captured_flat[c] = cap_k[0];
        assign cap_valid[c]     = cap_k[0][0];
        assign bench_status[c]  = alive_k[0];
      end

      mswu_lowrate_shared_post #(
          .N_CHANNELS(N_CHANNELS)
      ) u_post (
          .clk            (clk),
          .rst_n          (rst_n),
          .cap_valid      (cap_valid),
          .captured_flat  (captured_flat),
          .shared_code    (shared_code),
          .shared_valid   (shared_valid),
          .active_channel ()
      );
    end
  endgenerate

endmodule
