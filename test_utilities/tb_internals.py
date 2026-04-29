def reg(tb_dut, reg_number: int) -> int:
    assert 0 <= reg_number <= 7
    return tb_dut.sapling_cpu_core.register_bank.registers[reg_number].value


# def read_memory_byte(dut, addr: int) -> int:
#     # odd addressing of our tb_memory_controller for emulation performance
#     byte_index = addr * 8
#     # TODO: check this works
#     memory_data = dut.tb_memory_controller.memory.value
#     return memory_data[byte_index : 8].value


# TODO: tnx claude, glhf
def read_memory_byte(dut, address: int) -> int:
    """
    Read a byte from a packed memory vector indexed as `memory[addr*8 +: 8]`.

    Args:
        memory_signal: cocotb handle to the packed `logic [2**16*8-1:0] memory`
                       (e.g. ``dut.mem_ctrl.memory``).
        address: 16-bit byte address (0..0xFFFF).

    Returns:
        The byte value (0..255) stored at that address.
    """
    if not 0 <= address <= 0xFFFF:
        raise ValueError(f"address {address:#06x} out of range")

    binstr = dut.tb_memory_controller.memory.value.binstr
    total_bits = len(binstr)
    # binstr is MSB-first: bit (total_bits-1) at index 0, bit 0 at the end.
    # The byte at `address` is source bits [address*8 + 7 : address*8].
    end = total_bits - address * 8  # one past the LSB of the byte
    start = end - 8  # MSB of the byte
    return int(binstr[start:end], 2)
