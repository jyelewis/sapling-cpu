
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
  logic [15:0] ctrl_next_pc;
  next_pc_src_t ctrl_next_pc_src;
  always_comb begin
    case (ctrl_next_pc_src)
      NEXT_PC_INC:  ctrl_next_pc = current_pc + 16'h0002;
      NEXT_PC_HOLD: ctrl_next_pc = current_pc;
      default:      ctrl_next_pc = current_pc;
    endcase
  end
  program_counter program_counter (.*);

  // register bank
  logic [3:0] ctrl_read_register_a;
  logic [3:0] ctrl_read_register_b;

  logic [3:0] ctrl_write_register;
  logic [7:0] ctrl_imm8;
  reg_write_data_src_t ctrl_register_write_data_src;
  logic [8:0] register_write_data;
  logic ctrl_register_write_enable;

  logic [8:0] register_read_data_a;
  logic [8:0] register_read_data_b;
  always_comb begin
    case (ctrl_register_write_data_src)
      // TODO: don't love this, we're pipelining without any plan
      // this is what we did in the last model though...
      REG_WRITE_DATA_IMM8:       register_write_data = {1'b0, ctrl_imm8};
      //        REG_WRITE_DATA_IMM8:       register_write_data = instruction_imm8;
      REG_WRITE_DATA_REG_READ_A: register_write_data = register_read_data_a;
      // TOdo: error?
      default:                   register_write_data = {1'b0, ctrl_imm8};
    endcase
  end
  register_bank register_bank (.*);

  // instruction fetch
  logic ctrl_load_instruction;
  logic [15:0] instruction;
  instruction_register instruction_register (.*);

  // instruction decode
  opcode_t instruction_opcode;
  logic [3:0] instruction_segment_a;
  logic [3:0] instruction_segment_b;
  logic [3:0] instruction_segment_c;
  logic [7:0] instruction_imm8;
  instruction_decoder instruction_decoder (.*);

  // instruction execute
  instruction_executor instruction_executor (.*);

  // PLACEHOLDER: always load mem from current PC
  always_comb begin
    // TODO: think more about this, we need to pre-emptively load the next instruction while processing
    //    memory_address = current_pc;
    memory_address = ctrl_next_pc;
    memory_write_data = 8'h00;
    memory_write_enable = 0;
  end
endmodule
