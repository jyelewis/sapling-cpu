
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
    output logic [3:0] ctrl_read_register_c,
    output logic [3:0] ctrl_write_register,
    output reg_write_data_src_t ctrl_register_write_data_src,
    output logic ctrl_register_write_enable,
    output memory_address_src_t ctrl_memory_address_src,
    output memory_write_src_t ctrl_memory_write_src,
    output logic ctrl_memory_write,

    output alu_op_t ctrl_alu_op,
    output logic ctrl_load_flags
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

  task automatic do_alu_op(input alu_op_t alu_op, input logic write_back);
    ctrl_read_register_a         = instruction_segment_a;
    ctrl_read_register_b         = instruction_segment_b;
    ctrl_alu_op                  = alu_op;
    ctrl_write_register          = instruction_segment_a;
    ctrl_register_write_data_src = REG_WRITE_DATA_ALU;
    ctrl_register_write_enable   = write_back;
    ctrl_load_flags              = 1;
  endtask

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
    ctrl_memory_address_src = MEMORY_ADDRESS_NEXT_PC;
    ctrl_memory_write_src = MEMORY_WRITE_REG_C;
    ctrl_memory_write = 0;
    ctrl_load_flags = 0;
    ctrl_alu_op = ALU_OP_ADD;

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
        OPCODE_NOP: begin
        end

        OPCODE_LOAD_REG_IMM8: begin
          ctrl_write_register = instruction_segment_a;
          ctrl_register_write_data_src = REG_WRITE_DATA_IMM8;
          ctrl_register_write_enable = 1;
        end

        OPCODE_LOAD_REG_REG: begin
          ctrl_read_register_a = instruction_segment_b;
          ctrl_write_register = instruction_segment_a;
          ctrl_register_write_data_src = REG_WRITE_DATA_REG_READ_A;
          ctrl_register_write_enable = 1;
        end

        OPCODE_LOAD_REG_MEM_ABSOLUTE: begin
          unique case (microcode_step)
            0: begin
              // step 1a: load values from specified registers
              ctrl_read_register_a = instruction_segment_b;
              ctrl_read_register_b = instruction_segment_c;

              // step 1b: request memory load from [reg1, reg2]
              ctrl_memory_address_src = MEMORY_ADDRESS_REG_COMB;

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

        OPCODE_STORE_MEM_ABSOLUTE_REG: begin
          unique case (microcode_step)
            0: begin
              // step 1a: load address + data from specified registers
              ctrl_read_register_a = instruction_segment_a;  // dest addr hi
              ctrl_read_register_b = instruction_segment_b;  // dest addr low
              ctrl_read_register_c = instruction_segment_c;  // src

              // step 1b: request memory write of REG_C into [reg1, reg2]
              ctrl_memory_address_src = MEMORY_ADDRESS_REG_COMB;
              ctrl_memory_write_src = MEMORY_WRITE_REG_C;
              ctrl_memory_write = 1;

              ctrl_next_continue_microcode = 1;
              ctrl_next_pc_src = NEXT_PC_HOLD;
              ctrl_load_instruction = 0;  // memory address bus in use
            end
            1: begin
              // inserted NOP while the memory bus is being used for our write
            end
          endcase
        end

        // TODO: test me
        // TODO: does not seem to be working....
        OPCODE_LOAD_REG_MEM_SP_REL: begin
          $display("Executing LOAD_REG_MEM_SP_REL with imm8 offset");
          unique case (microcode_step)
            0: begin
              // step 1: request memory load from sp + imm8
              ctrl_memory_address_src = MEMORY_ADDRESS_SP_OFFSET;

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

        // TODO: test me
        OPCODE_STORE_MEM_SP_REL_REG: begin
          $display("Executing STORE_MEM_SP_REL_REG with imm8 offset");
          unique case (microcode_step)
            0: begin
              // step 1a: load data from specified register
              ctrl_read_register_c = instruction_segment_a;  // data src

              // step 1b: request memory write of REG_C into sp + imm8
              ctrl_memory_address_src = MEMORY_ADDRESS_SP_OFFSET;
              ctrl_memory_write_src = MEMORY_WRITE_REG_C;
              ctrl_memory_write = 1;

              ctrl_next_continue_microcode = 1;
              ctrl_next_pc_src = NEXT_PC_HOLD;
              ctrl_load_instruction = 0;  // memory address bus in use
            end
            1: begin
              // inserted NOP while the memory bus is being used for our write
              // TODO: I am not convinced this is the right answer
              // ctrl_next_pc_src = NEXT_PC_HOLD;
            end
          endcase
        end

        OPCODE_ADD: do_alu_op(ALU_OP_ADD, 1);
        OPCODE_SUB: do_alu_op(ALU_OP_SUB, 1);
        OPCODE_CMP: do_alu_op(ALU_OP_SUB, 0);
        OPCODE_AND: do_alu_op(ALU_OP_AND, 1);
        OPCODE_OR:  do_alu_op(ALU_OP_OR, 1);
        OPCODE_XOR: do_alu_op(ALU_OP_XOR, 1);
        OPCODE_SHL: do_alu_op(ALU_OP_SHL, 1);
        OPCODE_SHR: do_alu_op(ALU_OP_SHR, 1);


        default: begin
          $display("Unknown opcode: %h", instruction_opcode);
          ctrl_load_instruction = 0;
        end
      endcase
    end
  end
endmodule
