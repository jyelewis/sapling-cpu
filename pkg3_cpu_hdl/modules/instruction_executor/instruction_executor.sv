
// TODO: test me?
module instruction_executor
  import types::*;
(
    input logic clk,
    input logic reset,

    input opcode_t instruction_opcode,
    input logic [3:0] instruction_segment_a,
    input logic [3:0] instruction_segment_b,
    input logic [3:0] instruction_segment_c,
    input logic [7:0] instruction_imm8,

    input logic [15:0] current_pc,

    // control lines
    // TODO: not sold on this pattern yet
    output logic [15:0] ctrl_next_pc,
    output logic ctrl_load_instruction
);
  // TODO: handle memory not being ready after performing a load

  // TODO: respect reset

  always_ff @(posedge clk) begin
    case (instruction_opcode)
      NOP: begin
        $display("Decoded instruction: NOP");
        ctrl_next_pc <= current_pc + 16'h0002;  // move to the next instruction
        ctrl_load_instruction <= 1;  // TODO: this memory may not be ready yet?
      end

      default: begin
        $display("Unknown opcode: %b", instruction_opcode);
        ctrl_load_instruction <= 0;
      end
    endcase
  end
endmodule
