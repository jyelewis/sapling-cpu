from test_utilities import comb_tick, setup_cocotb_tests


# TODO: many more tests per op
async def test_add_1(dut):
    # TODO: enum alu ops?
    dut.alu_op.value = 0  # add
    dut.alu_lhs.value = 2
    dut.alu_rhs.value = 3
    dut.alu_carry_in.value = 0

    await comb_tick()

    assert dut.alu_result.value == 5
    assert dut.alu_carry_out.value == 0

    assert dut.alu_flag_zero.value == 0
    assert dut.alu_flag_negative.value == 0
    assert dut.alu_flag_carry.value == 0
    assert dut.alu_flag_overflow.value == 0


setup_cocotb_tests(globals())
