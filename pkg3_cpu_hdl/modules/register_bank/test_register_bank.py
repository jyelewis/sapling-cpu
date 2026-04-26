from test_utilities import comb_tick, setup_cocotb_tests, tick


async def test_inits_zero(dut):
    # clear input state
    dut.ctrl_read_register_a.value = 0
    dut.ctrl_read_register_b.value = 0
    dut.ctrl_write_register.value = 0
    dut.register_write_data.value = 0
    dut.ctrl_register_write_enable.value = 0
    await tick(dut)

    assert dut.register_read_data_a.value == 0
    assert dut.register_read_data_b.value == 0

    dut.ctrl_read_register_a.value = 1
    dut.ctrl_read_register_b.value = 2
    await comb_tick()
    assert dut.register_read_data_a.value == 0
    assert dut.register_read_data_b.value == 0

    dut.ctrl_read_register_a.value = 3
    dut.ctrl_read_register_b.value = 4
    await comb_tick()
    assert dut.register_read_data_a.value == 0
    assert dut.register_read_data_b.value == 0

    dut.ctrl_read_register_a.value = 5
    dut.ctrl_read_register_b.value = 6
    await comb_tick()
    assert dut.register_read_data_a.value == 0
    assert dut.register_read_data_b.value == 0

    dut.ctrl_read_register_a.value = 6
    dut.ctrl_read_register_b.value = 7
    await comb_tick()
    assert dut.register_read_data_a.value == 0
    assert dut.register_read_data_b.value == 0


async def test_write_to_each(dut):
    # clear input state
    dut.ctrl_read_register_a.value = 0
    dut.ctrl_read_register_b.value = 0
    dut.ctrl_write_register.value = 0
    dut.register_write_data.value = 0
    dut.ctrl_register_write_enable.value = 0
    await tick(dut)

    # test writing to each register, one by one
    for reg in range(0, 7):
        dut.ctrl_write_register.value = reg
        dut.register_write_data.value = reg + 5
        dut.ctrl_register_write_enable.value = 1
        dut.ctrl_read_register_a.value = reg  # read back our value
        dut.ctrl_read_register_b.value = reg  # on both ports

        await comb_tick()
        # pre-read, old value
        assert dut.register_read_data_a.value == 0
        assert dut.register_read_data_b.value == 0

        # do the write
        await tick(dut)
        assert dut.register_read_data_a.value == reg + 5
        assert dut.register_read_data_b.value == reg + 5

        # reset
        dut.register_write_data.value = 0
        dut.ctrl_register_write_enable.value = 0
        await tick(dut)

    # all registers should retain their number + 5
    for reg in range(0, 7):
        dut.ctrl_read_register_a.value = reg  # read back our value
        dut.ctrl_read_register_b.value = reg  # on both ports
        await comb_tick()
        assert dut.register_read_data_a.value == reg + 5
        assert dut.register_read_data_b.value == reg + 5


setup_cocotb_tests(globals(), auto_clk=True, auto_reset=True)
