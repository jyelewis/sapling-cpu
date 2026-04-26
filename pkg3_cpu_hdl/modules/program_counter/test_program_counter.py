from test_utilities.cocotb_utils import setup_cocotb_tests, tick


async def test_program_counter(dut):
    dut.next_pc.value = 0x1234
    assert dut.current_pc.value == 0x0000
    await tick(dut)
    assert dut.next_pc.value == 0x1234


setup_cocotb_tests(globals(), auto_clk=True, auto_reset=True)
