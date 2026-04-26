from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge


async def reset_dut(dut):
    dut.reset.value = 1
    await ClockCycles(dut.clk_in, 2)
    dut.reset.value = 0


@cocotb.test()
async def test_output_clock(dut):
    cocotb.start_soon(Clock(dut.clk_in, 2, unit="ns").start())
    await reset_dut(dut)

    # we should be at 0 when starting up
    assert dut.clk_out.value == 0

    await RisingEdge(dut.clk_in)
    await FallingEdge(dut.clk_in)
    assert dut.clk_out.value == 1

    await RisingEdge(dut.clk_in)
    await FallingEdge(dut.clk_in)
    assert dut.clk_out.value == 0

    await RisingEdge(dut.clk_in)
    await FallingEdge(dut.clk_in)
    assert dut.clk_out.value == 1

    await RisingEdge(dut.clk_in)
    await FallingEdge(dut.clk_in)
    assert dut.clk_out.value == 0

    await RisingEdge(dut.clk_in)
    await FallingEdge(dut.clk_in)
    assert dut.clk_out.value == 1

    await RisingEdge(dut.clk_in)
    await FallingEdge(dut.clk_in)
    assert dut.clk_out.value == 0


def test_clock_divider():
    from cocotb_tools.runner import get_runner

    repo_root = Path(__file__).resolve().parents[3]
    build_dir = repo_root / "build" / "cocotb" / "clock_divider"

    runner = get_runner("icarus")
    runner.build(
        sources=[Path(__file__).parent / "clock_divider.sv"],
        hdl_toplevel="clock_divider",
        build_dir=str(build_dir),
        build_args=["-g2012", "-DCOCOTB_SIM=1"],
        timescale=("1ns", "1ps"),
        waves=True,
    )
    runner.test(
        hdl_toplevel="clock_divider",
        test_module="test_clock_divider",
        build_dir=str(build_dir),
        waves=True,
    )
