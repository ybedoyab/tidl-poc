// Structural top. No analog front-end, no Ethernet MAC, no TDC physics.
// N_CHANNELS default 16 (S7). Fine TDC candidates A/B/C plug in behind tdc_*.

`timescale 1ns/1ps

module tidl_top #(
    parameter int N_CHANNELS     = 16,
    parameter int COARSE_W       = 32,
    parameter int FINE_W         = 16,
    parameter int T_REF_PS       = 10000,
    parameter bit USE_ULTRASCALE = 1'b0
) (
    input  logic                      clk,
    input  logic                      rst_n,
    input  logic                      coarse_enable,
    input  logic [N_CHANNELS-1:0]     hit,
    output logic signed [63:0]        last_delta_ps,
    output logic                      last_valid
);
  logic signed [COARSE_W-1:0] coarse;
  logic                       wrap;

  coarse_counter #(.WIDTH(COARSE_W)) u_coarse (
      .clk(clk),
      .rst_n(rst_n),
      .enable(coarse_enable),
      .load(1'b0),
      .load_value('0),
      .count(coarse),
      .wrapping(wrap)
  );

  logic              tdc_valid;
  logic [FINE_W-1:0] tdc_code;

  tdc_chain_if_stub #(.CODE_W(FINE_W)) u_tdc_stub (
      .clk(clk),
      .rst_n(rst_n),
      .hit(|hit),
      .valid(tdc_valid),
      .code(tdc_code)
  );

  // Family-specific interpolators are not connected. Instantiating them does
  // not create a TDC. They exist so later P&R work has a module boundary.
  generate
    if (USE_ULTRASCALE) begin : g_us
      logic unused_valid;
      logic [8*64-1:0] unused_taps;
      tdc_carry8_ultrascale u_carry8 (
          .clk(clk), .rst_n(rst_n), .hit(1'b0),
          .valid(unused_valid), .taps(unused_taps)
      );
    end else begin : g_7s
      logic unused_valid;
      logic [4*128-1:0] unused_taps;
      tdc_carry4_7series u_carry4 (
          .clk(clk), .rst_n(rst_n), .hit(1'b0),
          .valid(unused_valid), .taps(unused_taps)
      );
    end
  endgenerate

  timestamp_combiner #(
      .COARSE_W(COARSE_W),
      .FINE_W(FINE_W),
      .OUT_W(64),
      .T_REF_PS(T_REF_PS)
  ) u_comb (
      .clk(clk),
      .rst_n(rst_n),
      .valid_i(tdc_valid),
      .coarse(coarse),
      .fine_ps(tdc_code),
      .valid_o(last_valid),
      .delta_ps(last_delta_ps)
  );
endmodule
