## High level design

- This is an '8-bit CPU' with a 16-bit address bus.
- Due to its 64 bit address bus, it supports a maximum of 64KB of memory.
- Program memory & data memory is shared.
- It has 8 registers, each 8 bits wide.
- The CPU supports a simple instruction set: see [Instructions](./Instructions.md) for details.
- IO is not memory mapped, but instead uses a separate (3 bit) IO address space.
- There are 8 IO devices, each of which can be read from or written 8 bits at a time via the IN and OUT instructions.
- Each IO device has an interrupt line that can be triggered by the device to signal the CPU that it needs attention. When an interrupt line is triggered, the corresponding bit in the pending interrupts register is set, and if interrupts are enabled (IF flag is set), the CPU will jump to the interrupt vector to handle the interrupt.
- The CPU has a stack pointer (SP) which is a 16 bit register that points to the top of the stack in memory. The stack grows downwards (SP is decremented when pushing, and incremented when popping).
- The CPU has a flags register which is 8 bits wide, and contains the following flags:
  - Zero flag (ZF): set if the result of an arithmetic or logical operation is zero
  - Negative flag (NF): set if the result of an arithmetic or logical operation is negative (most significant bit is 1)
  - Carry flag (CF): set if the result of an arithmetic operation is too large to fit in 8 bits (i.e. if there is a carry out of the most significant bit)
  - Overflow flag (OF): set if the result of an arithmetic operation is too large to fit in 8 bits, and the sign of the result is incorrect (i.e. if there is a signed overflow)
  - Interrupt enable flag (IF): set if interrupts are enabled, and cleared if interrupts are disabled. When an interrupt line is triggered, the CPU will ALWAYS set the corresponding bit in the pending interrupts register, but it will only handle the interrupt if the IF flag is set. This allows software to disable interrupts when it needs to perform critical sections of code that should not be interrupted.
- The CPU has a pending interrupts register which is 8 bits wide, and contains a bit for each of the 8 IO devices. When an interrupt is triggered by an IO device, the corresponding bit in the pending interrupts register is set. The CPU can then check this register to determine which interrupts are pending, and handle them accordingly.
- The CPU has 1 vector: Address 0x0000, which is both the reset & interrupt vector. When the CPU is reset, it will start executing instructions from this address. When an interrupt is triggered, the CPU will also jump to this address to handle the interrupt. The interrupt handler can then check the pending interrupts register to determine which interrupt was triggered, and handle it accordingly.
