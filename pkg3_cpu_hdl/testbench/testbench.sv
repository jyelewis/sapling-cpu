
module testbench(
    input logic clk,
    input logic reset
);
    // TODO: use interfaces?
    logic [15:0] memory_address;
    logic [7:0] memory_read_data;
    logic [7:0] memory_read_data_peak;
    logic [7:0] memory_write_data;
    logic memory_write_enable;
    logic memory_ready;
    
    
      sapling_cpu_core cpu (.*);
      
      tb_memory_controller memory_controller (.*);
endmodule