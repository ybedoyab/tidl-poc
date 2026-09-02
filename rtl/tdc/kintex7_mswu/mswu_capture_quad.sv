// Four independent 200-tap capture banks (MSWU sampling registers surrogate).
//
// Timing-clean observability: full capture bus retained; one tap per bank
// registered as bank_alive. No wide XOR parity trees.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module mswu_capture_quad #(
    parameter int N_TAPS = 200
) (
    input  logic              clk,
    input  logic              rst_n,
    input  logic [N_TAPS-1:0] tdl_taps,
    (* KEEP = "TRUE", DONT_TOUCH = "TRUE" *)
    output logic [N_TAPS-1:0] captured [4],
    output logic [3:0]        bank_alive
);

  genvar b;
  generate
    for (b = 0; b < 4; b++) begin : gen_bank
      tdc_capture_bank #(
          .N_TAPS(N_TAPS)
      ) u_cap (
          .clk     (clk),
          .rst_n   (rst_n),
          .taps    (tdl_taps),
          .captured(captured[b])
      );
      assign bank_alive[b] = captured[b][0];
    end
  endgenerate

endmodule
