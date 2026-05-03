from enum import Enum

from test_utilities import comb_tick, setup_cocotb_tests


class AluOp(Enum):
    ADD = 0
    SUB = 1
    AND = 2
    OR = 3
    XOR = 4
    SHL = 5
    SHR = 6


async def do_alu_op(
    dut,
    op: AluOp,
    lhs: int,
    result: int,
    rhs: int = 0,
    carry_in: int = 0,
    flag_zero: bool = False,
    flag_negative: bool = False,
    flag_carry: bool = False,
    flag_overflow: bool = False,
):
    dut.ctrl_alu_op.value = op.value
    dut.alu_lhs.value = lhs
    dut.alu_rhs.value = rhs
    dut.alu_carry_in.value = carry_in

    await comb_tick()

    assert dut.alu_result.value == result

    assert dut.alu_result_flags.value[0] == flag_zero
    assert dut.alu_result_flags.value[1] == flag_negative
    assert dut.alu_result_flags.value[2] == flag_carry
    assert dut.alu_result_flags.value[3] == flag_overflow


def to_signed(value: int) -> int:
    if value >= 128:
        value -= 256
    return value


async def test_add(dut):
    # basic operations
    await do_alu_op(dut, op=AluOp.ADD, lhs=0, rhs=0, result=0, flag_zero=True)
    await do_alu_op(dut, op=AluOp.ADD, lhs=2, rhs=3, result=5)
    await do_alu_op(dut, op=AluOp.ADD, lhs=100, rhs=150, result=250, flag_negative=True)
    await do_alu_op(dut, op=AluOp.ADD, lhs=250, rhs=15, result=9, flag_carry=True)
    await do_alu_op(dut, op=AluOp.ADD, lhs=50, rhs=-6, result=44, flag_carry=True)

    # overflow
    await do_alu_op(dut, op=AluOp.ADD, lhs=120, rhs=30, result=150, flag_overflow=True, flag_negative=True)
    await do_alu_op(dut, op=AluOp.ADD, lhs=127, rhs=0, result=127, flag_overflow=False, flag_negative=False)
    await do_alu_op(dut, op=AluOp.ADD, lhs=127, rhs=1, result=128, flag_overflow=True, flag_negative=True)
    await do_alu_op(dut, op=AluOp.ADD, lhs=50, rhs=50, result=100)
    await do_alu_op(dut, op=AluOp.ADD, lhs=128, rhs=-2, result=126, flag_carry=True, flag_overflow=True)
    await do_alu_op(dut, op=AluOp.ADD, lhs=126, rhs=-1, result=125, flag_carry=True, flag_overflow=False)

    # neg
    await do_alu_op(dut, op=AluOp.ADD, lhs=0, rhs=1, result=1, flag_negative=False)
    await do_alu_op(dut, op=AluOp.ADD, lhs=0, rhs=100, result=100, flag_negative=False)
    await do_alu_op(dut, op=AluOp.ADD, lhs=0, rhs=126, result=126, flag_negative=False)
    await do_alu_op(dut, op=AluOp.ADD, lhs=0, rhs=127, result=127, flag_negative=False)
    await do_alu_op(dut, op=AluOp.ADD, lhs=0, rhs=128, result=128, flag_negative=True)
    await do_alu_op(dut, op=AluOp.ADD, lhs=0, rhs=255, result=255, flag_negative=True)


async def test_sub(dut):
    # basic operations
    await do_alu_op(dut, op=AluOp.SUB, lhs=0, rhs=0, result=0, flag_zero=True)
    await do_alu_op(dut, op=AluOp.SUB, lhs=5, rhs=3, result=2)
    await do_alu_op(dut, op=AluOp.SUB, lhs=10, rhs=10, result=0, flag_zero=True)
    await do_alu_op(dut, op=AluOp.SUB, lhs=255, rhs=255, result=0, flag_zero=True)
    await do_alu_op(dut, op=AluOp.SUB, lhs=200, rhs=56, result=144, flag_negative=True)

    # carry (borrow) — carry=True means lhs < rhs (unsigned)
    await do_alu_op(dut, op=AluOp.SUB, lhs=0, rhs=1, result=255, flag_carry=True, flag_negative=True)
    await do_alu_op(dut, op=AluOp.SUB, lhs=1, rhs=2, result=255, flag_carry=True, flag_negative=True)
    await do_alu_op(
        dut, op=AluOp.SUB, lhs=50, rhs=-6, result=56, flag_carry=True
    )  # 50 - 250 borrows, but signed 50-(-6)=56 fits fine
    await do_alu_op(dut, op=AluOp.SUB, lhs=5, rhs=10, result=251, flag_carry=True, flag_negative=True)

    # overflow
    # positive - negative(large) → result wraps to negative
    await do_alu_op(
        dut, op=AluOp.SUB, lhs=127, rhs=255, result=128, flag_carry=True, flag_overflow=True, flag_negative=True
    )  # +127 - (-1) = +128, no room
    await do_alu_op(
        dut, op=AluOp.SUB, lhs=1, rhs=128, result=129, flag_carry=True, flag_overflow=True, flag_negative=True
    )  # +1 - (-128) = +129, no room
    # negative - positive → result wraps to positive
    await do_alu_op(
        dut, op=AluOp.SUB, lhs=128, rhs=1, result=127, flag_carry=False, flag_overflow=True, flag_negative=False
    )  # -128 - 1 = -129, no room
    await do_alu_op(
        dut, op=AluOp.SUB, lhs=128, rhs=127, result=1, flag_carry=False, flag_overflow=True, flag_negative=False
    )  # -128 - 127 = -255, no room
    # no overflow — same sign inputs can't overflow
    await do_alu_op(dut, op=AluOp.SUB, lhs=127, rhs=1, result=126, flag_overflow=False)
    await do_alu_op(
        dut, op=AluOp.SUB, lhs=200, rhs=150, result=50, flag_overflow=False
    )  # both MSB=1 (same sign), no overflow despite crossing sign boundary in result
    await do_alu_op(dut, op=AluOp.SUB, lhs=50, rhs=6, result=44, flag_overflow=False)

    # neg flag
    await do_alu_op(dut, op=AluOp.SUB, lhs=0, rhs=1, result=255, flag_carry=True, flag_negative=True)
    await do_alu_op(
        dut, op=AluOp.SUB, lhs=128, rhs=1, result=127, flag_overflow=True, flag_negative=False
    )  # overflow flips to positive
    await do_alu_op(
        dut, op=AluOp.SUB, lhs=129, rhs=1, result=128, flag_negative=True, flag_overflow=False
    )  # same-sign, stays negative
    await do_alu_op(
        dut, op=AluOp.SUB, lhs=0, rhs=128, result=128, flag_carry=True, flag_negative=True, flag_overflow=True
    )


async def test_and(dut):
    await do_alu_op(dut, op=AluOp.AND, lhs=0b00000000, rhs=0b00000001, result=0b00000000, flag_zero=True)
    await do_alu_op(dut, op=AluOp.AND, lhs=0b00000001, rhs=0b00000000, result=0b00000000, flag_zero=True)
    await do_alu_op(dut, op=AluOp.AND, lhs=0b00000001, rhs=0b00000001, result=0b00000001)
    await do_alu_op(dut, op=AluOp.AND, lhs=0b00000000, rhs=0b00000000, result=0b00000000, flag_zero=True)
    await do_alu_op(dut, op=AluOp.AND, lhs=0b11111111, rhs=0b00000000, result=0b00000000, flag_zero=True)
    await do_alu_op(dut, op=AluOp.AND, lhs=0b00000000, rhs=0b11111111, result=0b00000000, flag_zero=True)
    await do_alu_op(dut, op=AluOp.AND, lhs=0b11111111, rhs=0b11111111, result=0b11111111, flag_negative=True)

    # alternating patterns — AND of complements always zeroes out
    await do_alu_op(dut, op=AluOp.AND, lhs=0b10101010, rhs=0b01010101, result=0b00000000, flag_zero=True)
    await do_alu_op(dut, op=AluOp.AND, lhs=0b01010101, rhs=0b10101010, result=0b00000000, flag_zero=True)
    # AND of same pattern preserves it
    await do_alu_op(dut, op=AluOp.AND, lhs=0b10101010, rhs=0b10101010, result=0b10101010, flag_negative=True)
    await do_alu_op(dut, op=AluOp.AND, lhs=0b01010101, rhs=0b01010101, result=0b01010101)

    # masking — common real-world use
    await do_alu_op(dut, op=AluOp.AND, lhs=0b11001101, rhs=0b00001111, result=0b00001101)  # mask low nibble
    await do_alu_op(
        dut, op=AluOp.AND, lhs=0b11001101, rhs=0b11110000, result=0b11000000, flag_negative=True
    )  # mask high nibble


async def test_or(dut):
    await do_alu_op(dut, op=AluOp.OR, lhs=0b00000000, rhs=0b00000000, result=0b00000000, flag_zero=True)

    await do_alu_op(dut, op=AluOp.OR, lhs=0b00000000, rhs=0b00000001, result=0b00000001)
    await do_alu_op(dut, op=AluOp.OR, lhs=0b00000001, rhs=0b00000000, result=0b00000001)
    await do_alu_op(dut, op=AluOp.OR, lhs=0b00000000, rhs=0b00000010, result=0b00000010)
    await do_alu_op(dut, op=AluOp.OR, lhs=0b00000010, rhs=0b00000000, result=0b00000010)
    await do_alu_op(dut, op=AluOp.OR, lhs=0b11111111, rhs=0b00000000, result=0b11111111, flag_negative=True)
    await do_alu_op(dut, op=AluOp.OR, lhs=0b00000000, rhs=0b11111111, result=0b11111111, flag_negative=True)

    await do_alu_op(dut, op=AluOp.OR, lhs=0b10101010, rhs=0b01010101, result=0b11111111, flag_negative=True)
    await do_alu_op(dut, op=AluOp.OR, lhs=0b01010101, rhs=0b10101010, result=0b11111111, flag_negative=True)


async def test_shl(dut):
    # basic
    await do_alu_op(dut, op=AluOp.SHL, lhs=0b00000000, result=0b00000000, flag_zero=True)
    await do_alu_op(dut, op=AluOp.SHL, lhs=0b00000001, result=0b00000010)
    await do_alu_op(dut, op=AluOp.SHL, lhs=0b00000010, result=0b00000100)
    await do_alu_op(dut, op=AluOp.SHL, lhs=0b01010101, result=0b10101010, flag_negative=True)

    # carry — MSB shifts out
    await do_alu_op(dut, op=AluOp.SHL, lhs=0b10000000, result=0b00000000, flag_carry=True, flag_zero=True)
    await do_alu_op(dut, op=AluOp.SHL, lhs=0b11111111, result=0b11111110, flag_carry=True, flag_negative=True)
    await do_alu_op(dut, op=AluOp.SHL, lhs=0b01111111, result=0b11111110, flag_carry=False, flag_negative=True)
    await do_alu_op(dut, op=AluOp.SHL, lhs=0b10101010, result=0b01010100, flag_carry=True)


async def test_shr(dut):
    # basic
    await do_alu_op(dut, op=AluOp.SHR, lhs=0b00000000, result=0b00000000, flag_zero=True)
    await do_alu_op(dut, op=AluOp.SHR, lhs=0b10000000, result=0b01000000)
    await do_alu_op(dut, op=AluOp.SHR, lhs=0b01000000, result=0b00100000)
    await do_alu_op(dut, op=AluOp.SHR, lhs=0b10101010, result=0b01010101)

    # carry — LSB shifts out
    await do_alu_op(dut, op=AluOp.SHR, lhs=0b00000001, result=0b00000000, flag_carry=True, flag_zero=True)
    await do_alu_op(dut, op=AluOp.SHR, lhs=0b11111111, result=0b01111111, flag_carry=True)
    await do_alu_op(dut, op=AluOp.SHR, lhs=0b11111110, result=0b01111111, flag_carry=False)
    await do_alu_op(dut, op=AluOp.SHR, lhs=0b01010101, result=0b00101010, flag_carry=True)

    # MSB always 0 after SHR (logical shift)
    await do_alu_op(dut, op=AluOp.SHR, lhs=0b11111111, result=0b01111111, flag_negative=False, flag_carry=True)
    await do_alu_op(dut, op=AluOp.SHR, lhs=0b10000000, result=0b01000000, flag_negative=False)


setup_cocotb_tests(globals())
