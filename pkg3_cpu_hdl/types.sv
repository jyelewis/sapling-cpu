package types;
  typedef enum logic [4:0] {
    NOP = 5'h00,
    LOAD_REG_IMM8 = 5'h01,
    LOAD_REG_REG = 5'h02,
    LOAD_REG_MEM_ABSOLUTE = 5'h03,
    STORE_MEM_ABSOLUTE_REG = 5'h04,
    LOAD_REG_MEM_SP_REL = 5'h05,
    STORE_MEM_SP_REL_REG = 5'h06,
    LOAD_REG_SPECIAL = 5'h07,
    STORE_SPECIAL_REG = 5'h08,
    IN = 5'h09,
    OUT = 5'h0A,
    ADD = 5'h0B,
    SUB = 5'h0C,
    CMP = 5'h0D,
    AND = 5'h0E,
    OR = 5'h0F,
    XOR = 5'h10,
    SHL = 5'h11,
    SHR = 5'h12,
    JMP_REL = 5'h13,
    JMP_REG = 5'h14,
    CALL = 5'h15,
    RET = 5'h16,
    BEQ = 5'h17,
    BLT = 5'h18,
    BOV = 5'h19,
    BCS = 5'h1A,
    PUSH = 5'h1B,
    POP = 5'h1C,
    WFI = 5'h1D
  } opcode_t;

  // TODO: unify naming of these control enums
  typedef enum logic [1:0] {
    NEXT_PC_HOLD = 2'h0,
    NEXT_PC_INC  = 2'h1
  } next_pc_src_t;

  typedef enum logic [1:0] {
    REG_WRITE_DATA_IMM8       = 2'h0,
    REG_WRITE_DATA_REG_READ_A = 2'h1
  } reg_write_data_src_t;
endpackage
