// 7-series CARRY4 placeholder used by tidl_top only.
// The original structural TDL is rtl/tdc/kintex7/. Do not add `#1ps` delays.

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
