
module alu
  import types::*;
(
    input alu_op_t alu_op,
    input logic [7:0] alu_lhs,
    input logic [7:0] alu_rhs,
    input logic alu_carry_in,

    output logic [7:0] alu_result,
    output flags_t alu_result_flags
);
  // larger internal logic to hold the carry bit
  logic [8:0] wide_result;

  always_comb begin
    alu_result_flags.carry = 0;
    alu_result_flags.overflow = 0;

    case (alu_op)
      ALU_OP_ADD: begin
        wide_result = alu_lhs + alu_rhs + alu_carry_in;
        alu_result = wide_result[7:0];
        alu_result_flags.carry = wide_result[8];

        //       Mixed signs dont't trigger overflow flag    - our sign bit must have flipped for overflow to occur
        alu_result_flags.overflow = (alu_lhs[7] == alu_rhs[7]) && (alu_result[7] != alu_lhs[7]);
      end

      ALU_OP_SUB: begin
        wide_result = alu_lhs - alu_rhs - alu_carry_in;
        alu_result = wide_result[7:0];
        alu_result_flags.carry = wide_result[8];

        //       Mixed signs dont't trigger overflow flag    - our sign bit must have flipped for overflow to occur
        alu_result_flags.overflow = (alu_lhs[7] != alu_rhs[7]) && (alu_result[7] != alu_lhs[7]);
      end

      ALU_OP_AND: begin
        alu_result = alu_lhs & alu_rhs;
      end

      ALU_OP_OR: begin
        alu_result = alu_lhs | alu_rhs;
      end

      ALU_OP_XOR: begin
        alu_result = alu_lhs ^ alu_rhs;
      end

      ALU_OP_SHL: begin
        alu_result = alu_lhs << 1;
        alu_result_flags.carry = alu_lhs[7];
      end

      ALU_OP_SHR: begin
        alu_result = alu_lhs >> 1;
        alu_result_flags.carry = alu_lhs[0];
      end

      default: begin
        $display("Unknown ALU OP");
      end
    endcase

    alu_result_flags.zero = (alu_result == 0);
    alu_result_flags.negative = (alu_result[7] == 1);
  end
endmodule
