from test_utilities import comb_tick, setup_cocotb_tests


async def test_instruction_decoder(dut):
    # Instruction: 0000  opcode: 00 NOP                   seg_a: 0  seg_b: 0  seg_c: 0  imm8: 0
    dut.instruction.value = 0x0000
    await comb_tick()
    assert dut.instruction_opcode.value == 0x00
    assert dut.instruction_segment_a.value == 0
    assert dut.instruction_segment_b.value == 0
    assert dut.instruction_segment_c.value == 0
    assert dut.instruction_imm8.value == 0

    # Instruction: 0ba5  opcode: 01 LOAD_REG_IMM8         seg_a: 3  seg_b: 5  seg_c: 1  imm8: 165
    dut.instruction.value = 0x0BA5
    await comb_tick()
    assert dut.instruction_opcode.value == 0x01
    assert dut.instruction_segment_a.value == 3
    assert dut.instruction_imm8.value == 0xA5

    # Instruction: 5c20  opcode: 0b ADD                   seg_a: 4  seg_b: 1  seg_c: 0  imm8: 32
    dut.instruction.value = 0x5C20
    await comb_tick()
    assert dut.instruction_opcode.value == 0x0B
    assert dut.instruction_segment_a.value == 4
    assert dut.instruction_segment_b.value == 1

    # Instruction: 194c  opcode: 03 LOAD_REG_MEM_ABSOLUTE  seg_a: 1  seg_b: 2  seg_c: 3  imm8: 76
    dut.instruction.value = 0x194C
    await comb_tick()
    assert dut.instruction_opcode.value == 0x03
    assert dut.instruction_segment_a.value == 1
    assert dut.instruction_segment_b.value == 2
    assert dut.instruction_segment_c.value == 3

    # Instruction: 9815  opcode: 13 JMP_REL               seg_a: 0  seg_b: 0  seg_c: 5  imm8: 21
    dut.instruction.value = 0x9815
    await comb_tick()
    assert dut.instruction_opcode.value == 0x13
    assert dut.instruction_imm8.value == 21

    # Instruction: a5e0  opcode: 14 JMP_REG               seg_a: 5  seg_b: 7  seg_c: 0  imm8: 224
    dut.instruction.value = 0xA5E0
    await comb_tick()
    assert dut.instruction_opcode.value == 0x14
    assert dut.instruction_segment_a.value == 5
    assert dut.instruction_segment_b.value == 7
    assert dut.instruction_segment_c.value == 0


setup_cocotb_tests(globals(), auto_clk=False, auto_reset=False)
