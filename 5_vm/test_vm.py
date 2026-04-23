"""End-to-end VM tests.

Two paths are exercised:
  1. Small inline ASM programs assembled through the real assembler → VM.
  2. Instructions built directly via assemble_instruction() when the test
     needs precise control over opcodes/operands.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "4_compiler"))

from assembler import asm_to_bin, assemble_instruction, Opcode, to_signed_imm8  # noqa: E402
from vm import (  # noqa: E402
    FLAG_CF,
    FLAG_NF,
    FLAG_OF,
    FLAG_ZF,
    IODevice,
    SaplingCpuEmu,
)


def words_to_bytes(words: list[int]) -> bytes:
    out = bytearray()
    for w in words:
        out.extend(w.to_bytes(2, byteorder="big"))
    return bytes(out)


def assemble_source(source: str) -> bytes:
    return words_to_bytes(asm_to_bin(source.splitlines()))


def assemble_file(path: str) -> bytes:
    with open(path) as f:
        return assemble_source(f.read())


def run_words(words: list[int], *, max_steps: int = 1000,
              io: dict[int, IODevice] | None = None) -> SaplingCpuEmu:
    cpu = SaplingCpuEmu()
    cpu.load_program(words_to_bytes(words))
    if io:
        for num, dev in io.items():
            cpu.attach_io_device(num, dev)
    cpu.run(max_steps=max_steps)
    return cpu


def run_source(source: str, **kwargs) -> SaplingCpuEmu:
    return run_words(asm_to_bin(source.splitlines()), **kwargs)


# --- small inline programs (uses real assembler) ----------------------


def test_program_io_echo():
    class Dev(IODevice):
        def __init__(self, value):
            super().__init__()
            self.value = value
            self.writes = []
        def read(self):
            return self.value
        def write(self, v):
            self.writes.append(v)

    dev_in = Dev(0x5A)
    dev_out = Dev(0)
    cpu = SaplingCpuEmu()
    cpu.load_program(assemble_source("""
        // Read one byte from DEV1, write it back to DEV2, then halt.
        IN R0 DEV1
        OUT DEV2 R0
        WFI
    """))
    cpu.attach_io_device(1, dev_in)
    cpu.attach_io_device(2, dev_out)
    cpu.run(max_steps=100)
    assert cpu.halted
    assert dev_out.writes == [0x5A]


def test_program_load_store():
    cpu = SaplingCpuEmu()
    cpu.load_program(assemble_source("""
        // Exercise LD immediate, LD reg-reg, and the special-register path.
        LD R0 0xAB
        LD R1 R0
        LD R2 $FLAGS
        WFI
    """))
    cpu.run(max_steps=100)
    assert cpu.registers[0] == 0xAB
    assert cpu.registers[1] == 0xAB
    assert cpu.registers[2] == cpu.flags
    assert cpu.halted


# --- basic instructions (via .sam) ------------------------------------


def test_nop_and_halt():
    cpu = run_source("NOP\nNOP\nWFI\n")
    assert cpu.halted
    assert cpu.instructions_executed == 3


def test_load_imm_and_reg_copy():
    cpu = run_source("""
        LD R0 0x42
        LD R1 R0
        WFI
    """)
    assert cpu.registers[0] == 0x42
    assert cpu.registers[1] == 0x42


# --- arithmetic / flags (instruction-level) ---------------------------


def test_add_sets_zero_and_carry():
    # R0 = 0xFF; R1 = 0x01; ADD R0 R1
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=0xFF),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0x01),
        assemble_instruction(Opcode(0x0B), 0, 1),   # ADD
        assemble_instruction(Opcode(0x1D)),          # WFI
    ])
    assert cpu.registers[0] == 0x00
    assert cpu.flags & FLAG_ZF
    assert cpu.flags & FLAG_CF
    assert not (cpu.flags & FLAG_NF)


def test_sub_negative_and_borrow():
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=0x01),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0x02),
        assemble_instruction(Opcode(0x0C), 0, 1),   # SUB
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[0] == 0xFF
    assert cpu.flags & FLAG_NF
    assert cpu.flags & FLAG_CF
    assert not (cpu.flags & FLAG_ZF)


def test_add_signed_overflow():
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=0x7F),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0x01),
        assemble_instruction(Opcode(0x0B), 0, 1),   # ADD
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[0] == 0x80
    assert cpu.flags & FLAG_OF
    assert cpu.flags & FLAG_NF
    assert not (cpu.flags & FLAG_CF)


def test_cmp_equal_sets_zero_no_writeback():
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=0x55),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0x55),
        assemble_instruction(Opcode(0x0D), 0, 1),   # CMP
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[0] == 0x55
    assert cpu.flags & FLAG_ZF


def test_logical_and_or_xor():
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=0xF0),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0x0F),
        assemble_instruction(Opcode(0x0E), 0, 1),   # AND
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[0] == 0

    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=0xF0),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0x0F),
        assemble_instruction(Opcode(0x0F), 0, 1),   # OR
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[0] == 0xFF

    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=0xAA),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0xFF),
        assemble_instruction(Opcode(0x10), 0, 1),   # XOR
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[0] == 0x55


def test_shifts():
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=0x81),
        assemble_instruction(Opcode(0x11), 0),      # SHL
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[0] == 0x02
    assert cpu.flags & FLAG_CF

    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=0x03),
        assemble_instruction(Opcode(0x12), 0),      # SHR
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[0] == 0x01
    assert cpu.flags & FLAG_CF


# --- control flow -----------------------------------------------------


def test_jmp_relative_skips_instruction():
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=1),
        assemble_instruction(Opcode(0x13), immediate=to_signed_imm8(1)),  # JMP +1
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=99),
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[0] == 1


def test_beq_taken():
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=5),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=5),
        assemble_instruction(Opcode(0x0D), 0, 1),   # CMP R0 R1 → ZF=1
        assemble_instruction(Opcode(0x17), immediate=to_signed_imm8(1)),  # BEQ +1
        assemble_instruction(Opcode.LOAD_REG_IMM8, 2, immediate=0xFF),
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[2] == 0  # branch skipped the write


def test_beq_not_taken():
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=5),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=6),
        assemble_instruction(Opcode(0x0D), 0, 1),
        assemble_instruction(Opcode(0x17), immediate=to_signed_imm8(1)),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 2, immediate=0xFF),
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[2] == 0xFF


def test_jmp_register_absolute():
    # Target instruction is at byte 0x08 (instruction 4 — the WFI).
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0x00),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 2, immediate=0x08),
        assemble_instruction(Opcode(0x14), 1, 2),   # JMP R1 R2
        assemble_instruction(Opcode.LOAD_REG_IMM8, 3, immediate=0xFF),  # skipped
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[3] == 0


def test_call_and_ret():
    # Byte layout:
    #   0x00 LD R1 0x00          ; high byte
    #   0x02 LD R2 0x0A          ; low byte (subroutine)
    #   0x04 CALL R1 R2
    #   0x06 LD R5 0xCC          ; after-return marker
    #   0x08 WFI
    #   0x0A LD R4 0xAB          ; subroutine
    #   0x0C RET
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0x00),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 2, immediate=0x0A),
        assemble_instruction(Opcode(0x15), 1, 2),   # CALL
        assemble_instruction(Opcode.LOAD_REG_IMM8, 5, immediate=0xCC),
        assemble_instruction(Opcode(0x1D)),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 4, immediate=0xAB),
        assemble_instruction(Opcode(0x16)),          # RET
    ])
    assert cpu.registers[4] == 0xAB
    assert cpu.registers[5] == 0xCC
    assert cpu.sp == 0x0000  # balanced


def test_push_pop():
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 0, immediate=0x11),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0x22),
        assemble_instruction(Opcode(0x1B), 0),      # PUSH R0
        assemble_instruction(Opcode(0x1B), 1),      # PUSH R1
        assemble_instruction(Opcode(0x1C), 2),      # POP R2
        assemble_instruction(Opcode(0x1C), 3),      # POP R3
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.registers[2] == 0x22
    assert cpu.registers[3] == 0x11


# --- absolute-address memory op --------------------------------------


def test_mem_absolute_load_store():
    # Write 0xAB to mem[0x1234] via ST #[R2 R3] R1, then read back into R4.
    cpu = run_words([
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0xAB),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 2, immediate=0x12),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 3, immediate=0x34),
        assemble_instruction(Opcode.STORE_MEM_ABSOLUTE_REG, 2, 3, 1),
        assemble_instruction(Opcode.LOAD_REG_MEM_ABSOLUTE, 4, 2, 3),
        assemble_instruction(Opcode(0x1D)),
    ])
    assert cpu.memory[0x1234] == 0xAB
    assert cpu.registers[4] == 0xAB


# --- IO devices -------------------------------------------------------


class MemoryDevice(IODevice):
    def __init__(self, read_values=None):
        super().__init__()
        self.read_queue = list(read_values or [])
        self.writes: list[int] = []

    def read(self) -> int:
        return self.read_queue.pop(0) if self.read_queue else 0

    def write(self, value: int) -> None:
        self.writes.append(value)


def test_io_read_write():
    dev_in = MemoryDevice(read_values=[0x5A])
    dev_out = MemoryDevice()
    cpu = run_source(
        """
        IN R0 DEV1
        OUT DEV2 R0
        WFI
        """,
        io={1: dev_in, 2: dev_out},
    )
    assert dev_out.writes == [0x5A]
    assert cpu.halted


# --- interrupts -------------------------------------------------------


def test_wfi_wakes_on_interrupt_and_handler_runs():
    # 0x0000 is both reset vector AND interrupt vector, so the code there
    # must distinguish the two paths by inspecting $PENDING_INTERRUPTS.
    # On interrupt entry the CPU masks IF; the handler re-enables it before
    # returning, so a later trigger will be serviced again.
    #
    # instr  byte   code                                 notes
    #    0   0x00   LD R6 $PENDING_INTERRUPTS            ; read pending mask
    #    1   0x02   LD R2 0                              ; zero constant for CMP
    #    2   0x04   CMP R6 R2                            ; ZF=1 → no pending → reset
    #    3   0x06   BEQ +6                               ; on reset, skip handler
    #    4   0x08   ADD R0 R7                            ; handler: R0 += R7 (R7=1)
    #    5   0x0A   LD R6 0
    #    6   0x0C   ST $PENDING_INTERRUPTS R6            ; clear pending bits
    #    7   0x0E   LD R6 0x10                           ; IF bit
    #    8   0x10   ST $FLAGS R6                         ; re-enable interrupts
    #    9   0x12   JMP R4 R5                            ; return to main resume point
    #   10   0x14   LD R7 1                              ; main entry (BEQ target)
    #   11   0x16   LD R4 0x00                           ; resume-addr high
    #   12   0x18   LD R5 0x1E                           ; resume-addr low (instr 15)
    #   13   0x1A   LD R1 0x10                           ; IF bit
    #   14   0x1C   ST $FLAGS R1                         ; enable interrupts
    #   15   0x1E   WFI                                  ; resume point
    #   16   0x20   WFI                                  ; fallback
    words = [
        assemble_instruction(Opcode.LOAD_REG_SPECIAL, 6, 3),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 2, immediate=0),
        assemble_instruction(Opcode.CMP, 6, 2),
        assemble_instruction(Opcode.BEQ, immediate=to_signed_imm8(6)),
        assemble_instruction(Opcode.ADD, 0, 7),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 6, immediate=0),
        assemble_instruction(Opcode.STORE_SPECIAL_REG, 3, 6),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 6, immediate=0x10),
        assemble_instruction(Opcode.STORE_SPECIAL_REG, 2, 6),
        assemble_instruction(Opcode.JMP_REG, 4, 5),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 7, immediate=1),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 4, immediate=0x00),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 5, immediate=0x1E),
        assemble_instruction(Opcode.LOAD_REG_IMM8, 1, immediate=0x10),
        assemble_instruction(Opcode.STORE_SPECIAL_REG, 2, 1),
        assemble_instruction(Opcode.WFI),
        assemble_instruction(Opcode.WFI),
    ]
    cpu = SaplingCpuEmu()
    cpu.load_program(words_to_bytes(words))
    cpu.run(max_steps=200)
    assert cpu.halted
    assert cpu.registers[0] == 0

    cpu.trigger_interrupt(3)
    cpu.run(max_steps=200)
    assert cpu.registers[0] == 1
    assert cpu.pending_interrupts == 0
    assert cpu.halted


def test_trigger_interrupt_sets_pending_bit_even_when_if_clear():
    cpu = SaplingCpuEmu()
    cpu.load_program(assemble_source("WFI\n"))
    cpu.run(max_steps=10)
    assert cpu.halted

    cpu.trigger_interrupt(2)
    assert cpu.pending_interrupts == 0b0000_0100
    assert not cpu.halted
    assert cpu.pc == 0x0002


# --- stepping ---------------------------------------------------------


def test_step_by_step():
    cpu = SaplingCpuEmu()
    cpu.load_program(assemble_source("""
        LD R0 1
        LD R1 2
        WFI
    """))
    cpu.step()
    assert cpu.registers[0] == 1
    assert cpu.registers[1] == 0
    cpu.step()
    assert cpu.registers[1] == 2
    cpu.step()
    assert cpu.halted
