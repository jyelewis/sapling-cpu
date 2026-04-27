def reg(tb_dut, reg_number: int) -> int:
    assert 0 <= reg_number <= 7
    return tb_dut.sapling_cpu_core.register_bank.registers[reg_number].value
