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


# TODO: validate instructions following this memory write work, I suspect they won't
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

    assert read_memory_byte(dut, 0x0102) == 0xAB
    await tick(dut)
    await tick(dut)
    await tick(dut)
    await tick(dut)


# TODO: this is not working, suspect something about pipelining instructions after memory fetches
@show_waveform(True)
@asm("""
// value to write
LD R0 0xAB

// write to SP+10
ST #[SP + 50] R0
LD R1 #[SP + 50]
""")
async def test_load_store_mem_sp_rel(dut):
    await wait_startup(dut)

    await tick(dut)  # LD R0 0xAB
    await tick(dut)  # ST [SP+10] R0
    await tick(dut)  # memory cycle
    await tick(dut)  # LD [SP+10] R1
    await tick(dut)  # memory cycle
    await tick(dut)  # ???
    await tick(dut)
    await tick(dut)
    await tick(dut)

    # TODO: this is failing due to timing issues after the microcode stall in the PC
    assert read_memory_byte(dut, 0x00A) == 0xAB
    assert reg(dut, 1) == 0xAB


@asm("""
LD R5 0x05
LD R6 0x06

ADD R5 R6 CARRY_ZERO
""")
async def test_alu_add(dut):
    await wait_startup(dut)

    await tick(dut)  # LD R5 0x05
    await tick(dut)  # LD R6 0x06
    await tick(dut)  # ADD R5 R6
    assert reg(dut, 5) == 0x0B


@asm("""
LD R5 0x05
LD R6 0x06

ADD R5 R6 CARRY_ONE
""")
async def test_alu_add_carry_one(dut):
    await wait_startup(dut)

    await tick(dut)  # LD R5 0x05
    await tick(dut)  # LD R6 0x06
    await tick(dut)  # ADD R5 R6
    assert reg(dut, 5) == 0x0C


@asm("""
LD R4 0
LD R5 250
LD R6 30

ADD R5 R6 CARRY_ZERO
ADD R4 R4 CARRY_LAST
""")
async def test_alu_add_carry_last(dut):
    await wait_startup(dut)

    await tick(dut)  # LD R4 0
    await tick(dut)  # LD R5 0x05
    await tick(dut)  # LD R6 0x06

    await tick(dut)  # ADD R5 R6 CARRY_ZERO
    await tick(dut)  # ADD R4 R4 CARRY_LAST

    assert reg(dut, 5) == 24
    assert reg(dut, 4) == 1


@asm("""
LD R5 0x06
LD R6 0x05

SUB R5 R6 CARRY_ZERO
""")
async def test_alu_sub(dut):
    await wait_startup(dut)

    await tick(dut)
    await tick(dut)
    await tick(dut)
    assert reg(dut, 5) == 0x01


@asm("""
LD R5 0x06
LD R6 0x05

SUB R5 R6 CARRY_ONE
""")
async def test_alu_sub_carry_one(dut):
    await wait_startup(dut)

    await tick(dut)
    await tick(dut)
    await tick(dut)
    assert reg(dut, 5) == 0x00


@asm("""
LD R3 0
LD R4 10
LD R5 30
LD R6 250

SUB R5 R6 CARRY_ZERO
SUB R4 R3 CARRY_LAST
""")
async def test_alu_sub_carry_last(dut):
    await wait_startup(dut)

    await tick(dut)
    await tick(dut)
    await tick(dut)
    await tick(dut)

    await tick(dut)
    await tick(dut)

    assert reg(dut, 5) == 36
    assert reg(dut, 4) == 9


@asm("""
LD R3 0
LD R4 10
LD R5 30
LD R6 250

CMP R5 R6 CARRY_ZERO
SUB R4 R3 CARRY_LAST
""")
async def test_alu_cmp_carry_last(dut):
    await wait_startup(dut)

    await tick(dut)
    await tick(dut)
    await tick(dut)
    await tick(dut)

    await tick(dut)
    await tick(dut)

    assert reg(dut, 5) == 30
    assert reg(dut, 4) == 9


@asm("""
LD R5 0b10101010
LD R6 0b00001111

AND R5 R6
""")
async def test_alu_and(dut):
    await wait_startup(dut)

    await tick(dut)
    await tick(dut)
    await tick(dut)
    assert reg(dut, 5) == 0b0001010


@asm("""
LD R5 0b10101010
LD R6 0b00001111

OR R5 R6
""")
async def test_alu_or(dut):
    await wait_startup(dut)

    await tick(dut)
    await tick(dut)
    await tick(dut)
    assert reg(dut, 5) == 0b10101111


@asm("""
LD R5 0b10101010
LD R6 0b00001111

XOR R5 R6
""")
async def test_alu_xor(dut):
    await wait_startup(dut)

    await tick(dut)
    await tick(dut)
    await tick(dut)
    assert reg(dut, 5) == 0b10100101


@asm("""
LD R5 0b00111100
SHL R5
""")
async def test_alu_shl(dut):
    await wait_startup(dut)

    await tick(dut)
    await tick(dut)
    assert reg(dut, 5) == 0b01111000


@asm("""
LD R5 0b00111100
SHR R5
""")
async def test_alu_shr(dut):
    await wait_startup(dut)

    await tick(dut)
    await tick(dut)
    assert reg(dut, 5) == 0b00011110


# TODO: test flags


types_path = repo_root / "pkg3_cpu_hdl" / "types.sv"
modules_path = repo_root / "pkg3_cpu_hdl" / "modules"
tb_path = repo_root / "pkg3_cpu_hdl" / "testbench"
setup_cocotb_tests(
    globals(),
    auto_reset=True,
    auto_clk=True,
    sources=[types_path] + list(modules_path.rglob("*.sv")) + list(tb_path.rglob("*.sv")),
)
