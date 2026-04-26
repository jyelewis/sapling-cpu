
module register_bank (
    input logic clk,
    input logic reset,

    input logic [3:0] ctrl_read_register_a,
    input logic [3:0] ctrl_read_register_b,

    input logic [3:0] ctrl_write_register,
    input logic [8:0] register_write_data,
    input logic ctrl_register_write_enable,

    output logic [8:0] register_read_data_a,
    output logic [8:0] register_read_data_b
);
  // 8x 8-bit registers
  logic [7:0] registers[8];

  always_ff @(posedge clk) begin
    if (reset) begin
      registers[0] <= 9'h000;
      registers[1] <= 9'h000;
      registers[2] <= 9'h000;
      registers[3] <= 9'h000;
      registers[4] <= 9'h000;
      registers[5] <= 9'h000;
      registers[6] <= 9'h000;
      registers[7] <= 9'h000;
    end else if (ctrl_register_write_enable) begin
      registers[ctrl_write_register] <= register_write_data;
    end
  end

  always_comb begin
    register_read_data_a = registers[ctrl_read_register_a];
    register_read_data_b = registers[ctrl_read_register_b];
  end
endmodule
