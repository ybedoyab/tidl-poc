// Parameterized parallel CARRY4 chains for one channel (structural baseline).
//
// First architecture branch uses N_CHAINS=8. Chain count is a parameter, not
// a frozen metrological result. Encoder and calibration ports are reserved
// interfaces only; they do not implement bubble encoding or code-density.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module multi_chain_tdc_structural #(
    parameter int N_CHAINS = 8,
    parameter int N_CARRY4 = 32
) (
    input  logic                             clk,
    input  logic                             rst_n,
    input  logic                             hit,
    output logic [N_CHAINS*4*N_CARRY4-1:0]   captured,
    output logic [N_CHAINS-1:0]              chain_parity,
    output logic                             encoder_ready,
    output logic                             cal_strobe
);

  localparam int N_TAPS = 4 * N_CARRY4;

  genvar k;
  generate
    for (k = 0; k < N_CHAINS; k++) begin : gen_chain
      logic [N_TAPS-1:0] taps_k;
      logic [N_TAPS-1:0] captured_k;

      carry4_tdl_chain #(
          .N_CARRY4(N_CARRY4)
      ) u_chain (
          .hit (hit),
          .taps(taps_k)
      );

      tdc_capture_bank #(
          .N_TAPS(N_TAPS)
      ) u_capture (
          .clk     (clk),
          .rst_n   (rst_n),
          .taps    (taps_k),
          .captured(captured_k)
      );

      assign captured[k*N_TAPS +: N_TAPS] = captured_k;
      assign chain_parity[k] = ^captured_k;
    end
  endgenerate

  // Future bubble-encoder interface: not implemented at this TRL.
  assign encoder_ready = 1'b0;
  // Future calibration interface: not implemented at this TRL.
  assign cal_strobe = 1'b0;

endmodule
