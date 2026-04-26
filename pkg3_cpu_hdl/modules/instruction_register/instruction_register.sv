
module instruction_register (
    input logic clk,
    input logic reset,

    input logic ctrl_load_instruction,

    input logic [7:0] memory_read_data,
    input logic [7:0] memory_read_data_peak,

    output logic [15:0] instruction
);
  always_ff @(posedge clk) begin
    if (reset) begin
      instruction <= 16'h0000;
    end else if (ctrl_load_instruction) begin
      // use our memory controllers peak byte to load the entire 16 bit instruciton at once
      instruction <= {memory_read_data, memory_read_data_peak};
    end
  end
endmodule
