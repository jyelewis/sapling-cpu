from test_utilities import asm, reg, repo_root, setup_cocotb_tests, show_waveform, tick


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


@show_waveform(False)
@asm("""
LD R0 0x12
LD R1 0x34
LD R2 0x56
LD R3 0x78
LD R4 0x9A
""")
async def test_load_reg_imm8(dut):
    # TODO: whats the 4 clocks for setup?
    await tick(dut)
    await tick(dut)
    await tick(dut)
    await tick(dut)

    # run instruction 1
    await tick(dut)
    assert reg(dut, 0) == 0x12
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x00
    assert reg(dut, 3) == 0x00
    assert reg(dut, 4) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0x12
    assert reg(dut, 1) == 0x34
    assert reg(dut, 2) == 0x00
    assert reg(dut, 3) == 0x00
    assert reg(dut, 4) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0x12
    assert reg(dut, 1) == 0x34
    assert reg(dut, 2) == 0x56
    assert reg(dut, 3) == 0x00
    assert reg(dut, 4) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0x12
    assert reg(dut, 1) == 0x34
    assert reg(dut, 2) == 0x56
    assert reg(dut, 3) == 0x78
    assert reg(dut, 4) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0x12
    assert reg(dut, 1) == 0x34
    assert reg(dut, 2) == 0x56
    assert reg(dut, 3) == 0x78
    assert reg(dut, 4) == 0x9A


types_path = repo_root / "pkg3_cpu_hdl" / "types.sv"
modules_path = repo_root / "pkg3_cpu_hdl" / "modules"
tb_path = repo_root / "pkg3_cpu_hdl" / "testbench"
setup_cocotb_tests(
    globals(),
    auto_reset=True,
    auto_clk=True,
    sources=[types_path] + list(modules_path.rglob("*.sv")) + list(tb_path.rglob("*.sv")),
)
