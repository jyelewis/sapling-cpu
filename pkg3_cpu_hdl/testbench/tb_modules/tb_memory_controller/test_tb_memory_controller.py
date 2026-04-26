from pathlib import Path

import cocotb
from cocotb.triggers import Timer


@cocotb.test()
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

@cocotb.test()
async def test_write(dut):
    dut.memory_address.value = 0x0015
    dut.memory_write_data.value = 0x42
    dut.memory_write_enable.value = 1
    await Timer(1, unit="ns")

    dut.memory_write_enable.value = 0
    await Timer(1, unit="ns")

    assert dut.memory_read_data.value == 0x42



# TODO: write some nicer cocotb test utils
def test_testbench():
    from cocotb_tools.runner import get_runner

    repo_root = Path(__file__).resolve().parents[4]
    build_dir = repo_root / "build" / "cocotb" / "tb_memory_controller"

    runner = get_runner("icarus")
    runner.build(
        sources=[Path(__file__).parent / "tb_memory_controller.sv"],
        hdl_toplevel="tb_memory_controller",
        build_dir=str(build_dir),
        build_args=["-g2012", "-DCOCOTB_SIM=1"],
        defines={"TB_MEMORY_CONTROLLER_INIT_DATA": str(Path(__file__).parent / "test_data.hex")},
        timescale=("1ns", "1ps"),
        waves=False,
    )
    runner.test(
        hdl_toplevel="tb_memory_controller",
        test_module="pkg3_cpu_hdl.testbench.tb_modules.tb_memory_controller.test_tb_memory_controller",
        build_dir=str(build_dir),
        waves=False,
    )
