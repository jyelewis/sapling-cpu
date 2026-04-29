
// TODO: test me!
module alu
  import types::*;
(
    input alu_op_t alu_op,
    input logic [7:0] alu_lhs,
    input logic [7:0] alu_rhs,
    input logic alu_carry_in,

    output logic [7:0] alu_result,
    output logic alu_carry_out,

    output logic alu_flag_zero,
    output logic alu_flag_negative,
    output logic alu_flag_carry,
    output logic alu_flag_overflow
);
  // larger internal logic to hold the carry bit
  logic [8:0] wide_result;

  always_comb begin
    case (alu_op)
      // TODO: test me
      ALU_OP_ADD: begin
        wide_result = alu_lhs + alu_rhs + alu_carry_in;
        alu_result = wide_result[7:0];
        alu_carry_out = wide_result[8];
      end

      // TODO: rest of the owl

      default: begin
        $display("Unknown ALU OP");
      end
    endcase


    // TODO: wire up flags
    alu_flag_zero = 0;
    alu_flag_negative = 0;
    alu_flag_carry = 0;
    alu_flag_overflow = 0;
  end
endmodule
