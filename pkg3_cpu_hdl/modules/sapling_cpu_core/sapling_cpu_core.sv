
module sapling_cpu_core (
    input logic clk,
    input logic reset,

    // memory controller
    output logic [15:0] memory_address,
    input logic [15:0] memory_read_data,
    output logic [15:0] memory_write_data,
    output logic memory_write_enable,
    input logic memory_ready
);
  // while we test, always read memory at address 0xABCD and ignore writes
  assign memory_address = 16'hABCD;
  assign memory_write_data = 16'h0000;
  assign memory_write_enable = 1'b0;

endmodule
