// UltraScale / UltraScale+ CARRY8 tapped-delay-line placeholder.
//
// TODO: instantiate CARRY8 primitives for the selected XCKU* / XCKU*P part.
// TODO: apply placement constraints in constraints/kintex_ultrascale[_plus]/.
// TODO: physical calibration is mandatory.
//
// Do not add a behavioural delay line and claim picosecond resolution.

`timescale 1ns/1ps

module tdc_carry8_ultrascale #(
    parameter int N_CARRY8 = 64
) (
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         hit,
    output logic                         valid,
    output logic [8*N_CARRY8-1:0]        taps
);
  assign valid = 1'b0;
  assign taps  = '0;
  /* unused */ wire _u = clk ^ rst_n ^ hit;
endmodule
