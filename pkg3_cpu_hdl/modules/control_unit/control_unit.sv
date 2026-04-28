
// TODO: test me?
module control_unit
  import types::*;
(
    input logic clk,
    input logic reset,

    input opcode_t instruction_opcode,
    // TODO: should we be using mux's for these too?
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
    output logic ctrl_register_write_enable,
    output memory_read_address_src_t ctrl_memory_read_address_src
);
  // microcode step tracking
  logic ctrl_next_continue_microcode;
  logic [2:0] microcode_step = 0;
  always_ff @(posedge clk) begin
    if (ctrl_next_continue_microcode) begin
      microcode_step <= microcode_step + 1;
    end else begin
      microcode_step <= 0;
    end
  end

  always_comb begin
    // set all values to 'nop' defaults
    // this allows our opcode case statement to only specify control lines that need changing
    ctrl_next_pc_src = NEXT_PC_INC;
    ctrl_load_instruction = 1;
    ctrl_read_register_a = 0;
    ctrl_read_register_b = 0;
    ctrl_write_register = 0;
    ctrl_register_write_data_src = REG_WRITE_DATA_IMM8;
    ctrl_register_write_enable = 0;
    ctrl_memory_read_address_src = MEMORY_READ_ADDRESS_NEXT_PC;

    ctrl_next_continue_microcode = 0;

    if (reset) begin
      ctrl_next_pc_src = NEXT_PC_HOLD;
      ctrl_load_instruction = 0;
    end else if (!memory_ready) begin
      // wait for memory to be ready before doing anything
      ctrl_next_pc_src = NEXT_PC_HOLD;
      ctrl_load_instruction = 0;
    end else begin
      case (instruction_opcode)
        NOP: begin
        end

        LOAD_REG_IMM8: begin
          ctrl_write_register = instruction_segment_a;
          ctrl_register_write_data_src = REG_WRITE_DATA_IMM8;
          ctrl_register_write_enable = 1;
        end

        LOAD_REG_REG: begin
          ctrl_read_register_a = instruction_segment_b;
          ctrl_write_register = instruction_segment_a;
          ctrl_register_write_data_src = REG_WRITE_DATA_REG_READ_A;
          ctrl_register_write_enable = 1;
        end

        LOAD_REG_MEM_ABSOLUTE: begin
          unique case (microcode_step)
            0: begin
              // step 1a: load values from specified registers
              ctrl_read_register_a = instruction_segment_b;
              ctrl_read_register_b = instruction_segment_c;

              // step 1b: request memory load from [reg1, reg2]
              ctrl_memory_read_address_src = MEMORY_READ_ADDRESS_REG_COMB;

              ctrl_next_continue_microcode = 1;
              ctrl_next_pc_src = NEXT_PC_HOLD;
              ctrl_load_instruction = 0;
            end
            1: begin
              // step 2: store in reg specified in segment_a
              ctrl_write_register = instruction_segment_a;
              ctrl_register_write_data_src = REG_WRITE_DATA_MEMORY;
              ctrl_register_write_enable = 1;
            end
          endcase
        end


        default: begin
          $display("Unknown opcode: %h", instruction_opcode);
          ctrl_load_instruction = 0;
        end
      endcase
    end
  end
endmodule
