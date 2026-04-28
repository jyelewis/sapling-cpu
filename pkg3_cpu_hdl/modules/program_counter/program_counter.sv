
module program_counter (
    input logic clk,
    input logic reset,
    output logic [15:0] current_pc,

    // TODO: not sold on this pattern yet
    input logic [15:0] next_pc
);
  always_ff @(posedge clk) begin
    if (reset) begin
      current_pc <= 16'h0000;  // Reset to address 0
    end else begin
      current_pc <= next_pc;  // Update PC to next value
    end
  end
endmodule
