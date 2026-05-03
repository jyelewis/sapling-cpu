
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
  logic [3:0] ctrl_read_register_c;
  logic [7:0] register_read_data_a;
  logic [7:0] register_read_data_b;
  logic [7:0] register_read_data_c;

  // writes
  logic [3:0] ctrl_write_register;
  logic ctrl_register_write_enable;
  reg_write_data_src_t ctrl_register_write_data_src;
  logic [7:0] register_write_data;
  logic [7:0] alu_result;  // early declare so we can use for writes
  always_comb begin
    unique case (ctrl_register_write_data_src)
      REG_WRITE_DATA_IMM8:       register_write_data = instruction_imm8;
      REG_WRITE_DATA_REG_READ_A: register_write_data = register_read_data_a;
      REG_WRITE_DATA_MEMORY:     register_write_data = memory_read_data;
      REG_WRITE_DATA_ALU:        register_write_data = alu_result;
    endcase
  end

  register_bank register_bank (.*);

  // ALU
  alu_op_t ctrl_alu_op;
  flags_t  alu_result_flags;
  alu alu (
      .alu_lhs(register_read_data_a),
      .alu_rhs(register_read_data_b),
      .alu_carry_in(1'h0),  // TODO: implement carry
      .*
  );

  // flags
  logic   ctrl_load_flags;
  flags_t current_flags;  // early declare
  flags flags (
      .flags_in (alu_result_flags),  // TODO: special reads/writes. TODO: maintain intd flag?
      .flags_out(current_flags),
      .*
  );

  // memory
  // TODO: should probably go in a memory controller module?
  memory_address_src_t ctrl_memory_address_src;
  memory_write_src_t ctrl_memory_write_src;
  logic ctrl_memory_write;

  always_comb begin
    unique case (ctrl_memory_address_src)
      MEMORY_ADDRESS_NEXT_PC:  memory_address = next_pc;
      MEMORY_ADDRESS_REG_COMB: memory_address = {register_read_data_a, register_read_data_b};
    endcase

    unique case (ctrl_memory_write_src)
      MEMORY_WRITE_REG_C: memory_write_data = register_read_data_c;
    endcase

    memory_write_enable = ctrl_memory_write;
  end

  // control_unit
  control_unit control_unit (.*);
endmodule
