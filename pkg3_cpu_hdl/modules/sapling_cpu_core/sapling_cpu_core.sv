
module sapling_cpu_core
  import types::*;
(
    input logic clk,
    input logic reset,

    // memory controller
    output logic [15:0] memory_address,
    input logic [7:0] memory_read_data,
    input logic [7:0] memory_read_data_peak,
    output logic [7:0] memory_write_data,
    output logic memory_write_enable,
    input logic memory_ready
);
  // program counter
  logic [15:0] current_pc;

  logic [15:0] next_pc;
  next_pc_src_t ctrl_next_pc_src;
  always_comb begin
    unique case (ctrl_next_pc_src)
      NEXT_PC_INC:  next_pc = current_pc + 16'h0002;
      NEXT_PC_HOLD: next_pc = current_pc;
    endcase
  end
  program_counter program_counter (.*);

  // instruction fetch
  logic ctrl_load_instruction;
  logic [15:0] instruction;
  instruction_register instruction_register (.*);

  // instruction parse - split into segments
  opcode_t instruction_opcode;
  logic [3:0] instruction_segment_a;
  logic [3:0] instruction_segment_b;
  logic [3:0] instruction_segment_c;
  logic [7:0] instruction_imm8;
  instruction_parser instruction_parser (.*);

  // register bank
  // reads
  logic [3:0] ctrl_read_register_a;
  logic [3:0] ctrl_read_register_b;
  logic [8:0] register_read_data_a;
  logic [8:0] register_read_data_b;

  // writes
  logic [3:0] ctrl_write_register;
  logic ctrl_register_write_enable;
  reg_write_data_src_t ctrl_register_write_data_src;
  logic [8:0] register_write_data;
  always_comb begin
    unique case (ctrl_register_write_data_src)
      REG_WRITE_DATA_IMM8:       register_write_data = instruction_imm8;
      REG_WRITE_DATA_REG_READ_A: register_write_data = register_read_data_a;
      REG_WRITE_DATA_MEMORY:     register_write_data = memory_read_data;
    endcase
  end

  register_bank register_bank (.*);

  // memory
  memory_read_address_src_t ctrl_memory_read_address_src;
  always_comb begin
    unique case (ctrl_memory_read_address_src)
      MEMORY_READ_ADDRESS_NEXT_PC:  memory_address = next_pc;
      MEMORY_READ_ADDRESS_REG_COMB: memory_address = {register_read_data_a, register_read_data_b};
    endcase

    memory_write_data   = 8'h00;
    memory_write_enable = 0;
  end

  // control_unit
  control_unit control_unit (.*);


endmodule
