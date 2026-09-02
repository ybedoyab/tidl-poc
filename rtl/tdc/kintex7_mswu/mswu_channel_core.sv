// One MSWU-inspired channel: TDL + quad capture + optional pre-encoder banks.
//
// Front-end (TDL + capture) is never shared between simultaneous channels.
// Pre-encoder logic is per-channel unless the top sets SHARED_POST.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module mswu_channel_core #(
    parameter bit INCLUDE_PREENCODER = 1'b0
) (
    input  logic              clk,
    input  logic              rst_n,
    input  logic              hit,
    input  logic              wu_arm,
    output logic [3:0]        bank_alive,
    output logic [10:0]       preenc_code [4],
    output logic [3:0]        preenc_valid,
    output logic              bench_status
);

  logic [199:0] tdl_taps;
  logic [199:0] captured [4];
  logic         launch_sample;

  mswu_launcher_boundary u_launch (
      .clk          (clk),
      .rst_n        (rst_n),
      .wu_arm       (wu_arm),
      .hit          (hit),
      .launch_sample(launch_sample)
  );

  mswu_tdl_200 u_tdl (
      .hit (hit),
      .taps(tdl_taps)
  );

  mswu_capture_quad u_cap (
      .clk        (clk),
      .rst_n      (rst_n),
      .tdl_taps   (tdl_taps),
      .captured   (captured),
      .bank_alive (bank_alive)
  );

  genvar p;
  generate
    if (INCLUDE_PREENCODER) begin : gen_preenc
      for (p = 0; p < 4; p++) begin : gen_bank_enc
        mswu_mbd5_preencoder_surrogate u_pre (
            .clk      (clk),
            .rst_n    (rst_n),
            .captured (captured[p]),
            .sub_sel  (3'd0),
            .encoded  (preenc_code[p]),
            .valid    (preenc_valid[p])
        );
      end
    end else begin : no_preenc
      assign preenc_code  = '{default: '0};
      assign preenc_valid = '0;
    end
  endgenerate

  always_ff @(posedge clk) begin
    if (!rst_n) bench_status <= 1'b0;
    else bench_status <= bank_alive[0];
  end

endmodule
