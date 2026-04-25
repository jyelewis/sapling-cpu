
// TODO: clock divider is an antipattern, apparently
module clock_divider #(
    parameter int DIVISOR = 2
) (
    input  logic clk_in,
    output logic clk_out = 1'b0,
    input  logic reset
);
  // param sanity checks
  initial begin
    if (DIVISOR < 2 || (DIVISOR % 2) != 0)
      $fatal(1, "clock_divider: DIVISOR must be even and >= 2, got %0d", DIVISOR);
  end

  localparam int HalfDiv = DIVISOR / 2;
  localparam int CntW = (HalfDiv <= 1) ? 1 : $clog2(HalfDiv);

  logic [CntW-1:0] counter = '0;

  always_ff @(posedge clk_in) begin
    if (reset) begin
      counter <= '0;
      clk_out <= 1'b0;
    end else if (counter == CntW'(HalfDiv - 1)) begin
      counter <= '0;
      clk_out <= ~clk_out;
    end else begin
      counter <= counter + 1'b1;
    end
  end
endmodule
