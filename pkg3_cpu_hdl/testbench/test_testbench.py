from test_utilities import asm, read_memory_byte, reg, repo_root, setup_cocotb_tests, show_waveform, tick

# TODO: should we run these on both the vm & the verilog tb? Check they behave the same


async def wait_startup(dut):
    # TODO: whats the 2 clocks for setup?
    await tick(dut)
    await tick(dut)
    # next tick we execute instruction 0x0000


@show_waveform(False)
@asm("""
NOP
""")
async def test_starts_up(dut):
    await wait_startup(dut)


@show_waveform(False)
@asm("""
LD R0 0x12
LD R1 0x34
LD R2 0x56
LD R3 0x78
LD R4 0x9A
""")
async def test_load_reg_imm8(dut):
    await wait_startup(dut)

    # run instruction 1
    await tick(dut)
    assert reg(dut, 0) == 0x12
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x00
    assert reg(dut, 3) == 0x00
    assert reg(dut, 4) == 0x00

    # run instruction 2
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


@show_waveform(False)
@asm("""
LD R0 0xAB
LD R1 R0
LD R2 R1
""")
async def test_load_reg_reg(dut):
    await wait_startup(dut)

    assert reg(dut, 0) == 0x00
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0xAB
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0xAB
    assert reg(dut, 1) == 0xAB
    assert reg(dut, 2) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0xAB
    assert reg(dut, 1) == 0xAB
    assert reg(dut, 2) == 0xAB


@show_waveform(False)
@asm("""
// constant at byte 1
LD R0 0xAB

// load address
LD R1 0x00
LD R2 0x01

// load our constant from byte 1
LD R3 #[R1 R2]
""")
async def test_load_reg_mem_absolute(dut):
    await wait_startup(dut)

    assert reg(dut, 0) == 0x00
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x00
    assert reg(dut, 3) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0xAB
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x00
    assert reg(dut, 3) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0xAB
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x00
    assert reg(dut, 3) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0xAB
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x01
    assert reg(dut, 3) == 0x00

    # LD is a 2 cycle instruction
    await tick(dut)
    await tick(dut)
    assert reg(dut, 0) == 0xAB
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x01
    assert reg(dut, 3) == 0xAB  # load imm8 from the original instruction


@show_waveform(False)
@asm("""
// value to write
LD R0 0xAB

// load address 0x0102
LD R1 0x01
LD R2 0x02

// store 0xAB at 0x0102
ST #[R1 R2] R0
""")
async def test_store_reg_mem_absolute(dut):
    await wait_startup(dut)

    assert reg(dut, 0) == 0x00
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0xAB
    assert reg(dut, 1) == 0x00
    assert reg(dut, 2) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0xAB
    assert reg(dut, 1) == 0x01
    assert reg(dut, 2) == 0x00

    await tick(dut)
    assert reg(dut, 0) == 0xAB
    assert reg(dut, 1) == 0x01
    assert reg(dut, 2) == 0x02

    assert read_memory_byte(dut, 0x0102) == 0x00

    # LD is a 2 cycle instruction
    await tick(dut)
    await tick(dut)

    # TODO: this is failing, we seem to write to 0x0202 instead?? No idea why
    assert read_memory_byte(dut, 0x0202) == 0xAB # TODO: WHY 0x0202??
    assert read_memory_byte(dut, 0x0102) == 0xAB # TODO: WHY NOT 0x0102
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
