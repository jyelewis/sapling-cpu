import pytest

from assembler import assemble_instruction, Opcode, to_signed_imm8, asm_to_bin, parse_asm_int

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
    
