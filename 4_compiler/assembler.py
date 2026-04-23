import argparse
from enum import Enum

class AssemblerException(Exception):
    pass


def tokenize(line: str) -> list[str]:
    """Split a line into tokens.

    Whitespace and commas both separate tokens. A `#[...]` block is kept as a
    single token so the inner whitespace doesn't break up memory operands like
    `#[R4 R5]` or `#[SP + 0x21]`. A bare `[...]` block (used for the indirect
    form of JMP/CALL) is also kept as a single token.
    """
    tokens: list[str] = []
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c.isspace() or c == ",":
            i += 1
            continue
        if c == "#" and i + 1 < n and line[i + 1] == "[":
            end = line.find("]", i)
            if end == -1:
                raise AssemblerException(f"Unterminated '#[' in: {line}")
            tokens.append(line[i:end + 1])
            i = end + 1
            continue
        if c == "[":
            end = line.find("]", i)
            if end == -1:
                raise AssemblerException(f"Unterminated '[' in: {line}")
            tokens.append(line[i:end + 1])
            i = end + 1
            continue
        j = i
        while j < n and not line[j].isspace() and line[j] != ",":
            j += 1
        tokens.append(line[i:j])
        i = j
    return tokens


def asm_to_bin(input_asm_lines: list[str]) -> list[int]:
    # --- Pass 1: strip comments/whitespace, collect labels, capture instruction lines ----
    labels: dict[str, int] = {}
    instr_tokens: list[list[str]] = []

    for raw in input_asm_lines:
        # strip comments
        line = raw.split("//")[0].strip()
        if line == "":
            continue

        # label-only line: `name:`
        if line.endswith(":") and " " not in line[:-1] and "\t" not in line[:-1]:
            label_name = line[:-1].strip()
            if not label_name:
                raise AssemblerException(f"Empty label name in: {raw!r}")
            if label_name in labels:
                raise AssemblerException(f"Duplicate label {label_name}")
            labels[label_name] = len(instr_tokens)
            continue

        instr_tokens.append(tokenize(line))

    # --- Pass 2: assemble -----------------------------------------------------------------
    output_bin: list[int] = []
    for instr_idx, tokens in enumerate(instr_tokens):
        mnemonic = tokens[0].upper()
        seg_1 = tokens[1] if len(tokens) > 1 else None
        seg_2 = tokens[2] if len(tokens) > 2 else None
        seg_3 = tokens[3] if len(tokens) > 3 else None

        match mnemonic:
            case "NOP":
                output_bin.append(assemble_instruction(Opcode.NOP))

            case "LD":
                dest_reg = parse_asm_reg(seg_1)
                if seg_2 is None:
                    raise AssemblerException(f"LD requires a source operand: {tokens}")

                if seg_2.startswith("R"):
                    # LD reg = reg                                  LD R2 R2
                    src_reg = parse_asm_reg(seg_2)
                    output_bin.append(assemble_instruction(Opcode.LOAD_REG_REG, dest_reg, src_reg))

                elif seg_2.startswith("#[SP"):
                    # LD reg = memory[SP + offset]                  LD R4 #[SP + 0x21]
                    offset = parse_asm_int(seg_2.strip("#[]").split("+")[1].strip())
                    output_bin.append(assemble_instruction(
                        Opcode.LOAD_REG_MEM_SP_REL,
                        segment_a=dest_reg,
                        immediate=to_signed_imm8(offset),
                    ))

                elif seg_2.startswith("#["):
                    # LD reg = memory[reg hi . reg low]             LD R3 #[R4 R5]
                    inner = seg_2.strip("#[]").strip()
                    parts = inner.split()
                    if len(parts) != 2:
                        raise AssemblerException(f"Expected two registers inside #[...], got {seg_2}")
                    reg_hi = parse_asm_reg(parts[0])
                    reg_low = parse_asm_reg(parts[1])
                    output_bin.append(assemble_instruction(
                        Opcode.LOAD_REG_MEM_ABSOLUTE,
                        segment_a=dest_reg,
                        segment_b=reg_hi,
                        segment_c=reg_low,
                    ))

                elif seg_2.startswith("$"):
                    # LD reg = special register                     LD R5 $FLAGS
                    src_reg = SpecialReg.from_str(seg_2.lstrip("$")).to_int()
                    output_bin.append(assemble_instruction(Opcode.LOAD_REG_SPECIAL, dest_reg, src_reg))

                elif seg_2.startswith(">"):
                    # LD reg = high byte of label                   LD R1 >some_label
                    imm_value = (label_byte_addr(labels, seg_2[1:]) >> 8) & 0xFF
                    output_bin.append(assemble_instruction(Opcode.LOAD_REG_IMM8, dest_reg, immediate=imm_value))

                elif seg_2.startswith("<"):
                    # LD reg = low byte of label                    LD R2 <some_label
                    imm_value = label_byte_addr(labels, seg_2[1:]) & 0xFF
                    output_bin.append(assemble_instruction(Opcode.LOAD_REG_IMM8, dest_reg, immediate=imm_value))

                else:
                    # LD reg = imm8                                 LD R1 0x21
                    imm_value = parse_asm_int(seg_2)
                    output_bin.append(assemble_instruction(Opcode.LOAD_REG_IMM8, dest_reg, immediate=imm_value))

            case "ST":
                if seg_1 is None:
                    raise AssemblerException("ST requires a destination operand")

                if seg_1.startswith("#[SP"):
                    # ST memory[SP + offset] = reg                  ST #[SP + 0x21] R4
                    offset = parse_asm_int(seg_1.strip("#[]").split("+")[1].strip())
                    src_reg = parse_asm_reg(seg_2)
                    output_bin.append(assemble_instruction(
                        Opcode.STORE_MEM_SP_REL_REG,
                        segment_a=src_reg,
                        immediate=to_signed_imm8(offset),
                    ))

                elif seg_1.startswith("#["):
                    # ST memory[reg hi . reg low] = reg             ST #[R4 R5] R3
                    inner = seg_1.strip("#[]").strip()
                    parts = inner.split()
                    if len(parts) != 2:
                        raise AssemblerException(f"Expected two registers inside #[...], got {seg_1}")
                    reg_hi = parse_asm_reg(parts[0])
                    reg_low = parse_asm_reg(parts[1])
                    src_reg = parse_asm_reg(seg_2)
                    output_bin.append(assemble_instruction(
                        Opcode.STORE_MEM_ABSOLUTE_REG,
                        segment_a=reg_hi,
                        segment_b=reg_low,
                        segment_c=src_reg,
                    ))

                elif seg_1.startswith("$"):
                    # ST special register = reg                     ST $FLAGS R5
                    dest_reg = SpecialReg.from_str(seg_1.lstrip("$")).to_int()
                    src_reg = parse_asm_reg(seg_2)
                    output_bin.append(assemble_instruction(Opcode.STORE_SPECIAL_REG, dest_reg, src_reg))

                else:
                    raise AssemblerException(
                        f"Invalid ST instruction, expected first argument to start with #[ or $ but got {seg_1}"
                    )

            case "IN":
                output_bin.append(assemble_instruction(Opcode.IN, parse_asm_reg(seg_1), parse_asm_device(seg_2)))

            case "OUT":
                output_bin.append(assemble_instruction(Opcode.OUT, parse_asm_device(seg_1), parse_asm_reg(seg_2)))

            case "ADD":
                # ADD dest src [carry_mode]  — default carry_mode is CARRY_ZERO
                carry_mode = CarryMode.from_str(seg_3).to_int() if seg_3 is not None else CarryMode.CARRY_ZERO.to_int()
                output_bin.append(assemble_instruction(
                    Opcode.ADD, parse_asm_reg(seg_1), parse_asm_reg(seg_2), carry_mode,
                ))

            case "SUB":
                # SUB dest src [carry_mode]  — default carry_mode is CARRY_ZERO
                carry_mode = CarryMode.from_str(seg_3).to_int() if seg_3 is not None else CarryMode.CARRY_ZERO.to_int()
                output_bin.append(assemble_instruction(
                    Opcode.SUB, parse_asm_reg(seg_1), parse_asm_reg(seg_2), carry_mode,
                ))

            case "CMP":
                output_bin.append(assemble_instruction(Opcode.CMP, parse_asm_reg(seg_1), parse_asm_reg(seg_2)))

            case "AND":
                output_bin.append(assemble_instruction(Opcode.AND, parse_asm_reg(seg_1), parse_asm_reg(seg_2)))

            case "OR":
                output_bin.append(assemble_instruction(Opcode.OR, parse_asm_reg(seg_1), parse_asm_reg(seg_2)))

            case "XOR":
                output_bin.append(assemble_instruction(Opcode.XOR, parse_asm_reg(seg_1), parse_asm_reg(seg_2)))

            case "SHL":
                output_bin.append(assemble_instruction(Opcode.SHL, parse_asm_reg(seg_1)))

            case "SHR":
                output_bin.append(assemble_instruction(Opcode.SHR, parse_asm_reg(seg_1)))

            case "JMP":
                if seg_1 is None:
                    raise AssemblerException("JMP requires an operand")
                if seg_1.startswith("#"):
                    # JMP to label (relative)                       JMP #label
                    offset = relative_offset_to_label(labels, seg_1[1:], instr_idx)
                    output_bin.append(assemble_instruction(Opcode.JMP_REL, immediate=to_signed_imm8(offset)))
                elif seg_1.startswith("["):
                    # JMP reg hi . reg low                          JMP [R4 R5]
                    reg_hi, reg_lo = parse_reg_pair_bracket(seg_1)
                    output_bin.append(assemble_instruction(Opcode.JMP_REG, reg_hi, reg_lo))
                elif seg_1.startswith("R"):
                    raise AssemblerException(
                        f"JMP to a register pair requires bracket syntax, e.g. 'JMP [{seg_1} {seg_2}]'"
                    )
                else:
                    # bare signed offset                            JMP -3
                    offset = parse_asm_int(seg_1)
                    output_bin.append(assemble_instruction(Opcode.JMP_REL, immediate=to_signed_imm8(offset)))

            case "CALL":
                # CALL reg hi . reg low                             CALL [R4 R5]
                reg_hi, reg_lo = parse_reg_pair_bracket(seg_1)
                output_bin.append(assemble_instruction(Opcode.CALL, reg_hi, reg_lo))

            case "RET":
                output_bin.append(assemble_instruction(Opcode.RET))

            case "BEQ":
                output_bin.append(assemble_instruction(
                    Opcode.BEQ,
                    immediate=to_signed_imm8(resolve_branch_offset(labels, seg_1, instr_idx)),
                ))

            case "BLT":
                output_bin.append(assemble_instruction(
                    Opcode.BLT,
                    immediate=to_signed_imm8(resolve_branch_offset(labels, seg_1, instr_idx)),
                ))

            case "BOV":
                output_bin.append(assemble_instruction(
                    Opcode.BOV,
                    immediate=to_signed_imm8(resolve_branch_offset(labels, seg_1, instr_idx)),
                ))

            case "BCS":
                output_bin.append(assemble_instruction(
                    Opcode.BCS,
                    immediate=to_signed_imm8(resolve_branch_offset(labels, seg_1, instr_idx)),
                ))

            case "PUSH":
                output_bin.append(assemble_instruction(Opcode.PUSH, parse_asm_reg(seg_1)))

            case "POP":
                output_bin.append(assemble_instruction(Opcode.POP, parse_asm_reg(seg_1)))

            case "WFI":
                output_bin.append(assemble_instruction(Opcode.WFI))

            case _:
                raise AssemblerException(f"Unknown mnemonic {mnemonic}")

    return output_bin


class Opcode(Enum):
    NOP = 0x00
    LOAD_REG_IMM8 = 0x01
    LOAD_REG_REG = 0x02
    LOAD_REG_MEM_ABSOLUTE = 0x03
    STORE_MEM_ABSOLUTE_REG = 0x04
    LOAD_REG_MEM_SP_REL = 0x05
    STORE_MEM_SP_REL_REG = 0x06
    LOAD_REG_SPECIAL = 0x07
    STORE_SPECIAL_REG = 0x08
    IN = 0x09
    OUT = 0x0A
    ADD = 0x0B
    SUB = 0x0C
    CMP = 0x0D
    AND = 0x0E
    OR = 0x0F
    XOR = 0x10
    SHL = 0x11
    SHR = 0x12
    JMP_REL = 0x13
    JMP_REG = 0x14
    CALL = 0x15
    RET = 0x16
    BEQ = 0x17
    BLT = 0x18
    BOV = 0x19
    BCS = 0x1A
    PUSH = 0x1B
    POP = 0x1C
    WFI = 0x1D

    def to_int(self) -> int:
        return self.value

class CarryMode(Enum):
    """Optional segment-C modifier on ADD/SUB selecting how the carry-in is sourced."""
    CARRY_ZERO = 0       # carry-in forced to 0 (plain ADD / SUB)
    CARRY_ONE = 1        # carry-in forced to 1
    CARRY_PREVIOUS = 2   # carry-in = previous value of CF (multi-byte add/sub chains)

    @staticmethod
    def from_str(carry_mode_str: str):
        match carry_mode_str.upper():
            case "CARRY_ZERO":
                return CarryMode.CARRY_ZERO
            case "CARRY_ONE":
                return CarryMode.CARRY_ONE
            case "CARRY_PREVIOUS":
                return CarryMode.CARRY_PREVIOUS

        raise AssemblerException(f"Unknown carry mode {carry_mode_str}")

    def to_int(self) -> int:
        return self.value


class SpecialReg(Enum):
    SP_HIGH = 0
    SP_LOW = 1
    FLAGS = 2
    PENDING_INTERRUPTS = 3

    @staticmethod
    def from_str(special_reg_str: str):
        match special_reg_str.upper():
            case "SP_HIGH":
                return SpecialReg.SP_HIGH
            case "SP_LOW":
                return SpecialReg.SP_LOW
            case "FLAGS":
                return SpecialReg.FLAGS
            case "PENDING_INTERRUPTS":
                return SpecialReg.PENDING_INTERRUPTS

        raise AssemblerException(f"Unknown special register {special_reg_str}")

    def to_int(self) -> int:
        return self.value


def assemble_instruction(opcode: Opcode, segment_a: int = None, segment_b: int = None, segment_c: int = None, immediate: int = None) -> int:
    # 16 bit instruction format:
    # 15    14    13    12    11    10     9     8     7     6     5     4     3     2     1     0
    # [         Opcode         ]    [  Segment A ]     [ Segment B ]     [ Segment C ]
    # [         Opcode         ]    [  Segment A ]     [              Immediate Value            ]

    # we can only use one of our two instruction formats
    assert immediate is None or (segment_b is None and segment_c is None), "Cannot provide segment b or c when an immediate is provided"

    # check we have no overflows
    assert opcode.to_int() == opcode.to_int() & 0b11111, "Opcode does not fit in 5 bits"
    assert segment_a is None or segment_a == segment_a & 0b111, "Segment a does not fit in 3 bits"
    assert segment_b is None or segment_b == segment_b & 0b111, "Segment b does not fit in 3 bits"
    assert segment_c is None or segment_c == segment_c & 0b111, "Segment c does not fit in 3 bits"
    assert immediate is None or immediate == immediate & 0b11111111, "Immediate does not fit in 8 bits"

    instruction = 0
    instruction |= opcode.to_int() << 11

    if segment_a is not None:
        instruction |= segment_a << 8

    if segment_b is not None:
        instruction |= segment_b << 5

    if segment_c is not None:
        instruction |= segment_c << 2

    if immediate is not None:
        instruction |= immediate

    return instruction

def parse_reg_pair_bracket(bracket_str: str) -> tuple[int, int]:
    """Parse a `[Rhi Rlo]` indirect-address operand.

    Used by JMP and CALL to specify a target address spread across two registers.
    """
    if bracket_str is None or not (bracket_str.startswith("[") and bracket_str.endswith("]")):
        raise AssemblerException(f"Expected [Rhi Rlo], got {bracket_str!r}")
    parts = bracket_str.strip("[]").split()
    if len(parts) != 2:
        raise AssemblerException(f"Expected two registers inside [...], got {bracket_str}")
    return parse_asm_reg(parts[0]), parse_asm_reg(parts[1])


def parse_asm_reg(asm_reg_str: str) -> int:
    if asm_reg_str is None or not asm_reg_str.startswith("R"):
        raise AssemblerException(f"Expected register to start with R, got {asm_reg_str!r}")

    reg_number = int(asm_reg_str[1:])
    if reg_number < 0 or reg_number > 7:
        raise AssemblerException(f"Register number out of bounds (0-7): {asm_reg_str}")

    return reg_number

def parse_asm_device(asm_io_str: str) -> int:
    if asm_io_str is None or not asm_io_str.startswith("DEV"):
        raise AssemblerException(f"Expected IO device to start with DEV, got {asm_io_str!r}")

    device_number = int(asm_io_str[3:])
    if device_number < 0 or device_number > 7:
        raise AssemblerException(f"IO device number out of bounds (0-7): {asm_io_str}")

    return device_number

def parse_asm_int(asm_int_str: str) -> int:
    return int(asm_int_str, 0)

def to_signed_imm8(value: int) -> int:
    # ensure our value fits in a signed imm8
    assert -128 <= value <= 127

    # python negative 'infinite' 1's in the high bits, truncate to 8 bits
    return value & 0xFF


def label_byte_addr(labels: dict[str, int], name: str) -> int:
    if name not in labels:
        raise AssemblerException(f"Unknown label {name!r}")
    # each instruction occupies 2 bytes
    return labels[name] * 2


def relative_offset_to_label(labels: dict[str, int], name: str, current_instr_idx: int) -> int:
    """Compute the signed offset (in instructions) from the instruction after the
    current one to the target label — this matches how the VM applies the offset
    (PC has already advanced past the branch when the offset is added).
    """
    if name not in labels:
        raise AssemblerException(f"Unknown label {name!r}")
    offset = labels[name] - current_instr_idx - 1
    if offset < -128 or offset > 127:
        raise AssemblerException(
            f"Branch to {name!r} out of range: offset {offset} does not fit in signed imm8"
        )
    return offset


def resolve_branch_offset(labels: dict[str, int], operand: str, current_instr_idx: int) -> int:
    """Parse a branch operand, which can be `#label` or a bare signed integer."""
    if operand is None:
        raise AssemblerException("Branch instruction requires a target")
    if operand.startswith("#"):
        return relative_offset_to_label(labels, operand[1:], current_instr_idx)
    return parse_asm_int(operand)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Sapling Assembler',
        description='Assembles sapling ASM text into binary'
    )

    parser.add_argument('filename')
    parser.add_argument('-f', '--format', choices=['bin', 'hex', 'debug'], default='bin')
    parser.add_argument('-o', '--output', help='Output file path. If omitted, writes to stdout.')

    args = parser.parse_args()

    with open(args.filename, "r") as f:
        asm_lines = f.readlines()
    output_words = asm_to_bin(asm_lines)

    if args.format == 'hex':
        hex_output_lines: list[str] = []
        for word in output_words:
            hex_output_lines.append(f"{word:04x}")
        text_output = "\n".join(hex_output_lines)
        if args.output:
            with open(args.output, "w") as f:
                f.write(text_output)
        else:
            print(text_output)

    elif args.format == 'debug':
        debug_output_lines: list[str] = []
        for word in output_words:
            opcode = (word & 0b1111100000000000) >> 11
            opcode_name = Opcode(opcode).name

            seg_a = (word &  0b0000011100000000) >> 8
            seg_b = (word &  0b0000000011100000) >> 5
            seg_c = (word &  0b0000000000011100) >> 2
            imm8  = (word &  0b0000000011111111)

            debug_output_lines.append(f"Instruction: {word:04x}  opcode: {opcode:02x} {opcode_name:<20}  seg_a: {seg_a}  seg_b: {seg_b}  seg_c: {seg_c}  imm8: {imm8}")
        text_output = "\n".join(debug_output_lines)
        if args.output:
            with open(args.output, "w") as f:
                f.write(text_output)
        else:
            print(text_output)
    else:
        output_bytes = bytearray()
        for word in output_words:
            output_bytes.extend(word.to_bytes(2, byteorder='big'))
        if args.output:
            with open(args.output, "wb") as f:
                f.write(output_bytes)
        else:
            print(output_bytes)

