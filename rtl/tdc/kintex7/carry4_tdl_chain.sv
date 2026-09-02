// Original 7-series CARRY4 tapped delay line (structural).
//
// Not copied from Kwiatkowski, Mao, CERN, or other TDC repositories.
// Taps are the four CO outputs of each CARRY4. This is not a behavioural
// delay model, not a 1 ps interpolator, and not a physical bin-width claim.
// Post-route cell delays must not be treated as TDC bins.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module carry4_tdl_chain #(
    parameter int N_CARRY4 = 32
) (
    input  logic                  hit,
    output logic [4*N_CARRY4-1:0] taps
);

  (* DONT_TOUCH = "TRUE" *) logic [3:0] co [N_CARRY4];
  (* KEEP = "TRUE" *)       logic [3:0] o  [N_CARRY4];

  genvar i;
  generate
    for (i = 0; i < N_CARRY4; i++) begin : gen_carry
      if (i == 0) begin : gen_head
        (* DONT_TOUCH = "TRUE" *)
        CARRY4 u_carry (
            .CO(co[i]),
            .O(o[i]),
            .CI(1'b0),
            .CYINIT(hit),
            .DI(4'b0000),
            .S(4'b1111)
        );
      end else begin : gen_body
        (* DONT_TOUCH = "TRUE" *)
        CARRY4 u_carry (
            .CO(co[i]),
            .O(o[i]),
            .CI(co[i-1][3]),
            .CYINIT(1'b0),
            .DI(4'b0000),
            .S(4'b1111)
        );
      end
      assign taps[4*i +: 4] = co[i];
    end
  endgenerate

endmodule
