// OOC MSWU-inspired structural benchmark top.
//
// PREENC_MODE: 0=none, 1=sequential scanner, 2=parallel banks×regions
// SHARED_POST: 16 independent front-ends + pipelined shared post FSM

`timescale 1ns/1ps

module mswu_benchmark_top #(
    parameter int  N_CHANNELS = 1,
    parameter int  PREENC_MODE = 0,
    parameter bit  SHARED_POST = 1'b0
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic [N_CHANNELS-1:0]   hit,
    input  logic [N_CHANNELS-1:0]   wu_arm,
    output logic [N_CHANNELS-1:0]   bench_status,
    output logic [10:0]             shared_code,
    output logic                    shared_valid,
    output logic [10:0]             preenc_flat [20],
    output logic                    preenc_flat_valid [20]
);

  genvar c, i;
  generate
    if (!SHARED_POST) begin : gen_per_channel
      logic [10:0] codes_0 [4][5];
      logic        valid_0 [4][5];

      for (c = 0; c < N_CHANNELS; c++) begin : gen_ch
        if (c == 0) begin : ch0
          mswu_channel_core #(
              .PREENC_MODE(PREENC_MODE)
          ) u_ch (
              .clk           (clk),
              .rst_n         (rst_n),
              .hit           (hit[c]),
              .wu_arm        (wu_arm[c]),
              .bank_alive    (),
              .preenc_code   (),
              .preenc_valid  (),
              .scan_complete (),
              .bench_codes   (codes_0),
              .bench_valid   (valid_0),
              .bench_status  (bench_status[c])
          );
        end else begin : chn
          mswu_channel_core #(
              .PREENC_MODE(0)
          ) u_ch (
              .clk           (clk),
              .rst_n         (rst_n),
              .hit           (hit[c]),
              .wu_arm        (wu_arm[c]),
              .bank_alive    (),
              .preenc_code   (),
              .preenc_valid  (),
              .scan_complete (),
              .bench_codes   (),
              .bench_valid   (),
              .bench_status  (bench_status[c])
          );
        end
      end

      for (i = 0; i < 20; i++) begin : gen_flat
        localparam int BANK = i / 5;
        localparam int SUB  = i % 5;
        assign preenc_flat[i]       = codes_0[BANK][SUB];
        assign preenc_flat_valid[i] = valid_0[BANK][SUB];
      end

      assign shared_code = preenc_flat[0];

      always_comb begin
        shared_valid = 1'b0;
        for (int i = 0; i < 20; i++) begin
          shared_valid = shared_valid | preenc_flat_valid[i];
        end
      end
    end else begin : gen_lowrate
      logic [199:0] captured_flat [N_CHANNELS];
      logic [N_CHANNELS-1:0] cap_valid;
      logic [10:0] post_codes [5];
      logic        post_valid [5];

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
          .active_channel (),
          .bench_codes    (post_codes),
          .bench_valid    (post_valid)
      );

      for (i = 0; i < 5; i++) begin : gen_post_flat
        assign preenc_flat[i]       = post_codes[i];
        assign preenc_flat_valid[i] = post_valid[i];
      end
      for (i = 5; i < 20; i++) begin : gen_post_pad
        assign preenc_flat[i]       = '0;
        assign preenc_flat_valid[i] = 1'b0;
      end
    end
  endgenerate

endmodule
