from test_utilities import setup_cocotb_tests, tick


async def test_instruction_register(dut):
    assert dut.instruction.value == 0x0000

    dut.memory_read_data.value = 0x12
    dut.memory_read_data_peak.value = 0x34
    await tick(dut)

    # instruction should not update until we pulse ctrl
    assert dut.instruction.value == 0x0000

    dut.ctrl_load_instruction.value = 1
    await tick(dut)
    dut.ctrl_load_instruction.value = 0

    assert dut.instruction.value == 0x1234


setup_cocotb_tests(globals(), auto_clk=True, auto_reset=True)
