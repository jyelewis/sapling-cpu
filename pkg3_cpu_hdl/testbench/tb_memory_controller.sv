
module tb_memory_controller(
    input logic [15:0] memory_address,
    output logic [15:0] memory_read_data,
    input logic [15:0] memory_write_data,
    input logic memory_write_enable,
    output logic memory_ready
);
    // inline memmory
    logic [15:0] memory [0:16];
    
    initial begin
        $readmemb(`TB_MEMORY_CONTROLLER_INIT_DATA, memory);
    end
    
    // perform our reads & writes
    always_comb begin
        if (memory_write_enable) begin
            memory[memory_address] = memory_write_data;
            memory_read_data = '0; // return 0 on writes
            memory_ready = 1'b1;
        end else begin
            memory_read_data = memory[memory_address];
            memory_ready = 1'b1;        
        end
    end
endmodule
    