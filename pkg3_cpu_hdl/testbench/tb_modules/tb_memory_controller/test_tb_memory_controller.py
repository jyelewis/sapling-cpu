from pathlib import Path

from test_utilities import setup_cocotb_tests, tick


async def test_8bit_reads_with_peak(dut):
    dut.memory_address.value = 0x0000
    await tick(dut)
    assert dut.memory_read_data.value == 0x00
    assert dut.memory_read_data_peak.value == 0x01

    dut.memory_address.value = 0x0001
    await tick(dut)
    assert dut.memory_read_data.value == 0x01
    assert dut.memory_read_data_peak.value == 0x02

    dut.memory_address.value = 0x0007
    await tick(dut)
    assert dut.memory_read_data.value == 0xAC
    assert dut.memory_read_data_peak.value == 0xEE


async def test_write(dut):
    dut.memory_address.value = 0x0015
    dut.memory_write_data.value = 0x42
    # TODO: how do we do memory writes without a clock...
    dut.memory_write_enable.value = 1
    await tick(dut)

    dut.memory_write_enable.value = 0
    await tick(dut)

    assert dut.memory_read_data.value == 0x42


setup_cocotb_tests(
    globals(),
    auto_clk=True,
    auto_reset=True,
    default_verilog_defines={"TB_MEMORY_CONTROLLER_INIT_DATA": str(Path(__file__).parent / "test_data.hex")},
)
