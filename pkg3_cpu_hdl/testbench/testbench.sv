
module testbench(
    input logic clk,
    input logic reset
);
    // TODO: use interfaces?
    logic [15:0] memory_address;
    logic [15:0] memory_read_data;
    logic [15:0] memory_write_data;
    logic memory_write_enable;
    logic memory_ready;
    
    
      sapling_cpu_core cpu (
        .clk(clk),
        .reset(reset),
//        .memory_address(),
//        .memory_read_data(16'h0000),
//        .memory_write_data(),
//        .memory_write_enable(),
//        .memory_ready(1'b1)

        .* 
      );
      
      tb_memory_controller memory_controller (
//        .memory_address(cpu.memory_address),
//        .memory_read_data(cpu.memory_read_data),
//        .memory_write_data(cpu.memory_write_data),
//        .memory_write_enable(cpu.memory_write_enable),
//        .memory_ready(cpu.memory_ready)
        .* 
      );
endmodule