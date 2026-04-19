// TODO: apparently an FPGA antipattern to produce your own clock
module clock_divider #(
    parameter int DIVISOR = 2
) (
    input  logic reset,
    input  logic clk_in,
    output logic clk_out
);
  // we only count on the pos edge
  localparam int HalfDivisor = DIVISOR / 2;

  logic [$clog2(HalfDivisor)-1:0] counter;

  always_ff @(posedge clk_in or posedge reset) begin
    if (reset) begin
      counter <= '0;
      clk_out <= 0;  // Reset output clock
    end else begin
      if (counter == HalfDivisor - 1) begin
        counter <= '0;
        clk_out <= ~clk_out;  // Toggle output clock
      end else begin
        counter <= counter + 1;
      end
    end
  end
endmodule
