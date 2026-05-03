## Instruction format

Each instruction is 16 bits long. There are no variable length instructions.
All instructions start with a 6 bit opcode, followed by 0-3 segments, or 0-1 segment and an immediate 8 bit value.

```
15    14    13    12    11    10     9     8     7     6     5     4     3     2     1     0
[         Opcode         ]    [  Segment A ]     [ Segment B ]     [ Segment C ]
[         Opcode         ]    [  Segment A ]     [              Immediate Value            ]
```

# Instruction list
TODO: missing carry settings for ALU ops

| Instruction                                  | Mnemonic | Opcode | Segment A        | Segment B       | Segment C | Immediate Value  | Sets Flags | Description                                                                                    |
|----------------------------------------------|----------| ------ | ---------------- | --------------- | --------- | ---------------- | ---------- | ---------------------------------------------------------------------------------------------- |
| NOP                                          | NOP      | 0x00   | -                | -               | -         | -                | No         | No operation                                                                                   |
| LOAD reg = imm8                              | LD       | 0x01   | dest reg         | -               | -         | Immediate Value  | No         | Load immediate value into register                                                             |
| LOAD reg = reg                               | LD       | 0x02   | dest reg         | src reg         | -         | -                | No         | Copy value from one register to another                                                        |
| LOAD reg = memory[reg hi val . reg low val]  | LD       | 0x03   | dest reg         | reg hi          | reg low   | -                | No         | Load value from memory into register                                                           |
| STORE memory[reg hi val . reg low val] = reg | ST       | 0x04   | reg hi           | reg low         | src reg   | -                | No         | Store value from register into memory                                                          |
| LOAD reg = memory[SP + offset]               | LD       | 0x05   | dest reg         | -               | -         | offset           | No         | Load value from memory at SP + offset                                                          |
| STORE memory[SP + offset] = reg              | ST       | 0x06   | src reg          | -               | -         | offset           | No         | Store value from register into memory at SP + offset                                           |
| LOAD reg = special register                  | LD       | 0x07   | dest reg         | src special reg | -         | -                | No         | Load value from a special register into reg (SP_HIGH, SP_LOW, FLAGS, PENDING_INTERRUPTS)       |
| STORE special register = reg                 | ST       | 0x08   | dest special reg | src reg         | -         | -                | No         | Store value from register into a special register (SP_HIGH, SP_LOW, FLAGS, PENDING_INTERRUPTS) |
| IN reg = IO device                           | IN       | 0x09   | dest reg         | src IO device   | -         | -                | No         | Load value from an IO device into a register                                                   |
| OUT IO device = reg                          | OUT      | 0x0A   | dest IO device   | src reg         | -         | -                | No         | Store value from a register into an IO device                                                  |
| ADD dest reg = dest reg + src reg            | ADD      | 0x0B   | dest reg         | src reg         | -         | -                | Yes        | Add src reg to dest reg, and store the result in dest reg                                      |
| SUB dest reg = dest reg - src reg            | SUB      | 0x0C   | dest reg         | src reg         | -         | -                | Yes        | Subtract src reg from dest reg, and store the result in dest reg                               |
| CMP reg A - reg B                            | CMP      | 0x0D   | reg A            | reg B           | -         | -                | Yes        | Subtract reg B from reg A and set flags accordingly, discarding the result                     |
| AND dest reg = dest reg & src reg            | AND      | 0x0E   | dest reg         | src reg         | -         | -                | Yes        | Bitwise AND src reg with dest reg, and store the result in dest reg                            |
| OR dest reg = dest reg OR src reg            | OR       | 0x0F   | dest reg         | src reg         | -         | -                | Yes        | Bitwise OR src reg with dest reg, and store the result in dest reg                             |
| XOR dest reg = dest reg ^ src reg            | XOR      | 0x10   | dest reg         | src reg         | -         | -                | Yes        | Bitwise XOR src reg with dest reg, and store the result in dest reg                            |
| SHIFT LEFT reg = reg << 1                    | SHL      | 0x11   | reg              | -               | -         | -                | Yes        | Shift reg left by 1 bit, and store the result in reg                                           |
| SHIFT RIGHT reg = reg >> 1                   | SHR      | 0x12   | reg              | -               | -         | -                | Yes        | Shift reg right by 1 bit, and store the result in reg                                          |
| JUMP signed offset                           | JMP      | 0x13   | -                | -               | -         | signed offset    | No         | Jump to PC + signed offset (in instructions)                                                   |
| JUMP reg hi val . reg low val                | JMP      | 0x14   | reg hi           | reg low         | -         | -                | No         | Jump to address specified by concatenating the values in the two registers                     |
| CALL reg hi val . reg low val                | CALL     | 0x15   | reg hi           | reg low         | -         | -                | No         | Push return address onto stack (high byte first), then jump to address in registers            |
| RETURN                                       | RET      | 0x16   | -                | -               | -         | -                | No         | Pop return address from stack (low byte first), then jump to it                                |
| BRANCH IF zero set                           | BEQ      | 0x17   | -                | -               | -         | signed offset    | No         | Branch to PC + signed offset (in instructions) if zero flag is set                             |
| BRANCH IF negative set                       | BLT      | 0x18   | -                | -               | -         | signed offset    | No         | Branch to PC + signed offset (in instructions) if negative flag is set                         |
| BRANCH IF overflow set                       | BOV      | 0x19   | -                | -               | -         | signed offset    | No         | Branch to PC + signed offset (in instructions) if overflow flag is set                         |
| BRANCH IF carry set                          | BCS      | 0x1A   | -                | -               | -         | signed offset    | No         | Branch to PC + signed offset (in instructions) if carry flag is set                            |
| PUSH reg                                     | PUSH     | 0x1B   | src reg          | -               | -         | -                | No         | Push value from register onto stack (decrement SP, then store value at SP)                     |
| POP reg                                      | POP      | 0x1C   | dest reg         | -               | -         | -                | No         | Pop value from stack into register (load value at SP into register, then increment SP)         |
| Wait for interrupt                           | WFI      | 0x1D   | -                | -               | -         | -                | No         | Halt the CPU (stop executing instructions) until an interrupt                                  |
