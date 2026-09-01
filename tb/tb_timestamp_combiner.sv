// Protocol/arithmetic testbench for timestamp_combiner.
// Optional simulator only; CI uses the Python twin in tests/test_coarse_fine.py.

`timescale 1ns/1ps

module tb_timestamp_combiner;
  localparam int COARSE_W = 8;
  localparam int FINE_W   = 8;
  localparam int OUT_W    = 32;
  localparam int T_REF_PS = 100;

  logic clk, rst_n, valid_i, valid_o;
  logic signed [COARSE_W-1:0] coarse;
  logic [FINE_W-1:0] fine_ps;
  logic signed [OUT_W-1:0] delta_ps;

  timestamp_combiner #(
      .COARSE_W(COARSE_W), .FINE_W(FINE_W), .OUT_W(OUT_W), .T_REF_PS(T_REF_PS)
  ) dut (
      .clk(clk), .rst_n(rst_n), .valid_i(valid_i),
      .coarse(coarse), .fine_ps(fine_ps), .valid_o(valid_o), .delta_ps(delta_ps)
  );

  initial clk = 1'b0;
  always #5 clk = ~clk;

  task automatic check(input longint expected, input string tag);
    begin
      valid_i = 1'b1;
      @(posedge clk);
      valid_i = 1'b0;
      @(posedge clk);
      if (!valid_o || delta_ps !== expected) begin
        $display("FAIL %s got %0d expected %0d valid=%0b", tag, delta_ps, expected, valid_o);
        $finish(1);
      end
    end
  endtask

  initial begin
    rst_n = 1'b0;
    valid_i = 1'b0;
    coarse = '0;
    fine_ps = '0;
    repeat (3) @(posedge clk);
    rst_n = 1'b1;
    @(posedge clk);

    coarse = 0; fine_ps = 0;
    check(0, "zero");

    coarse = 1; fine_ps = 7;
    check(107, "+one period +7");

    coarse = -1; fine_ps = 0;
    check(-100, "minus one period");

    coarse = -1; fine_ps = 1;
    check(-99, "minus one period +1ps-unit");

    $display("tb_timestamp_combiner PASS");
    $finish;
  end
endmodule
