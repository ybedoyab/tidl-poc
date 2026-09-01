// Arithmetic testbench for coarse_counter. Not a timing simulation of a TDC.
// Optional: iverilog -g2012 tb/tb_coarse_counter.sv rtl/timestamp/coarse_counter.sv
// CI does not require a Verilog simulator.

`timescale 1ns/1ps

module tb_coarse_counter;
  localparam int WIDTH = 4;
  logic clk, rst_n, enable, load, wrapping;
  logic signed [WIDTH-1:0] load_value, count;

  coarse_counter #(.WIDTH(WIDTH)) dut (
      .clk(clk), .rst_n(rst_n), .enable(enable), .load(load),
      .load_value(load_value), .count(count), .wrapping(wrapping)
  );

  initial clk = 1'b0;
  always #5 clk = ~clk;

  int errors;
  initial begin
    errors = 0;
    rst_n = 1'b0;
    enable = 1'b0;
    load = 1'b0;
    load_value = '0;
    repeat (3) @(posedge clk);
    rst_n = 1'b1;
    @(posedge clk);
    enable = 1'b1;
    repeat (5) @(posedge clk);
    enable = 1'b0;
    @(posedge clk);
    if (count !== 4'sd5) begin
      $display("FAIL count=%0d expected 5", count);
      errors += 1;
    end
    load = 1'b1;
    load_value = -4'sd3;
    @(posedge clk);
    load = 1'b0;
    @(posedge clk);
    if (count !== -4'sd3) begin
      $display("FAIL loaded count=%0d", count);
      errors += 1;
    end
    enable = 1'b1;
    load_value = {1'b0, {(WIDTH-1){1'b1}}};
    load = 1'b1;
    @(posedge clk);
    load = 1'b0;
    @(posedge clk);
    @(posedge clk);
    if (!wrapping) begin
      $display("FAIL expected wrapping at max positive");
      errors += 1;
    end
    if (errors == 0) $display("tb_coarse_counter PASS");
    else $display("tb_coarse_counter FAIL %0d", errors);
    $finish;
  end
endmodule
