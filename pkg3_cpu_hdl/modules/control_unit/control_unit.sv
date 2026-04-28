
// TODO: test me?
module control_unit
  import types::*;
(
    input logic clk,
    input logic reset,

    input opcode_t instruction_opcode,
    input logic [3:0] instruction_segment_a,
    input logic [3:0] instruction_segment_b,
    input logic [3:0] instruction_segment_c,

    input logic memory_ready,

    // TODO: interfaces man!
    // control lines
    output next_pc_src_t ctrl_next_pc_src,
    output logic ctrl_load_instruction,
    output logic [3:0] ctrl_read_register_a,
    output logic [3:0] ctrl_read_register_b,
    output logic [3:0] ctrl_write_register,
    output reg_write_data_src_t ctrl_register_write_data_src,
    output logic ctrl_register_write_enable
);
  always_comb begin
    if (reset) begin
      ctrl_next_pc_src = NEXT_PC_HOLD;
      ctrl_load_instruction = 0;
    end else if (!memory_ready) begin
      // wait for memory to be ready before doing anything
      ctrl_next_pc_src = NEXT_PC_HOLD;
      ctrl_load_instruction = 0;
    end else begin

      // TODO: sensible defaults on everything
      ctrl_next_pc_src = NEXT_PC_HOLD;
      ctrl_register_write_enable = 0;

      case (instruction_opcode)
        NOP: begin
          $display("Decoded instruction: NOP");
          ctrl_next_pc_src = NEXT_PC_INC;
          ctrl_load_instruction = 1;
        end

        LOAD_REG_IMM8: begin
          $display("Decoded instruction: LOAD_REG_IMM8");
          ctrl_write_register = instruction_segment_a;
          ctrl_register_write_data_src = REG_WRITE_DATA_IMM8;
          ctrl_register_write_enable = 1;

          ctrl_next_pc_src = NEXT_PC_INC;
          ctrl_load_instruction = 1;
        end

        LOAD_REG_REG: begin
          $display("Decoded instruction: LOAD_REG_REG");
          ctrl_read_register_a = instruction_segment_b;
          ctrl_write_register = instruction_segment_a;
          ctrl_register_write_data_src = REG_WRITE_DATA_REG_READ_A;
          ctrl_register_write_enable = 1;

          ctrl_next_pc_src = NEXT_PC_INC;
          ctrl_load_instruction = 1;
        end


        default: begin
          $display("Unknown opcode: %h", instruction_opcode);
          ctrl_load_instruction = 0;
        end
      endcase
    end
  end
endmodule
