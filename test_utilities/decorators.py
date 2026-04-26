import os
import tempfile
from pathlib import Path

from pkg4_compiler.assembler import asm_to_bin


def verilog_define(constant_name: str, value: str):
    """
    decorator to specify build time defines for a test

    example:
    @verilog_define("TB_MEMORY_CONTROLLER_INIT_DATA", "/Users/jyelewis/dev-personal/sapling-cpu/pkg3_cpu_hdl/testbench/tb_modules/tb_memory_controller/test_data.hex")
    def my_test(dut):
        ...
    """

    def decorator(fn):
        if not hasattr(fn, "_verilog_defines"):
            fn._verilog_defines = {}

        if constant_name in fn._verilog_defines:
            raise Exception(f"verilog_define: constant {constant_name} already defined for function {fn.__name__}")

        fn._verilog_defines[constant_name] = value
        return fn

    return decorator


def asm(code: str):
    """
    decorator to specify assembly code to be assembled and loaded into memory before a test runs
    """
    assembled_words = asm_to_bin(code.strip().splitlines())
    initial_memory_hex = "\n".join([f"{word:04x}" for word in assembled_words])

    initial_memory = bytearray()
    for word in assembled_words:
        initial_memory.extend(word.to_bytes(2, byteorder="big"))
    fd, tmp_path = tempfile.mkstemp(suffix=".hex")
    os.close(fd)
    hex_file = Path(tmp_path)
    hex_file.write_text(initial_memory_hex)

    # meta decorator - attach our newly written hex file as a verilog define
    # when the test case runs, it'll load our program from the hex file we just wrote
    # into the test bench memory controller, before execution starts
    return verilog_define("TB_MEMORY_CONTROLLER_INIT_DATA", str(tmp_path))

def show_waveform(show_waveform: bool = True):
    def decorator(fn):
        fn.show_waveform = show_waveform
        return fn

    return decorator