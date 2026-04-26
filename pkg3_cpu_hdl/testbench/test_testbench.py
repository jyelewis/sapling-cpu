from cocotb.triggers import ClockCycles

from test_utilities import asm, repo_root, setup_cocotb_tests, show_waveform


#
# async def reset_dut(dut):
#     dut.reset.value = 1
#     await ClockCycles(dut.clk, 2)
#     dut.reset.value = 0


@show_waveform(True)
@asm("""
NOP
NOP
NOP
""")
async def test_output_clock(dut):
    # cocotb.start_soon(Clock(dut.clk, 2, unit="ns").start())
    # await reset_dut(dut)

    # TODO: use our own utils instead
    await ClockCycles(dut.clk, 20)


types_path = repo_root / "pkg3_cpu_hdl" / "types.sv"
modules_path = repo_root / "pkg3_cpu_hdl" / "modules"
tb_path = repo_root / "pkg3_cpu_hdl" / "testbench"
setup_cocotb_tests(
    globals(),
    auto_reset=True,
    auto_clk=True,
    sources=[types_path] + list(modules_path.rglob("*.sv")) + list(tb_path.rglob("*.sv")),
)
