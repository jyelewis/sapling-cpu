import pytest

from assembler import (
    AssemblerException,
    Opcode,
    asm_to_bin,
    assemble_instruction,
    parse_asm_int,
    to_signed_imm8,
    tokenize,
)


def _decode(word: int) -> tuple[int, int, int, int, int]:
    opcode = (word >> 11) & 0b11111
    seg_a = (word >> 8) & 0b111
    seg_b = (word >> 5) & 0b111
    seg_c = (word >> 2) & 0b111
    imm8 = word & 0xFF
    return opcode, seg_a, seg_b, seg_c, imm8


def test_assemble_instruction_nop():
    assert assemble_instruction(Opcode.NOP, None, None, None) == 0


def test_assemble_instruction_load_reg_imm8():
    assert assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=2) == 2306
    assert assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=3) == 2307


def test_assemble_instruction_signed():
    assert assemble_instruction(Opcode.NOP, immediate=0) == 0
    assert assemble_instruction(Opcode.NOP, immediate=1) == 1

    with pytest.raises(AssertionError):
        assemble_instruction(Opcode.NOP, immediate=-1)


def test_parse_asm_int():
    assert parse_asm_int("123") == 123
    assert parse_asm_int("0x123") == 0x123
    assert parse_asm_int("0b110011") == 0b110011
    assert parse_asm_int("0x123_456") == 0x123_456


def test_to_signed_imm8():
    assert to_signed_imm8(0) == 0
    assert to_signed_imm8(1) == 1
    assert to_signed_imm8(100) == 100
    assert to_signed_imm8(127) == 127
    assert to_signed_imm8(-1) == 255
    assert to_signed_imm8(-100) == 156
    assert to_signed_imm8(-128) == 128

    with pytest.raises(AssertionError):
        to_signed_imm8(128)

    with pytest.raises(AssertionError):
        to_signed_imm8(-129)


def test_asm_to_bin_nops():
    bin = asm_to_bin(["NOP", "NOP", "NOP"])
    assert bin == [0, 0, 0]


# --- tokenizer -------------------------------------------------------------


def test_tokenize_keeps_bracket_block_together():
    assert tokenize("LD R3 #[R4 R5]") == ["LD", "R3", "#[R4 R5]"]
    assert tokenize("LD R4 #[SP + 0x21]") == ["LD", "R4", "#[SP + 0x21]"]


def test_tokenize_commas_are_whitespace():
    assert tokenize("ADD R1, R2") == ["ADD", "R1", "R2"]


# --- ALU -------------------------------------------------------------------


def test_alu_two_operand_ops():
    words = asm_to_bin([
        "ADD R1 R2",
        "SUB R3 R4",
        "CMP R5 R6",
        "AND R0 R7",
        "OR R1 R2",
        "XOR R3 R4",
    ])
    opcodes = [Opcode.ADD, Opcode.SUB, Opcode.CMP, Opcode.AND, Opcode.OR, Opcode.XOR]
    pairs = [(1, 2), (3, 4), (5, 6), (0, 7), (1, 2), (3, 4)]
    for word, opcode, (a, b) in zip(words, opcodes, pairs):
        decoded = _decode(word)
        assert decoded[0] == opcode.to_int()
        assert decoded[1] == a
        assert decoded[2] == b


def test_alu_unary_ops():
    words = asm_to_bin(["SHL R2", "SHR R3"])
    assert _decode(words[0])[:2] == (Opcode.SHL.to_int(), 2)
    assert _decode(words[1])[:2] == (Opcode.SHR.to_int(), 3)


def test_alu_accepts_commas():
    words = asm_to_bin(["ADD R1, R2"])
    assert _decode(words[0])[:3] == (Opcode.ADD.to_int(), 1, 2)


# --- stack -----------------------------------------------------------------


def test_push_pop():
    words = asm_to_bin(["PUSH R4", "POP R5"])
    assert _decode(words[0])[:2] == (Opcode.PUSH.to_int(), 4)
    assert _decode(words[1])[:2] == (Opcode.POP.to_int(), 5)


# --- jumps / branches ------------------------------------------------------


def test_jmp_reg_pair():
    words = asm_to_bin(["JMP R3 R4"])
    op, a, b, _, _ = _decode(words[0])
    assert op == Opcode.JMP_REG.to_int()
    assert (a, b) == (3, 4)


def test_jmp_relative_forward_label():
    # NOP @ 0, JMP -> target @ 3 (after JMP at index 1).
    # VM adds offset AFTER PC has advanced past the branch, so offset = 3 - 1 - 1 = 1.
    words = asm_to_bin([
        "NOP",
        "JMP #target",
        "NOP",
        "target:",
        "NOP",
    ])
    op, _, _, _, imm = _decode(words[1])
    assert op == Opcode.JMP_REL.to_int()
    assert imm == 1


def test_jmp_relative_backward_label():
    # target @ 0, ..., JMP #target @ 2.  offset = 0 - 2 - 1 = -3 -> 0xFD
    words = asm_to_bin([
        "target:",
        "NOP",
        "NOP",
        "JMP #target",
    ])
    op, _, _, _, imm = _decode(words[2])
    assert op == Opcode.JMP_REL.to_int()
    assert imm == to_signed_imm8(-3)


def test_branch_mnemonics():
    words = asm_to_bin([
        "BEQ #skip",
        "BLT #skip",
        "BOV #skip",
        "BCS #skip",
        "skip:",
        "NOP",
    ])
    expected_opcodes = [Opcode.BEQ, Opcode.BLT, Opcode.BOV, Opcode.BCS]
    expected_offsets = [3, 2, 1, 0]  # from each branch at i to target at 4: 4 - i - 1
    for i, (opcode, offset) in enumerate(zip(expected_opcodes, expected_offsets)):
        op, _, _, _, imm = _decode(words[i])
        assert op == opcode.to_int()
        assert imm == offset


def test_call_and_ret():
    words = asm_to_bin(["CALL R2 R3", "RET"])
    assert _decode(words[0])[:3] == (Opcode.CALL.to_int(), 2, 3)
    assert _decode(words[1])[0] == Opcode.RET.to_int()


def test_unknown_label_raises():
    with pytest.raises(AssemblerException):
        asm_to_bin(["JMP #nowhere"])


def test_duplicate_label_raises():
    with pytest.raises(AssemblerException):
        asm_to_bin(["foo:", "NOP", "foo:", "NOP"])


def test_branch_out_of_range_raises():
    lines = ["start:"] + ["NOP"] * 129 + ["BEQ #start"]
    with pytest.raises(AssemblerException):
        asm_to_bin(lines)


# --- inline label hi/lo bytes ---------------------------------------------


def test_load_label_hi_lo():
    # target is the 4th instruction (index 3) -> byte address 6 -> hi=0, lo=6
    words = asm_to_bin([
        "LD R0 >target",
        "LD R1 <target",
        "NOP",
        "target:",
        "NOP",
    ])
    op0, a0, _, _, imm0 = _decode(words[0])
    op1, a1, _, _, imm1 = _decode(words[1])
    assert op0 == Opcode.LOAD_REG_IMM8.to_int()
    assert op1 == Opcode.LOAD_REG_IMM8.to_int()
    assert (a0, imm0) == (0, 0x00)
    assert (a1, imm1) == (1, 0x06)


def test_load_label_hi_lo_large_address():
    # 300 NOPs, then target.  Target index = 300, byte address = 600 = 0x0258.
    lines = ["LD R0 >target", "LD R1 <target"] + ["NOP"] * 298 + ["target:", "NOP"]
    words = asm_to_bin(lines)
    _, _, _, _, imm0 = _decode(words[0])
    _, _, _, _, imm1 = _decode(words[1])
    assert imm0 == 0x02
    assert imm1 == 0x58


def test_full_call_via_label():
    # Build the target address into R0:R1 then CALL.
    words = asm_to_bin([
        "LD R0 >func",
        "LD R1 <func",
        "CALL R0 R1",
        "WFI",
        "func:",
        "RET",
    ])
    # CALL at index 2 uses R0, R1
    op, a, b, _, _ = _decode(words[2])
    assert op == Opcode.CALL.to_int()
    assert (a, b) == (0, 1)
    # func is at instruction index 4 -> byte address 8
    assert _decode(words[0])[4] == 0x00
    assert _decode(words[1])[4] == 0x08


# --- ST with #[R R] (previous bug) -----------------------------------------


def test_store_absolute_reg_reg_reg():
    words = asm_to_bin(["ST #[R4 R5] R3"])
    op, a, b, c, _ = _decode(words[0])
    assert op == Opcode.STORE_MEM_ABSOLUTE_REG.to_int()
    assert (a, b, c) == (4, 5, 3)

