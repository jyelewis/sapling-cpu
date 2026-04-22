## Instruction format

Each instruction is 16 bits long. There are no variable length instructions.
All instructions start with a 6 bit opcode, followed by 0-3 segments, or 0-1 segment and an immediate 8 bit value.

```
15    14    13    12    11    10     9     8     7     6     5     4     3     2     1     0
[         Opcode         ]    [  Segment A ]     [ Segment B ]     [ Segment C ]
[         Opcode         ]    [  Segment A ]     [              Immediate Value            ]
```

# Instruction list

| Instruction                                  | Mnemonic | Opcode | Segment A        | Segment B       | Segment C     | Immediate Value            | Description                                                                                    |
| -------------------------------------------- | -------- | ------ | ---------------- | --------------- | ------------- | -------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| NOP                                          | NOP      | 0x00   | -                | -               | -             | -                          | No operation                                                                                   |
| LOAD reg = imm8                              | LD       | 0x01   | reg              | -               | -             | Immediate Value            | Load immediate value into register                                                             |
| LOAD reg = reg                               | LD       | 0x02   | dest reg         | src reg         | -             | -                          | Load value from one register to another                                                        |
| LOAD reg = memory[reg hi val . reg low val]  | LD       | 0x03   | dest reg         | reg hi          | reg low       | -                          | Load value from memory into register                                                           |
| STORE memory[reg hi val . reg low val] = reg | ST       | 0x04   | reg hi           | reg low         | src reg       | -                          | Store value from register into memory                                                          |
| LOAD reg = memory[SP + offset]               | LD       | 0x05   | dest reg         | -               | -             | offset                     | Load value from memory at SP + offset                                                          |
| LOAD reg = special register                  | LD       | 0x06   | dest reg         | src special reg | -             | -                          | Load value from a special register into reg (SP_HIGH, SP_LOW, FLAGS, PENDING_INTERRUPTS)       |
| STORE special register = reg                 | ST       | 0x07   | dest special reg | src reg         | -             | -                          | Store value from register into a special register (SP_HIGH, SP_LOW, FLAGS, PENDING_INTERRUPTS) |
| IN reg = IO device                           | IN       | 0x08   | dest reg         | src IO device   | -             | -                          | Load value from an IO device into a register                                                   |
| OUT IO device = reg                          | OUT      | 0x09   | dest IO device   | src reg         | -             | -                          | Store value from a register into an IO device                                                  |
| ADD dest reg = dest reg + src reg            | ADD      | 0x0A   | dest reg         | src reg         | -             | -                          | Add src reg to dest reg, and store the result in dest reg                                      |
| SUB dest reg = dest reg + src reg            | SUB      | 0x0B   | dest reg         | src reg         | -             | -                          | Subtract src reg from dest reg, and store the result in dest reg                               |
| CMP reg A - reg B                            | CMP      | 0x0C   | reg A            | reg B           | -             | -                          | Compare reg A to reg B, and set flags accordingly (equal, less than, greater than)             |
| AND dest reg = dest reg & src reg            | AND      | 0x0D   | dest reg         | src reg         | -             | -                          | Bitwise AND src reg with dest reg, and store the result in dest reg                            |
| OR dest reg = dest reg                       | OR       | 0x0E   | dest reg         | src reg         | -             | -                          | Bitwise OR src reg with dest reg, and store the result in dest reg                             |
| XOR dest reg = dest reg ^ src reg            | XOR      | 0x0F   | dest reg         | src reg         | -             | -                          | Bitwise XOR src reg with dest reg, and store the result in dest reg                            |
| SHIFT LEFT reg = reg << 1                    | SHL      | 0x10   | reg              | -               | -             | -                          | Shift reg left by 1 bit, and store the result in reg                                           |
| SHIFT RIGHT reg = reg >> 1                   | SHR      | 0x11   | reg              | -               | -             | -                          | Shift reg right by 1 bit, and store the result in reg                                          |
| JUMP offset                                  | JMP      | 0x12   | -                | -               | signed offset | Jump to PC + signed offset | Jump to address specified by adding the signed offset to the current PC (program counter)      |
| JUMP reg hi val . reg low val                | JMP      | 0x13   | reg hi           | reg low         | -             | -                          | Jump to address specified by concatenating the values in the two registers                     |
| CALL reg hi val . reg low val                | CALL     | 0x14   | reg hi           | reg low         | -             | -                          | Call subroutine at address specified by concatenating the values in the two registers          |
| RETURN                                       | RET      | 0x15   | -                | -               | -             | -                          | Return from subroutine (jump to address on top of stack, and pop the stack)                    |
| BRANCH IF zero set                           | BEQ      | 0x16   | -                | -               | -             | offset                     | Branch to PC + offset if zero flag is set                                                      |
| BRANCH IF negative set                       | BLT      | 0x17   | -                | -               | -             | offset                     | Branch to PC + offset if negative flag is set                                                  |
| BRANCH IF overflow set                       | BOV      | 0x18   | -                | -               | -             | offset                     | Branch to PC + offset if overflow flag is set                                                  |
| BRANCH IF carry set                          | BCS      | 0x19   | -                | -               | -             | offset                     | Branch to PC + offset if carry flag is set                                                     |
| PUSH reg                                     | PUSH     | 0x1A   | src reg          | -               | -             | -                          | Push value from register onto stack (decrement SP, then store value at SP)                     |
| POP reg                                      | POP      | 0x1B   | dest reg         |                 | -             | -                          | -                                                                                              | Pop value from stack into register (load value at SP into register, then increment SP) |
| Wait for interrupt                           | WFI      | 0x1C   | -                | -               | -             | -                          | Halt the CPU (stop executing instructions) until an interrupt                                  |
