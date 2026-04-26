from pathlib import Path

from cocotb.triggers import Timer

from test_utilities.cocotb_utils import setup_cocotb_tests


async def test_8bit_reads_with_peak(dut):
    dut.memory_address.value = 0x0000
    await Timer(1, unit="ns")
    assert dut.memory_read_data.value == 0x00
    assert dut.memory_read_data_peak.value == 0x01

    dut.memory_address.value = 0x0001
    await Timer(1, unit="ns")
    assert dut.memory_read_data.value == 0x01
    assert dut.memory_read_data_peak.value == 0x02

    dut.memory_address.value = 0x0007
    await Timer(1, unit="ns")
    assert dut.memory_read_data.value == 0xAC
    assert dut.memory_read_data_peak.value == 0xEE


async def test_write(dut):
    dut.memory_address.value = 0x0015
    dut.memory_write_data.value = 0x42
    # TODO: how do we do memory writes without a clock...
    dut.memory_write_enable.value = 1
    await Timer(1, unit="ns")

    dut.memory_write_enable.value = 0
    await Timer(1, unit="ns")

    assert dut.memory_read_data.value == 0x42


setup_cocotb_tests(
    globals(),
    auto_clk=False,
    auto_reset=False,
    default_verilog_defines={"TB_MEMORY_CONTROLLER_INIT_DATA": str(Path(__file__).parent / "test_data.hex")},
)
