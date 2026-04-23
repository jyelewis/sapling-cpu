import argparse
from enum import Enum

class AssemblerException(Exception):
    pass

def asm_to_bin(input_asm_lines: list[str]) -> list[int]:
    # list of 16 bit instructions
    output_bin: list[int] = []
    for asm_line in input_asm_lines:
        # strip everything after a comment marker
        asm_line = asm_line.split("//")[0]
        
        # remove whitespace
        asm_line = asm_line.strip()

        # skip empty lines
        if asm_line == "":
            continue
            
        # split into segments
        asm_line_parts = asm_line.split(" ")
        mnemonic = asm_line_parts[0].upper()
        
        seg_1 = asm_line_parts[1] if len(asm_line_parts) > 1 else None
        seg_2 = asm_line_parts[2] if len(asm_line_parts) > 2 else None
        seg_3 = asm_line_parts[3] if len(asm_line_parts) > 3 else None
        
        match mnemonic:
            case "NOP":
                output_bin.append(assemble_instruction(Opcode.NOP))

            case "LD":
                # check second param to decide which op we'll need
                dest_reg = parse_asm_reg(seg_1)
                if seg_2.startswith("R"):
                    # LOAD reg = reg                                LD R2 R2
                    src_reg = parse_asm_reg(seg_2)
                    output_bin.append(assemble_instruction(Opcode.LOAD_REG_REG, dest_reg, src_reg))
                    
                elif seg_2.startswith("#[SP"):
                    # LOAD reg = memory[SP + offset]                LD R4 #[SP + 0x21]
                    offset = parse_asm_int(seg_2.strip("#[]").split("+")[1].strip())
                    output_bin.append(assemble_instruction(Opcode.LOAD_REG_MEM_SP_REL, segment_a=dest_reg, immediate=to_signed_imm8(offset)))
                    
                elif seg_2.startswith("#["):
                    # LOAD reg = memory[reg hi val . reg low val]   LD R3 #[R4 R5]
                    reg_hi_str, reg_lo_str = seg_2.strip("#[]").split(" ")
                    reg_hi = parse_asm_reg(reg_hi_str)
                    reg_low = parse_asm_reg(reg_lo_str)
                    output_bin.append(assemble_instruction(Opcode.LOAD_REG_MEM_ABSOLUTE, segment_a=dest_reg, segment_b=reg_hi, segment_c=reg_low))
                    
                elif seg_2.startswith("$"):
                    # LOAD reg = special register                   LD R5 $FLAGS
                    src_reg = SpecialReg.from_str(seg_2.lstrip("$")).to_int()
                    output_bin.append(assemble_instruction(Opcode.LOAD_REG_SPECIAL, dest_reg, src_reg))
                    
                else:
                    # LOAD reg = imm8                               LD R1 0x21
                    imm_value = parse_asm_int(seg_2)
                    output_bin.append(assemble_instruction(Opcode.LOAD_REG_IMM8, dest_reg, immediate=imm_value))
                    
            case "ST":
                # STORE memory[reg hi val . reg low val] = reg
                # STORE memory[SP + offset] = reg
                # STORE special register = reg
                
                # check first param to decide which op we'll need
                if seg_1.startswith("#[SP"):
                    # STORE memory[SP + offset] = reg               ST #[SP + 0x21] R4
                    offset = parse_asm_int(seg_1.strip("#[]").split("+")[1].strip())
                    src_reg = parse_asm_reg(seg_2)
                    output_bin.append(assemble_instruction(Opcode.STORE_MEM_SP_REL_REG, segment_a=src_reg, immediate=to_signed_imm8(offset)))
            
                elif seg_1.startswith("#["):
                    # STORE memory[reg hi val . reg low val] = reg  ST #[R4 R5] R3
                    reg_hi_str, reg_lo_str = seg_1.strip("#[]").split(" ")
                    reg_hi = parse_asm_reg(reg_hi_str)
                    reg_low = parse_asm_reg(reg_lo_str)
                    src_reg = parse_asm_reg(seg_3)
                    output_bin.append(assemble_instruction(Opcode.STORE_MEM_ABSOLUTE_REG, segment_a=reg_hi, segment_b=reg_low, segment_c=src_reg))
            
                elif seg_1.startswith("$"):
                    # STORE special register = reg                  ST $FLAGS R5
                    dest_reg = SpecialReg.from_str(seg_1.lstrip("$")).to_int()
                    src_reg = parse_asm_reg(seg_2)
                    output_bin.append(assemble_instruction(Opcode.STORE_SPECIAL_REG, dest_reg, src_reg))
                else:
                    raise AssemblerException(f"Invalid ST instruction, expected first argument to start with #[ or $ but got {seg_1}")
                    
            case "IN":
                output_bin.append(assemble_instruction(Opcode.IN, parse_asm_reg(seg_1), parse_asm_device(seg_2)))
            case "OUT":
                output_bin.append(assemble_instruction(Opcode.OUT, parse_asm_device(seg_1), parse_asm_reg(seg_2)))
                
            
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

    WFI = 0x1D
    
    def to_int(self) -> int:
        return self.value
    
# TODO: is this overcooked?
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

def parse_asm_reg(asm_reg_str: str) -> int:
    if not asm_reg_str.startswith("R"):
        raise "Expected register to start with R"
    
    reg_number = int(asm_reg_str.strip("R"))
    if reg_number < 0 or reg_number > 8:
        raise "Register number out of bounds (0-8)"
    
    return reg_number

def parse_asm_device(asm_io_str: str) -> int:
    if not asm_io_str.startswith("DEV"):
        raise "Expected IO device to start with DEV"

    device_number = int(asm_io_str.strip("DEV"))
    if device_number < 0 or device_number > 8:
        raise "IO device number out of bounds (0-8)"

    return device_number

def parse_asm_int(asm_int_str: str) -> int:
    return int(asm_int_str, 0)

def to_signed_imm8(value: int) -> int:
    # ensure our value fits in a signed imm8
    assert -128 <= value <= 127

    # python negative 'infinite' 1's in the high bits, truncate to 8 bits
    return value & 0xFF
    
    

# if main

# Add R1 = 100 + 5
# Output R1
# result = asm_to_bin("""
# LD R2 100
# LD R3 5
# LD R1 R2
# LD R1 #[R2 R3]
# LD R1 #[SP + R3]
# // ADD R1 R3 CARRY_NONE
# // OUT 0d1 R1
# """)

# print("result")
# print(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Sapling Assembler',
        description='Assembles sapling ASM text into binary'
    )
    
    parser.add_argument('filename')
    parser.add_argument('-f', '--format', choices=['bin', 'hex', 'debug'], default='bin')
    
    args = parser.parse_args()
    
    with open(args.filename, "r") as f:
        asm_lines = f.readlines()
        output_words = asm_to_bin(asm_lines)
        
        if args.format == 'hex':
            hex_output_lines: list[str] = []
            for word in output_words:
                hex_output_lines.append(f"{word:04x}")
            print("\n".join(hex_output_lines))
        if args.format == 'debug':
            debug_output_lines: list[str] = []
            for word in output_words:
                opcode = (word & 0b1111100000000000) >> 11
                opcode_name = Opcode(opcode).name
                
                seg_a = (word &  0b0000011100000000) >> 8
                seg_b = (word &  0b0000000011100000) >> 5
                seg_c = (word &  0b0000000000011100) >> 2
                imm8  = (word &  0b0000000011111111)
                
                debug_output_lines.append(f"Instruction: {word:04x}  opcode: {opcode:02x} {opcode_name:<20}  seg_a: {seg_a}  seg_b: {seg_b}  seg_c: {seg_c}  imm8: {imm8}")
            print("\n".join(debug_output_lines))
        else:
            output_bytes = bytearray()
            for word in output_words:
                output_bytes.extend(word.to_bytes(2, byteorder='big'))
            print(output_bytes)
    
