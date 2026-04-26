
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

    input logic memory_ready,
    input logic [15:0] current_pc,

    // control lines
    // TODO: not sold on this pattern yet
    output logic [15:0] ctrl_next_pc,
    output logic ctrl_load_instruction
);
  always_ff @(posedge clk) begin
    if (reset) begin
      ctrl_next_pc <= 16'h0000;
      ctrl_load_instruction <= 0;
    end else if (!memory_ready) begin
      // wait for memory to be ready before doing anything
      ctrl_load_instruction <= 0;
    end else begin
      case (instruction_opcode)
        NOP: begin
          $display("Decoded instruction: NOP");
          // our PC increments via 2 registers, causing all instructions to take 2 clock cycles. Not ideal
          //ctrl_next_pc <= current_pc + 16'h0002;  // move to the next instruction
          
          // TODO: think more about this, we're always trying to stay ahead
          ctrl_next_pc <= ctrl_next_pc + 16'h0002;  // move to the next instruction
          ctrl_load_instruction <= 1;
        end

        default: begin
          $display("Unknown opcode: %b", instruction_opcode);
          ctrl_load_instruction <= 0;
        end
      endcase
    end
  end
endmodule
