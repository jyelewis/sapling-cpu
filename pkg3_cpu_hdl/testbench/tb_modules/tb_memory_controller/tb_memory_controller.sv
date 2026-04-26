module tb_memory_controller(
    input logic [15:0] memory_address,
    output logic [7:0] memory_read_data,
    output logic [7:0] memory_read_data_peak,
    input logic [7:0] memory_write_data,
    input logic memory_write_enable,
    output logic memory_ready
);
    // Packed: one 524288-bit vector instead of 65536 separate elements.
    // Indexed as memory[addr*8 +: 8] to extract a byte.
    // this is to avoid a performance issues with icarus & unpacked arrays - see the initial block below.
    logic [2**16*8-1:0] memory;

    // Explicit 16-bit wrap so the peak doesn't index past the end at 0xFFFF
    logic [15:0] peak_address;
    assign peak_address = memory_address + 16'd1;

    // $readmemh wants an unpacked array, so we read the file manually.
    // claude wrote this, was sick of waiting for build times - this fixes the unpacked array performance issue.
    initial begin
        int fd, status, byte_idx;
        logic [7:0] byte_val;
        fd = $fopen(`TB_MEMORY_CONTROLLER_INIT_DATA, "r");
        if (fd == 0) begin
            $error("Failed to open memory init file");
            $finish;
        end
        memory = '0;
        byte_idx = 0;
        while (!$feof(fd)) begin
            status = $fscanf(fd, "%h", byte_val);
            if (status == 1) begin
                memory[byte_idx*8 +: 8] = byte_val;
                byte_idx++;
            end
        end
        $fclose(fd);
    end

    always_comb begin
        if (memory_write_enable) begin
            memory[memory_address*8 +: 8] = memory_write_data;
            memory_read_data      = '0;
            memory_read_data_peak = '0;
            memory_ready          = 1'b1;
        end else begin
            memory_read_data      = memory[memory_address*8 +: 8];
            memory_read_data_peak = memory[peak_address*8   +: 8];
            memory_ready          = 1'b1;
        end
    end
endmodule