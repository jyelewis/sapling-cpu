
// TODO: should this be called a register_file?
module register_bank (
    input logic clk,
    input logic reset,

    input logic [3:0] ctrl_read_register_a,
    input logic [3:0] ctrl_read_register_b,
    input logic [3:0] ctrl_read_register_c,

    output logic [7:0] register_read_data_a,
    output logic [7:0] register_read_data_b,
    output logic [7:0] register_read_data_c,

    input logic [3:0] ctrl_write_register,
    input logic [7:0] register_write_data,
    input logic ctrl_register_write_enable
);
  // 8x 8-bit registers
  logic [7:0] registers[8];

  always_ff @(posedge clk) begin
    if (reset) begin
      registers[0] <= 8'h00;
      registers[1] <= 8'h00;
      registers[2] <= 8'h00;
      registers[3] <= 8'h00;
      registers[4] <= 8'h00;
      registers[5] <= 8'h00;
      registers[6] <= 8'h00;
      registers[7] <= 8'h00;
    end else if (ctrl_register_write_enable) begin
      registers[ctrl_write_register] <= register_write_data;
    end
  end

  always_comb begin
    register_read_data_a = registers[ctrl_read_register_a];
    register_read_data_b = registers[ctrl_read_register_b];
    register_read_data_c = registers[ctrl_read_register_c];
  end

  // useful for debugging waveforms
  logic [7:0] R0, R1, R2, R3, R4, R5, R6, R7;
  assign R0 = registers[0];
  assign R1 = registers[1];
  assign R2 = registers[2];
  assign R3 = registers[3];
  assign R4 = registers[4];
  assign R5 = registers[5];
  assign R6 = registers[6];
  assign R7 = registers[7];
endmodule
