// TODO: apparently an FPGA antipattern to produce your own clock
// TODO: test me
module clock_divider #(
    parameter int DIVISOR = 2
) (
    input  logic clk_in,
    output logic clk_out
);
  // we only count on the pos edge
  localparam int HALF_DIVISOR = DIVISOR / 2;

  logic [$clog2(HALF_DIVISOR)-1:0] counter;

  always_ff @(posedge clk_in) begin
    if (counter == HALF_DIVISOR - 1) begin
      counter <= '0;
      clk_out <= ~clk_out;  // Toggle output clock
    end else begin
      counter <= counter + 1;
    end
  end
endmodule
