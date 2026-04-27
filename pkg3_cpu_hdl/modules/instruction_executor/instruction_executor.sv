
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

    // TODO: interfaces man!
    // control lines
    // TODO: not sold on this pattern yet
    output logic [15:0] ctrl_next_pc,
    output logic ctrl_load_instruction,
    output logic [3:0] ctrl_read_register_a,
    output logic [3:0] ctrl_read_register_b,
    output logic [3:0] ctrl_write_register,
    output logic [8:0] register_write_data,  // TODO: should we be muxing here?
    output logic ctrl_register_write_enable
);
  always_ff @(posedge clk) begin
    if (reset) begin
      ctrl_next_pc <= 16'h0000;
      ctrl_load_instruction <= 0;
    end else if (!memory_ready) begin
      // wait for memory to be ready before doing anything
      ctrl_load_instruction <= 0;
    end else begin

      // TODO: sensible defaults on everything
      ctrl_register_write_enable <= 0;

      case (instruction_opcode)
        NOP: begin
          $display("Decoded instruction: NOP");
          // our PC increments via 2 registers, causing all instructions to take 2 clock cycles. Not ideal
          //ctrl_next_pc <= current_pc + 16'h0002;  // move to the next instruction

          // TODO: think more about this, we're always trying to stay ahead
          ctrl_next_pc <= ctrl_next_pc + 16'h0002;  // move to the next instruction
          ctrl_load_instruction <= 1;
        end

        LOAD_REG_IMM8: begin
          $display("Decoded instruction: LOAD_REG_IMM8");
          ctrl_write_register <= instruction_segment_a;
          register_write_data <= instruction_imm8;
          ctrl_register_write_enable <= 1;

          ctrl_next_pc <= ctrl_next_pc + 16'h0002;  // move to the next instruction
          ctrl_load_instruction <= 1;
        end
        
        LOAD_REG_REG: begin
            $display("Decoded instruction: LOAD_REG_REG");
            ctrl_read_register_a <= instruction_segment_b;
            ctrl_write_register <= instruction_segment_a;
            register_write_data <= register_read_data_a;
            ctrl_register_write_enable <= 1;
            
            ctrl_next_pc <= ctrl_next_pc + 16'h0002;  // move to the next instruction
            ctrl_load_instruction <= 1;
        end


        default: begin
          // TODO: fault + halt signal?
          $display("Unknown opcode: %h", instruction_opcode);
          ctrl_load_instruction <= 0;
        end
      endcase
    end
  end
endmodule
