"""Sapling CPU virtual machine.

Emulates the Sapling CPU as described in 1_design/ISA/.

Usage — library:
    cpu = SaplingCpuEmu()
    cpu.load_program(open("program.bin", "rb").read())
    cpu.attach_io_device(1, MyDevice())
    cpu.step()            # execute one instruction
    cpu.run()             # run until halted (WFI with no pending interrupts)
    cpu.trigger_interrupt(3)
    print(cpu.dump_state())

Usage — CLI:
    python vm.py program.bin --steps 100
    python vm.py program.bin --trace
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional


# Flag bits in the FLAGS register
FLAG_ZF = 1 << 0  # Zero
FLAG_NF = 1 << 1  # Negative
FLAG_CF = 1 << 2  # Carry
FLAG_OF = 1 << 3  # Overflow
FLAG_IF = 1 << 4  # Interrupt enable

# Special register indices (match SpecialReg in assembler.py)
SPECIAL_SP_HIGH = 0
SPECIAL_SP_LOW = 1
SPECIAL_FLAGS = 2
SPECIAL_PENDING_INTERRUPTS = 3

# Carry-mode selectors, encoded in segment C of ADD/SUB (match CarryMode in assembler.py).
CARRY_MODE_ZERO = 0      # carry-in forced to 0 — plain ADD/SUB
CARRY_MODE_ONE = 1       # carry-in forced to 1
CARRY_MODE_PREVIOUS = 2  # carry-in = previous value of CF — multi-byte chains

MEMORY_SIZE = 65536
INTERRUPT_VECTOR = 0x0000


class IODevice:
    """Base class for IO devices attached to the CPU.

    Subclass and override read()/write(). Call self.trigger_interrupt()
    from device code (e.g. a keyboard polling loop) to raise an IRQ.
    """

    def __init__(self) -> None:
        self.cpu: Optional["SaplingCpuEmu"] = None
        self.device_num: Optional[int] = None

    def read(self) -> int:
        return 0

    def write(self, value: int) -> None:
        pass

    def trigger_interrupt(self) -> None:
        if self.cpu is None or self.device_num is None:
            raise RuntimeError("IO device not attached to a CPU")
        self.cpu.trigger_interrupt(self.device_num)


class ConsoleDevice(IODevice):
    """Prints each byte written to it to a stream as an ASCII character.

    Attached by default at IO slot 7 when running the VM via the CLI, so
    programs can emit text with `OUT DEV7 Rn`.
    """

    def __init__(self, stream=None) -> None:
        super().__init__()
        self.stream = stream if stream is not None else sys.stdout

    def write(self, value: int) -> None:
        self.stream.write(chr(value & 0xFF))
        self.stream.flush()


CONSOLE_DEVICE_NUM = 7


class SaplingCpuEmu:
    def __init__(self) -> None:
        self.memory = bytearray(MEMORY_SIZE)
        self.registers = [0] * 8
        self.pc = 0
        self.sp = 0
        self.flags = 0
        self.pending_interrupts = 0
        self.halted = False
        self.io_devices: dict[int, IODevice] = {}
        self.instructions_executed = 0

    # --- setup ---------------------------------------------------------

    def reset(self) -> None:
        for i in range(8):
            self.registers[i] = 0
        self.pc = 0
        self.sp = 0
        self.flags = 0
        self.pending_interrupts = 0
        self.halted = False
        self.instructions_executed = 0

    def load_program(self, data: bytes | bytearray, offset: int = 0) -> None:
        if offset + len(data) > MEMORY_SIZE:
            raise ValueError("Program does not fit in memory")
        self.memory[offset:offset + len(data)] = data

    def attach_io_device(self, device_num: int, device: IODevice) -> None:
        if not 0 <= device_num <= 7:
            raise ValueError("IO device number must be 0-7")
        self.io_devices[device_num] = device
        device.cpu = self
        device.device_num = device_num

    def trigger_interrupt(self, device_num: int) -> None:
        if not 0 <= device_num <= 7:
            raise ValueError("IO device number must be 0-7")
        self.pending_interrupts |= 1 << device_num
        # Any pending interrupt wakes the CPU from WFI, even if IF is clear
        self.halted = False

    # --- execution -----------------------------------------------------

    def step(self) -> None:
        """Execute one instruction (or service an interrupt, if pending).

        If an interrupt is pending and IF is set, redirect PC to the interrupt
        vector, clear IF to mask further interrupts, and then execute the
        handler's first instruction in the same step. The handler is
        responsible for clearing the pending bit and re-enabling IF (typically
        just before returning via a JMP back to the resume point).
        """
        if self.pending_interrupts != 0 and (self.flags & FLAG_IF):
            self.pc = INTERRUPT_VECTOR
            self.flags &= ~FLAG_IF
            self.halted = False

        if self.halted:
            return

        instr = (self.memory[self.pc] << 8) | self.memory[(self.pc + 1) & 0xFFFF]
        self.pc = (self.pc + 2) & 0xFFFF
        self._execute(instr)
        self.instructions_executed += 1

    def run(self, max_steps: Optional[int] = None, trace: bool = False) -> int:
        """Run until the CPU is halted with no pending interrupts, or max_steps reached.

        Returns the number of steps executed.
        """
        steps = 0
        while True:
            if max_steps is not None and steps >= max_steps:
                break
            if self.halted and (self.pending_interrupts == 0 or not (self.flags & FLAG_IF)):
                break
            if trace:
                print(self.dump_state())
            self.step()
            steps += 1
        return steps

    # --- internal ------------------------------------------------------

    def _read_mem(self, addr: int) -> int:
        return self.memory[addr & 0xFFFF]

    def _write_mem(self, addr: int, value: int) -> None:
        self.memory[addr & 0xFFFF] = value & 0xFF

    def _read_special(self, idx: int) -> int:
        if idx == SPECIAL_SP_HIGH:
            return (self.sp >> 8) & 0xFF
        if idx == SPECIAL_SP_LOW:
            return self.sp & 0xFF
        if idx == SPECIAL_FLAGS:
            return self.flags & 0xFF
        if idx == SPECIAL_PENDING_INTERRUPTS:
            return self.pending_interrupts & 0xFF
        raise RuntimeError(f"Unknown special register index {idx}")

    def _write_special(self, idx: int, value: int) -> None:
        value &= 0xFF
        if idx == SPECIAL_SP_HIGH:
            self.sp = (self.sp & 0x00FF) | (value << 8)
        elif idx == SPECIAL_SP_LOW:
            self.sp = (self.sp & 0xFF00) | value
        elif idx == SPECIAL_FLAGS:
            self.flags = value
        elif idx == SPECIAL_PENDING_INTERRUPTS:
            self.pending_interrupts = value
        else:
            raise RuntimeError(f"Unknown special register index {idx}")

    def _set_flags_arith(self, a: int, b: int, result_full: int, is_sub: bool) -> None:
        """Update ZF/NF/CF/OF given the full (unbounded) arithmetic result.

        For ADD (is_sub=False): result_full = a + b [+ carry_in]. CF is set if
        result_full overflows 8 bits; OF is set when the signed result's sign
        differs from both operands'.

        For SUB (is_sub=True): result_full = a - b [- borrow_in], possibly
        negative. CF is set when a borrow occurred (result_full < 0); OF is set
        when a and b have opposite signs and the result's sign differs from a's.
        """
        result = result_full & 0xFF
        self.flags &= ~(FLAG_ZF | FLAG_NF | FLAG_CF | FLAG_OF)
        if result == 0:
            self.flags |= FLAG_ZF
        if result & 0x80:
            self.flags |= FLAG_NF
        if is_sub:
            if result_full < 0:
                self.flags |= FLAG_CF
            if ((a ^ b) & 0x80) and ((a ^ result) & 0x80):
                self.flags |= FLAG_OF
        else:
            if result_full > 0xFF:
                self.flags |= FLAG_CF
            if (~(a ^ b) & (a ^ result)) & 0x80:
                self.flags |= FLAG_OF

    def _carry_in(self, carry_mode: int) -> int:
        if carry_mode == CARRY_MODE_ZERO:
            return 0
        if carry_mode == CARRY_MODE_ONE:
            return 1
        if carry_mode == CARRY_MODE_PREVIOUS:
            return 1 if self.flags & FLAG_CF else 0
        raise RuntimeError(f"Invalid carry mode {carry_mode}")

    def _set_flags_logical(self, result: int) -> None:
        self.flags &= ~(FLAG_ZF | FLAG_NF | FLAG_CF | FLAG_OF)
        if result == 0:
            self.flags |= FLAG_ZF
        if result & 0x80:
            self.flags |= FLAG_NF

    def _branch_rel(self, simm8: int) -> None:
        # Offset is signed and in instructions, relative to PC of next instruction
        self.pc = (self.pc + simm8 * 2) & 0xFFFF

    def _execute(self, instr: int) -> None:
        opcode = (instr >> 11) & 0b11111
        seg_a = (instr >> 8) & 0b111
        seg_b = (instr >> 5) & 0b111
        seg_c = (instr >> 2) & 0b111
        imm8 = instr & 0xFF
        simm8 = imm8 - 256 if imm8 & 0x80 else imm8

        if opcode == 0x00:  # NOP
            return
        if opcode == 0x01:  # LOAD reg = imm8
            self.registers[seg_a] = imm8
            return
        if opcode == 0x02:  # LOAD reg = reg
            self.registers[seg_a] = self.registers[seg_b]
            return
        if opcode == 0x03:  # LOAD reg = memory[hi.lo]
            addr = (self.registers[seg_b] << 8) | self.registers[seg_c]
            self.registers[seg_a] = self._read_mem(addr)
            return
        if opcode == 0x04:  # STORE memory[hi.lo] = reg
            addr = (self.registers[seg_a] << 8) | self.registers[seg_b]
            self._write_mem(addr, self.registers[seg_c])
            return
        if opcode == 0x05:  # LOAD reg = memory[SP + offset]
            addr = (self.sp + simm8) & 0xFFFF
            self.registers[seg_a] = self._read_mem(addr)
            return
        if opcode == 0x06:  # STORE memory[SP + offset] = reg
            addr = (self.sp + simm8) & 0xFFFF
            self._write_mem(addr, self.registers[seg_a])
            return
        if opcode == 0x07:  # LOAD reg = special
            self.registers[seg_a] = self._read_special(seg_b)
            return
        if opcode == 0x08:  # STORE special = reg
            self._write_special(seg_a, self.registers[seg_b])
            return
        if opcode == 0x09:  # IN reg = IO device
            dev = self.io_devices.get(seg_b)
            self.registers[seg_a] = (dev.read() & 0xFF) if dev is not None else 0
            return
        if opcode == 0x0A:  # OUT IO device = reg
            dev = self.io_devices.get(seg_a)
            if dev is not None:
                dev.write(self.registers[seg_b])
            return
        if opcode == 0x0B:  # ADD — seg_c selects the carry-in source
            a = self.registers[seg_a]
            b = self.registers[seg_b]
            carry_in = self._carry_in(seg_c)
            full = a + b + carry_in
            self._set_flags_arith(a, b, full, is_sub=False)
            self.registers[seg_a] = full & 0xFF
            return
        if opcode == 0x0C:  # SUB — seg_c selects the borrow-in source
            a = self.registers[seg_a]
            b = self.registers[seg_b]
            borrow_in = self._carry_in(seg_c)
            full = a - b - borrow_in
            self._set_flags_arith(a, b, full, is_sub=True)
            self.registers[seg_a] = full & 0xFF
            return
        if opcode == 0x0D:  # CMP
            a = self.registers[seg_a]
            b = self.registers[seg_b]
            borrow_in = self._carry_in(seg_c)
            full = a - b - borrow_in
            self._set_flags_arith(a, b, full, is_sub=True)
            return
        if opcode == 0x0E:  # AND
            result = self.registers[seg_a] & self.registers[seg_b] & 0xFF
            self._set_flags_logical(result)
            self.registers[seg_a] = result
            return
        if opcode == 0x0F:  # OR
            result = (self.registers[seg_a] | self.registers[seg_b]) & 0xFF
            self._set_flags_logical(result)
            self.registers[seg_a] = result
            return
        if opcode == 0x10:  # XOR
            result = (self.registers[seg_a] ^ self.registers[seg_b]) & 0xFF
            self._set_flags_logical(result)
            self.registers[seg_a] = result
            return
        if opcode == 0x11:  # SHL
            a = self.registers[seg_a]
            result = (a << 1) & 0xFF
            self.flags &= ~(FLAG_ZF | FLAG_NF | FLAG_CF | FLAG_OF)
            if result == 0:
                self.flags |= FLAG_ZF
            if result & 0x80:
                self.flags |= FLAG_NF
            if a & 0x80:
                self.flags |= FLAG_CF
            self.registers[seg_a] = result
            return
        if opcode == 0x12:  # SHR
            a = self.registers[seg_a]
            result = (a >> 1) & 0xFF
            self.flags &= ~(FLAG_ZF | FLAG_NF | FLAG_CF | FLAG_OF)
            if result == 0:
                self.flags |= FLAG_ZF
            if a & 0x01:
                self.flags |= FLAG_CF
            self.registers[seg_a] = result
            return
        if opcode == 0x13:  # JMP signed offset
            self._branch_rel(simm8)
            return
        if opcode == 0x14:  # JMP reg hi.lo
            self.pc = ((self.registers[seg_a] << 8) | self.registers[seg_b]) & 0xFFFF
            return
        if opcode == 0x15:  # CALL reg hi.lo
            target = ((self.registers[seg_a] << 8) | self.registers[seg_b]) & 0xFFFF
            ret = self.pc  # already advanced to the instruction after CALL
            self.sp = (self.sp - 1) & 0xFFFF
            self._write_mem(self.sp, (ret >> 8) & 0xFF)
            self.sp = (self.sp - 1) & 0xFFFF
            self._write_mem(self.sp, ret & 0xFF)
            self.pc = target
            return
        if opcode == 0x16:  # RET
            lo = self._read_mem(self.sp)
            self.sp = (self.sp + 1) & 0xFFFF
            hi = self._read_mem(self.sp)
            self.sp = (self.sp + 1) & 0xFFFF
            self.pc = (hi << 8) | lo
            return
        if opcode == 0x17:  # BEQ (zero flag set)
            if self.flags & FLAG_ZF:
                self._branch_rel(simm8)
            return
        if opcode == 0x18:  # BLT (negative flag set)
            if self.flags & FLAG_NF:
                self._branch_rel(simm8)
            return
        if opcode == 0x19:  # BOV (overflow flag set)
            if self.flags & FLAG_OF:
                self._branch_rel(simm8)
            return
        if opcode == 0x1A:  # BCS (carry flag set)
            if self.flags & FLAG_CF:
                self._branch_rel(simm8)
            return
        if opcode == 0x1B:  # PUSH
            self.sp = (self.sp - 1) & 0xFFFF
            self._write_mem(self.sp, self.registers[seg_a])
            return
        if opcode == 0x1C:  # POP
            self.registers[seg_a] = self._read_mem(self.sp)
            self.sp = (self.sp + 1) & 0xFFFF
            return
        if opcode == 0x1D:  # WFI
            self.halted = True
            return

        raise RuntimeError(f"Unknown opcode 0x{opcode:02x} at instruction 0x{instr:04x}")

    # --- introspection -------------------------------------------------

    def dump_state(self) -> str:
        regs = "  ".join(f"R{i}=0x{v:02x}" for i, v in enumerate(self.registers))
        flag_str = "".join([
            "I" if self.flags & FLAG_IF else "-",
            "O" if self.flags & FLAG_OF else "-",
            "C" if self.flags & FLAG_CF else "-",
            "N" if self.flags & FLAG_NF else "-",
            "Z" if self.flags & FLAG_ZF else "-",
        ])
        next_instr = (self.memory[self.pc] << 8) | self.memory[(self.pc + 1) & 0xFFFF]
        halt = "HALT" if self.halted else "RUN "
        return (
            f"[{halt}] PC=0x{self.pc:04x} SP=0x{self.sp:04x} "
            f"FLAGS={flag_str} PEND=0b{self.pending_interrupts:08b} "
            f"NEXT=0x{next_instr:04x}\n  {regs}"
        )


def _main() -> None:
    parser = argparse.ArgumentParser(
        prog="sapling-vm",
        description="Run a Sapling CPU binary in the emulator.",
    )
    parser.add_argument("binary", help="Path to assembled .bin file")
    parser.add_argument("--steps", type=int, default=None,
                        help="Max instructions to execute (default: run to halt)")
    parser.add_argument("--trace", action="store_true",
                        help="Print CPU state before each instruction")
    parser.add_argument("--no-console", action="store_true",
                        help=f"Don't attach the default console IO device at slot {CONSOLE_DEVICE_NUM}")
    args = parser.parse_args()

    with open(args.binary, "rb") as f:
        data = f.read()

    cpu = SaplingCpuEmu()
    cpu.load_program(data)
    if not args.no_console:
        cpu.attach_io_device(CONSOLE_DEVICE_NUM, ConsoleDevice())
    steps = cpu.run(max_steps=args.steps, trace=args.trace)
    print(f"\nExecuted {steps} steps ({cpu.instructions_executed} instructions)")
    print(cpu.dump_state())


if __name__ == "__main__":
    _main()
