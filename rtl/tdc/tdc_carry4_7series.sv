// 7-series CARRY4 tapped-delay-line placeholder.
//
// TODO: instantiate CARRY4 primitives only after a Kintex-7 part is selected.
// TODO: apply RLOC / Pblock constraints in constraints/kintex7/.
// TODO: physical calibration (code-density) is mandatory; this file has no delays.
//
// A generic `assign #1ps` delay line would be neither synthesizable nor accurate.
// Do not add one.

`timescale 1ns/1ps

module tdc_carry4_7series #(
    parameter int N_CARRY4 = 128
) (
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         hit,
    output logic                         valid,
    output logic [4*N_CARRY4-1:0]        taps
);
  // Intentionally tied off. Synthesis of this module is not TDC evidence.
  assign valid = 1'b0;
  assign taps  = '0;
  /* unused */ wire _u = clk ^ rst_n ^ hit;
endmodule
