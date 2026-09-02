// Per-tap capture register bank for the structural CARRY4 TDL.
//
// Every delay-line tap is registered so synthesis cannot drop the chain as
// unused combinational logic. Capture FFs are synchronous to clk; the carry
// path itself remains asynchronous. This bank is not a bubble encoder.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module tdc_capture_bank #(
    parameter int N_TAPS = 128
) (
    input  logic              clk,
    input  logic              rst_n,
    input  logic [N_TAPS-1:0] taps,
    output logic [N_TAPS-1:0] captured
);

  genvar i;
  generate
    for (i = 0; i < N_TAPS; i++) begin : gen_ff
      FDRE #(
          .INIT(1'b0)
      ) u_ff (
          .Q (captured[i]),
          .C (clk),
          .CE(1'b1),
          .R (~rst_n),
          .D (taps[i])
      );
    end
  endgenerate

endmodule
