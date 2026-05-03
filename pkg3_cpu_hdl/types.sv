package types;
  typedef enum logic [4:0] {
    OPCODE_NOP = 5'h00,
    OPCODE_LOAD_REG_IMM8 = 5'h01,
    OPCODE_LOAD_REG_REG = 5'h02,
    OPCODE_LOAD_REG_MEM_ABSOLUTE = 5'h03,
    OPCODE_STORE_MEM_ABSOLUTE_REG = 5'h04,
    OPCODE_LOAD_REG_MEM_SP_REL = 5'h05,
    OPCODE_STORE_MEM_SP_REL_REG = 5'h06,
    OPCODE_LOAD_REG_SPECIAL = 5'h07,
    OPCODE_STORE_SPECIAL_REG = 5'h08,
    OPCODE_IN = 5'h09,
    OPCODE_OUT = 5'h0A,
    OPCODE_ADD = 5'h0B,
    OPCODE_SUB = 5'h0C,
    OPCODE_CMP = 5'h0D,
    OPCODE_AND = 5'h0E,
    OPCODE_OR = 5'h0F,
    OPCODE_XOR = 5'h10,
    OPCODE_SHL = 5'h11,
    OPCODE_SHR = 5'h12,
    OPCODE_JMP_REL = 5'h13,
    OPCODE_JMP_REG = 5'h14,
    OPCODE_CALL = 5'h15,
    OPCODE_RET = 5'h16,
    OPCODE_BEQ = 5'h17,
    OPCODE_BLT = 5'h18,
    OPCODE_BOV = 5'h19,
    OPCODE_BCS = 5'h1A,
    OPCODE_PUSH = 5'h1B,
    OPCODE_POP = 5'h1C,
    OPCODE_WFI = 5'h1D
  } opcode_t;

  // TODO: unify naming of these control enums
  // TODO: inconsistant enum value prefixes?
  typedef enum logic [1:0] {
    NEXT_PC_HOLD = 2'h0,
    NEXT_PC_INC  = 2'h1
  } next_pc_src_t;

  typedef enum logic [1:0] {
    REG_WRITE_DATA_IMM8       = 2'h0,
    REG_WRITE_DATA_REG_READ_A = 2'h1,
    REG_WRITE_DATA_MEMORY     = 2'h2,
    REG_WRITE_DATA_ALU        = 2'h3
  } reg_write_data_src_t;

  typedef enum logic [1:0] {
    MEMORY_ADDRESS_NEXT_PC  = 2'h0,
    MEMORY_ADDRESS_REG_COMB = 2'h1
  } memory_address_src_t;

  typedef enum logic [1:0] {MEMORY_WRITE_REG_C = 2'h0} memory_write_src_t;

  // alu types
  typedef enum logic [2:0] {
    ALU_OP_ADD = 3'h0,
    ALU_OP_SUB = 3'h1,
    ALU_OP_AND = 3'h2,
    ALU_OP_OR  = 3'h3,
    ALU_OP_XOR = 3'h4,
    ALU_OP_SHL = 3'h5,
    ALU_OP_SHR = 3'h6
  } alu_op_t;

  typedef struct packed {
    logic [2:0] unused;  // 5, 6, 7
    logic disable_interrupts;  // 4
    logic overflow;  // 3
    logic carry;  // 2
    logic negative;  // 1
    logic zero;  // 0
  } flags_t;

  typedef enum logic [2:0] {
    CARRY_ZERO = 3'h0,
    CARRY_ONE  = 3'h1,
    CARRY_LAST = 3'h2
  } carry_mode_t;
endpackage
