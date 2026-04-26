from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def reset_dut(dut):
    dut.reset.value = 1
    await ClockCycles(dut.clk, 2)
    dut.reset.value = 0


@cocotb.test()
async def test_output_clock(dut):
    cocotb.start_soon(Clock(dut.clk, 2, unit="ns").start())
    await reset_dut(dut)

    await ClockCycles(dut.clk, 20)


# TODO: write some nicer test utils
def test_testbench():
    from cocotb_tools.runner import get_runner

    repo_root = Path(__file__).resolve().parents[2]
    build_dir = repo_root / "build" / "cocotb" / "testbench"

    modules_path = repo_root / "pkg3_cpu_hdl" / "modules"
    tb_path = repo_root / "pkg3_cpu_hdl" / "testbench"
    sources = list(modules_path.rglob("*.sv")) + list(tb_path.rglob("*.sv"))

    # assembly & write init memory
    import os
    import tempfile

    from pkg4_compiler.assembler import asm_to_bin

    assembled_words = asm_to_bin(["LD R1 R2", "NOP", "NOP"])
    initial_memory_hex = "\n".join([f"{word:04x}" for word in assembled_words])

    initial_memory = bytearray()
    for word in assembled_words:
        initial_memory.extend(word.to_bytes(2, byteorder="big"))
    fd, tmp_path = tempfile.mkstemp(suffix=".hex")
    os.close(fd)
    bin_file = Path(tmp_path)
    bin_file.write_text(initial_memory_hex)

    runner = get_runner("icarus")
    runner.build(
        # sources=[Path(__file__).parent / "testbench.sv"],
        sources=sources,
        hdl_toplevel="testbench",
        build_dir=str(build_dir),
        build_args=["-g2012", "-DCOCOTB_SIM=1"],
        defines={"TB_MEMORY_CONTROLLER_INIT_DATA": str(tmp_path)},
        timescale=("1ns", "1ps"),
        waves=False,
    )
    runner.test(
        hdl_toplevel="testbench",
        test_module="pkg3_cpu_hdl.testbench.test_testbench",
        build_dir=str(build_dir),
        waves=False,
    )
