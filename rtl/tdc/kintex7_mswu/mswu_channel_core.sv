// One MSWU-inspired channel: TDL + quad capture + optional pre-encoder banks.
//
// Front-end (TDL + capture) is never shared between simultaneous channels.
// PREENC_MODE: 0=none, 1=sequential low-rate scanner, 2=parallel per-bank×region.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module mswu_channel_core #(
    parameter int PREENC_MODE = 0  // 0=none, 1=seq, 2=parallel
) (
    input  logic              clk,
    input  logic              rst_n,
    input  logic              hit,
    input  logic              wu_arm,
    output logic [3:0]        bank_alive,
    output logic [10:0]       preenc_code,
    output logic              preenc_valid,
    output logic              scan_complete,
    output logic [10:0]       bench_codes [4][5],
    output logic              bench_valid [4][5],
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

  generate
    if (PREENC_MODE == 1) begin : gen_seq
      logic [2:0] bank_sel;
      logic [2:0] sub_sel;

      mswu_preenc_seq_scanner u_scan (
          .clk           (clk),
          .rst_n         (rst_n),
          .captured      (captured),
          .bank_sel      (bank_sel),
          .sub_sel       (sub_sel),
          .encoded       (preenc_code),
          .valid         (preenc_valid),
          .scan_complete (scan_complete),
          .bench_codes   (bench_codes),
          .bench_valid   (bench_valid)
      );
    end else if (PREENC_MODE == 2) begin : gen_parallel
      assign scan_complete = 1'b1;

      mswu_preenc_parallel_banks u_par (
          .clk         (clk),
          .rst_n       (rst_n),
          .captured    (captured),
          .bench_codes (bench_codes),
          .bench_valid (bench_valid)
      );

      always_ff @(posedge clk) begin
        if (!rst_n) begin
          preenc_code  <= '0;
          preenc_valid <= 1'b0;
        end else begin
          preenc_valid <= bench_valid[0][0];
          preenc_code  <= bench_codes[0][0];
        end
      end
    end else begin : no_preenc
      assign preenc_code   = '0;
      assign preenc_valid  = 1'b0;
      assign scan_complete = 1'b0;
      assign bench_codes   = '{default: '0};
      assign bench_valid   = '{default: '0};
    end
  endgenerate

  always_ff @(posedge clk) begin
    if (!rst_n) bench_status <= 1'b0;
    else bench_status <= bank_alive[0] | preenc_valid | scan_complete;
  end

endmodule
