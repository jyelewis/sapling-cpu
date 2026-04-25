
module tb_memory_controller(
    // TODO: this 16 bit / 8 bit thing is a bit of a mess, should we have a seperate port for "memory_peak_read_data" to give us the extra 8 bits?
    //       alternately we could just cop the double clock to read in both halves of the memory - ala 6502
    input logic [15:0] memory_address,
    output logic [15:0] memory_read_data,
    input logic [15:0] memory_write_data,
    input logic memory_write_enable,
    output logic memory_ready
);
    // inline memmory
    // TODO: is this memory size correct...??
    // TODO: needs 8 bit seeking... 
    logic [15:0] memory [0:16];
    
    initial begin
        $readmemh(`TB_MEMORY_CONTROLLER_INIT_DATA, memory);
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
    