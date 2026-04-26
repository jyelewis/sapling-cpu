
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

  program_counter program_counter (.*);

  // TODO: this isn't in the core!
  // memory controller
  //  memory_controller memory_controller (.*);

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
