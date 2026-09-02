// 200 logical-tap TDL using Kintex-7 CARRY4 (50 × 4 CO taps).
//
// Relation: N_LOGICAL_TAPS = N_CARRY4 * 4. Paper anchor: 200 carry taps.
// Original structural mapping; not copied from Kwiatkowski et al.

`timescale 1ns/1ps

(* KEEP_HIERARCHY = "YES" *)
module mswu_tdl_200 (
    input  logic              hit,
    output logic [199:0]      taps
);

  localparam int N_CARRY4 = 50;

  logic [4*N_CARRY4-1:0] co_taps;

  carry4_tdl_chain #(
      .N_CARRY4(N_CARRY4)
  ) u_chain (
      .hit (hit),
      .taps(co_taps)
  );

  assign taps = co_taps[199:0];

endmodule
