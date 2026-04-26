from test_utilities import asm, repo_root, setup_cocotb_tests, show_waveform, tick


@show_waveform(False)
@asm("""
NOP
NOP
NOP
""")
async def test_output_clock(dut):
    await tick(dut)
    await tick(dut)
    await tick(dut)
    await tick(dut)
    await tick(dut)
    await tick(dut)


types_path = repo_root / "pkg3_cpu_hdl" / "types.sv"
modules_path = repo_root / "pkg3_cpu_hdl" / "modules"
tb_path = repo_root / "pkg3_cpu_hdl" / "testbench"
setup_cocotb_tests(
    globals(),
    auto_reset=True,
    auto_clk=True,
    sources=[types_path] + list(modules_path.rglob("*.sv")) + list(tb_path.rglob("*.sv")),
)
