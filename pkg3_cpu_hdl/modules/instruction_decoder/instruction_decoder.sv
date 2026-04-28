
// TODO: rename to something without ambigious 'decoder' in the name
module instruction_decoder
  import types::*;
(
    input logic [15:0] instruction,

    output opcode_t instruction_opcode,
    output logic [3:0] instruction_segment_a,
    output logic [3:0] instruction_segment_b,
    output logic [3:0] instruction_segment_c,
    output logic [7:0] instruction_imm8
);
  // Decode the instruction into its components
  assign instruction_opcode = opcode_t'(instruction[15:11]);
  assign instruction_segment_a = instruction[10:8];
  assign instruction_segment_b = instruction[7:5];
  assign instruction_segment_c = instruction[4:2];
  assign instruction_imm8 = instruction[7:0];
endmodule
