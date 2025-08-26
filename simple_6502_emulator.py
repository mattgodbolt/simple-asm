#!/usr/bin/env python3
"""
Minimal 6502 Emulator

A simple 6502 processor emulator that implements only the opcodes needed
by our assembler. Raises exceptions on undefined opcodes.

Usage:
    python simple_6502_emulator.py --load os.bin@0200 --load program@1000 --start 0200 --trap 1000
"""

import sys

import click


class CPU6502:
    """Minimal 6502 CPU emulator with only needed opcodes implemented"""

    def __init__(self):
        # 64KB memory
        self.memory = bytearray(65536)

        # 8-bit registers
        self.a = 0  # Accumulator
        self.x = 0  # X index register
        self.y = 0  # Y index register
        self.sp = 0xFF  # Stack pointer (starts at top of stack page)

        # 16-bit program counter
        self.pc = 0

        # Status flags (only implement the ones we need)
        self.carry = False  # C flag
        self.zero = False  # Z flag
        self.negative = False  # N flag
        self.overflow = False  # V flag (needed for proper flag handling)

        # Debug settings
        self.trace = False
        self.quiet = False
        self.cycle_count = 0

        # Opcode dispatch table
        self.opcodes = {
            # Load instructions
            0xA9: self.lda_imm,  # LDA #nn
            0xAD: self.lda_abs,  # LDA nnnn
            0xA5: self.lda_zp,  # LDA nn (zero page)
            0xBD: self.lda_abs_x,  # LDA nnnn,X
            0xB9: self.lda_abs_y,  # LDA nnnn,Y
            0xB1: self.lda_ind_y,  # LDA (nn),Y
            0xA2: self.ldx_imm,  # LDX #nn
            0xAE: self.ldx_abs,  # LDX nnnn
            0xA6: self.ldx_zp,  # LDX nn
            0xA0: self.ldy_imm,  # LDY #nn
            0xAC: self.ldy_abs,  # LDY nnnn
            0xA4: self.ldy_zp,  # LDY nn
            # Store instructions
            0x8D: self.sta_abs,  # STA nnnn
            0x85: self.sta_zp,  # STA nn
            0x9D: self.sta_abs_x,  # STA nnnn,X
            0x99: self.sta_abs_y,  # STA nnnn,Y
            0x91: self.sta_ind_y,  # STA (nn),Y
            0x8E: self.stx_abs,  # STX nnnn
            0x86: self.stx_zp,  # STX nn
            0x8C: self.sty_abs,  # STY nnnn
            0x84: self.sty_zp,  # STY nn
            # Arithmetic
            0x69: self.adc_imm,  # ADC #nn
            0xE9: self.sbc_imm,  # SBC #nn
            # Compare
            0xC9: self.cmp_imm,  # CMP #nn
            0xCD: self.cmp_abs,  # CMP nnnn
            0xC5: self.cmp_zp,  # CMP nn
            0xD1: self.cmp_ind_y,  # CMP (nn),Y
            0xD9: self.cmp_abs_y,  # CMP nnnn,Y
            0xE0: self.cpx_imm,  # CPX #nn
            0xC0: self.cpy_imm,  # CPY #nn
            # Increment/Decrement memory
            0xEE: self.inc_abs,  # INC nnnn
            0xE6: self.inc_zp,  # INC nn
            0xCE: self.dec_abs,  # DEC nnnn
            0xC6: self.dec_zp,  # DEC nn
            # Increment/Decrement registers
            0xE8: self.inx,  # INX
            0xCA: self.dex,  # DEX
            0xC8: self.iny,  # INY
            0x88: self.dey,  # DEY
            # Transfer instructions
            0xAA: self.tax,  # TAX
            0xA8: self.tay,  # TAY
            0x8A: self.txa,  # TXA
            0x98: self.tya,  # TYA
            # Jump/Branch
            0x4C: self.jmp_abs,  # JMP nnnn
            0x20: self.jsr,  # JSR nnnn
            0x60: self.rts,  # RTS
            # Branches
            0xF0: self.beq,  # BEQ
            0xD0: self.bne,  # BNE
            0xB0: self.bcs,  # BCS
            0x90: self.bcc,  # BCC
            # Stack
            0x48: self.pha,  # PHA
            0x68: self.pla,  # PLA
            # Shift/Logic
            0x0A: self.asl_a,  # ASL A
            0x05: self.ora_zp,  # ORA nn
            # Flag operations
            0x18: self.clc,  # CLC
            0x38: self.sec,  # SEC
            # Control
            0xEA: self.nop,  # NOP
            0x00: self.brk,  # BRK
        }

    def read_pc_byte(self) -> int:
        """Read byte at PC and increment PC"""
        byte = self.memory[self.pc]
        self.pc = (self.pc + 1) & 0xFFFF
        return byte

    def read_pc_word(self) -> int:
        """Read little-endian word at PC and increment PC by 2"""
        lo = self.read_pc_byte()
        hi = self.read_pc_byte()
        return (hi << 8) | lo

    def read_word(self, addr: int) -> int:
        """Read little-endian word from memory"""
        lo = self.memory[addr & 0xFFFF]
        hi = self.memory[(addr + 1) & 0xFFFF]
        return (hi << 8) | lo

    def write_word(self, addr: int, value: int):
        """Write little-endian word to memory"""
        self.memory[addr & 0xFFFF] = value & 0xFF
        self.memory[(addr + 1) & 0xFFFF] = (value >> 8) & 0xFF

    def set_nz(self, value: int):
        """Set N and Z flags based on 8-bit value"""
        value = value & 0xFF
        self.zero = value == 0
        self.negative = (value & 0x80) != 0

    def push(self, value: int):
        """Push byte onto stack"""
        self.memory[0x0100 + self.sp] = value & 0xFF
        self.sp = (self.sp - 1) & 0xFF

    def pop(self) -> int:
        """Pop byte from stack"""
        self.sp = (self.sp + 1) & 0xFF
        return self.memory[0x0100 + self.sp]

    # Load instructions
    def lda_imm(self):
        """LDA #nn - Load accumulator immediate"""
        self.a = self.read_pc_byte()
        self.set_nz(self.a)

    def lda_abs(self):
        """LDA nnnn - Load accumulator absolute"""
        addr = self.read_pc_word()
        self.a = self.memory[addr]
        self.set_nz(self.a)

    def lda_zp(self):
        """LDA nn - Load accumulator zero page"""
        addr = self.read_pc_byte()
        self.a = self.memory[addr]
        self.set_nz(self.a)

    def lda_abs_x(self):
        """LDA nnnn,X - Load accumulator absolute,X"""
        addr = (self.read_pc_word() + self.x) & 0xFFFF
        self.a = self.memory[addr]
        self.set_nz(self.a)

    def lda_abs_y(self):
        """LDA nnnn,Y - Load accumulator absolute,Y"""
        addr = (self.read_pc_word() + self.y) & 0xFFFF
        self.a = self.memory[addr]
        self.set_nz(self.a)

    def lda_ind_y(self):
        """LDA (nn),Y - Load accumulator indirect,Y"""
        zp_addr = self.read_pc_byte()
        base_addr = self.read_word(zp_addr)
        addr = (base_addr + self.y) & 0xFFFF
        self.a = self.memory[addr]
        self.set_nz(self.a)

    def ldx_imm(self):
        """LDX #nn - Load X immediate"""
        self.x = self.read_pc_byte()
        self.set_nz(self.x)

    def ldx_abs(self):
        """LDX nnnn - Load X absolute"""
        addr = self.read_pc_word()
        self.x = self.memory[addr]
        self.set_nz(self.x)

    def ldx_zp(self):
        """LDX nn - Load X zero page"""
        addr = self.read_pc_byte()
        self.x = self.memory[addr]
        self.set_nz(self.x)

    def ldy_imm(self):
        """LDY #nn - Load Y immediate"""
        self.y = self.read_pc_byte()
        self.set_nz(self.y)

    def ldy_abs(self):
        """LDY nnnn - Load Y absolute"""
        addr = self.read_pc_word()
        self.y = self.memory[addr]
        self.set_nz(self.y)

    def ldy_zp(self):
        """LDY nn - Load Y zero page"""
        addr = self.read_pc_byte()
        self.y = self.memory[addr]
        self.set_nz(self.y)

    # Store instructions
    def sta_abs(self):
        """STA nnnn - Store accumulator absolute"""
        addr = self.read_pc_word()
        self.memory[addr] = self.a

    def sta_zp(self):
        """STA nn - Store accumulator zero page"""
        addr = self.read_pc_byte()
        self.memory[addr] = self.a

    def sta_abs_x(self):
        """STA nnnn,X - Store accumulator absolute,X"""
        addr = (self.read_pc_word() + self.x) & 0xFFFF
        self.memory[addr] = self.a

    def sta_abs_y(self):
        """STA nnnn,Y - Store accumulator absolute,Y"""
        addr = (self.read_pc_word() + self.y) & 0xFFFF
        self.memory[addr] = self.a

    def sta_ind_y(self):
        """STA (nn),Y - Store accumulator indirect,Y"""
        zp_addr = self.read_pc_byte()
        base_addr = self.read_word(zp_addr)
        addr = (base_addr + self.y) & 0xFFFF
        self.memory[addr] = self.a

    def stx_abs(self):
        """STX nnnn - Store X absolute"""
        addr = self.read_pc_word()
        self.memory[addr] = self.x

    def stx_zp(self):
        """STX nn - Store X zero page"""
        addr = self.read_pc_byte()
        self.memory[addr] = self.x

    def sty_abs(self):
        """STY nnnn - Store Y absolute"""
        addr = self.read_pc_word()
        self.memory[addr] = self.y

    def sty_zp(self):
        """STY nn - Store Y zero page"""
        addr = self.read_pc_byte()
        self.memory[addr] = self.y

    # Arithmetic instructions
    def adc_imm(self):
        """ADC #nn - Add with carry immediate"""
        operand = self.read_pc_byte()
        result = self.a + operand + (1 if self.carry else 0)

        # Set flags
        self.carry = result > 255
        self.overflow = ((self.a ^ result) & (operand ^ result) & 0x80) != 0

        self.a = result & 0xFF
        self.set_nz(self.a)

    def sbc_imm(self):
        """SBC #nn - Subtract with carry immediate"""
        operand = self.read_pc_byte()
        result = self.a - operand - (0 if self.carry else 1)

        # Set flags
        self.carry = result >= 0
        self.overflow = ((self.a ^ operand) & (self.a ^ result) & 0x80) != 0

        self.a = result & 0xFF
        self.set_nz(self.a)

    # Memory increment/decrement
    def inc_abs(self):
        """INC nnnn - Increment memory absolute"""
        addr = self.read_pc_word()
        value = (self.memory[addr] + 1) & 0xFF
        self.memory[addr] = value
        self.set_nz(value)

    def inc_zp(self):
        """INC nn - Increment memory zero page"""
        addr = self.read_pc_byte()
        value = (self.memory[addr] + 1) & 0xFF
        self.memory[addr] = value
        self.set_nz(value)

    def dec_abs(self):
        """DEC nnnn - Decrement memory absolute"""
        addr = self.read_pc_word()
        value = (self.memory[addr] - 1) & 0xFF
        self.memory[addr] = value
        self.set_nz(value)

    def dec_zp(self):
        """DEC nn - Decrement memory zero page"""
        addr = self.read_pc_byte()
        value = (self.memory[addr] - 1) & 0xFF
        self.memory[addr] = value
        self.set_nz(value)

    # Register increment/decrement
    def inx(self):
        """INX - Increment X"""
        self.x = (self.x + 1) & 0xFF
        self.set_nz(self.x)

    def dex(self):
        """DEX - Decrement X"""
        self.x = (self.x - 1) & 0xFF
        self.set_nz(self.x)

    def iny(self):
        """INY - Increment Y"""
        self.y = (self.y + 1) & 0xFF
        self.set_nz(self.y)

    def dey(self):
        """DEY - Decrement Y"""
        self.y = (self.y - 1) & 0xFF
        self.set_nz(self.y)

    # Compare instructions
    def cmp_imm(self):
        """CMP #nn - Compare accumulator immediate"""
        operand = self.read_pc_byte()
        result = self.a - operand
        self.carry = self.a >= operand
        self.set_nz(result & 0xFF)

    def cmp_abs(self):
        """CMP nnnn - Compare accumulator absolute"""
        addr = self.read_pc_word()
        operand = self.memory[addr]
        result = self.a - operand
        self.carry = self.a >= operand
        self.set_nz(result & 0xFF)

    def cmp_zp(self):
        """CMP nn - Compare accumulator zero page"""
        addr = self.read_pc_byte()
        operand = self.memory[addr]
        result = self.a - operand
        self.carry = self.a >= operand
        self.set_nz(result & 0xFF)

    def cmp_ind_y(self):
        """CMP (nn),Y - Compare accumulator indirect indexed"""
        zp_addr = self.read_pc_byte()
        base_addr = self.memory[zp_addr] | (self.memory[(zp_addr + 1) & 0xFF] << 8)
        addr = (base_addr + self.y) & 0xFFFF
        operand = self.memory[addr]
        result = self.a - operand
        self.carry = self.a >= operand
        self.set_nz(result & 0xFF)

    def cmp_abs_y(self):
        """CMP nnnn,Y - Compare accumulator absolute indexed Y"""
        addr_low = self.read_pc_byte()
        addr_high = self.read_pc_byte()
        base_addr = addr_low | (addr_high << 8)
        addr = (base_addr + self.y) & 0xFFFF
        operand = self.memory[addr]
        result = self.a - operand
        self.carry = self.a >= operand
        self.set_nz(result & 0xFF)

    def cpx_imm(self):
        """CPX #nn - Compare X immediate"""
        operand = self.read_pc_byte()
        result = self.x - operand
        self.carry = self.x >= operand
        self.set_nz(result & 0xFF)

    def cpy_imm(self):
        """CPY #nn - Compare Y immediate"""
        operand = self.read_pc_byte()
        result = self.y - operand
        self.carry = self.y >= operand
        self.set_nz(result & 0xFF)

    # Transfer instructions
    def tax(self):
        """TAX - Transfer A to X"""
        self.x = self.a
        self.set_nz(self.x)

    def tay(self):
        """TAY - Transfer A to Y"""
        self.y = self.a
        self.set_nz(self.y)

    def txa(self):
        """TXA - Transfer X to A"""
        self.a = self.x
        self.set_nz(self.a)

    def tya(self):
        """TYA - Transfer Y to A"""
        self.a = self.y
        self.set_nz(self.a)

    # Jump and subroutine instructions
    def jmp_abs(self):
        """JMP nnnn - Jump absolute"""
        self.pc = self.read_pc_word()

    def jsr(self):
        """JSR nnnn - Jump to subroutine"""
        addr = self.read_pc_word()
        # Push return address - 1 onto stack (JSR pushes PC-1)
        return_addr = (self.pc - 1) & 0xFFFF
        self.push((return_addr >> 8) & 0xFF)  # High byte first
        self.push(return_addr & 0xFF)  # Low byte second
        self.pc = addr

    def rts(self):
        """RTS - Return from subroutine"""
        # Pop return address and add 1
        lo = self.pop()
        hi = self.pop()
        self.pc = ((hi << 8) | lo) + 1
        self.pc &= 0xFFFF

    # Branch instructions
    def beq(self):
        """BEQ - Branch if equal (zero flag set)"""
        offset = self.read_pc_byte()
        if self.zero:
            # Sign-extend 8-bit offset to 16-bit
            if offset & 0x80:
                offset = offset - 256
            self.pc = (self.pc + offset) & 0xFFFF

    def bne(self):
        """BNE - Branch if not equal (zero flag clear)"""
        offset = self.read_pc_byte()
        if not self.zero:
            # Sign-extend 8-bit offset to 16-bit
            if offset & 0x80:
                offset = offset - 256
            self.pc = (self.pc + offset) & 0xFFFF

    def bcs(self):
        """BCS - Branch if carry set"""
        offset = self.read_pc_byte()
        if self.carry:
            # Sign-extend 8-bit offset to 16-bit
            if offset & 0x80:
                offset = offset - 256
            self.pc = (self.pc + offset) & 0xFFFF

    def bcc(self):
        """BCC - Branch if carry clear"""
        offset = self.read_pc_byte()
        if not self.carry:
            # Sign-extend 8-bit offset to 16-bit
            if offset & 0x80:
                offset = offset - 256
            self.pc = (self.pc + offset) & 0xFFFF

    # Stack instructions
    def pha(self):
        """PHA - Push accumulator"""
        self.push(self.a)

    def pla(self):
        """PLA - Pull accumulator"""
        self.a = self.pop()
        self.set_nz(self.a)

    # Shift/Logic instructions
    def asl_a(self):
        """ASL A - Arithmetic shift left accumulator"""
        self.carry = (self.a & 0x80) != 0
        self.a = (self.a << 1) & 0xFF
        self.set_nz(self.a)

    def ora_zp(self):
        """ORA nn - OR accumulator with zero page"""
        addr = self.read_pc_byte()
        operand = self.memory[addr]
        self.a |= operand
        self.set_nz(self.a)

    # Flag instructions
    def clc(self):
        """CLC - Clear carry flag"""
        self.carry = False

    def sec(self):
        """SEC - Set carry flag"""
        self.carry = True

    # Control instructions
    def nop(self):
        """NOP - No operation"""
        pass

    def brk(self):
        """BRK - Break (stop execution)"""
        # BRK is handled specially in the execution loop
        pass

    # Execution and debugging
    def load_file(self, filename: str, address: int):
        """Load binary file into memory at specified address"""
        try:
            with open(filename, "rb") as f:
                data = f.read()
            for i, byte in enumerate(data):
                self.memory[(address + i) & 0xFFFF] = byte
            if self.trace:
                print(f"Loaded {len(data)} bytes from {filename} at ${address:04X}")
        except FileNotFoundError:
            raise Exception(f"File not found: {filename}") from None

    def load_data(self, data: bytes, address: int):
        """Load data into memory at specified address"""
        for i, byte in enumerate(data):
            self.memory[(address + i) & 0xFFFF] = byte
        if self.trace:
            print(f"Loaded {len(data)} bytes at ${address:04X}")

    def dump_memory(self, start: int, end: int, filename: str | None = None):
        """Dump memory range to file or return as bytes"""
        start = start & 0xFFFF
        end = end & 0xFFFF
        if end < start:
            end += 0x10000

        data = bytearray()
        addr = start
        while addr <= end:
            data.append(self.memory[addr & 0xFFFF])
            addr += 1

        if filename:
            with open(filename, "wb") as f:
                f.write(data)
            print(f"Dumped ${start:04X}-${end:04X} ({len(data)} bytes) to {filename}")
        else:
            return bytes(data)

    def print_memory(self, start: int, length: int = 256):
        """Print memory dump in hex format"""
        print(f"\nMemory dump ${start:04X}-${start + length - 1:04X}:")
        for offset in range(0, length, 16):
            addr = (start + offset) & 0xFFFF
            hex_bytes = []
            ascii_chars = []

            for i in range(16):
                if offset + i < length:
                    byte = self.memory[(addr + i) & 0xFFFF]
                    hex_bytes.append(f"{byte:02X}")
                    ascii_chars.append(chr(byte) if 32 <= byte <= 126 else ".")
                else:
                    hex_bytes.append("  ")
                    ascii_chars.append(" ")

            print(f"${addr:04X}: {' '.join(hex_bytes[:8])} {' '.join(hex_bytes[8:])} |{''.join(ascii_chars)}|")

    def print_registers(self):
        """Print CPU register state"""
        flags = ""
        flags += "N" if self.negative else "-"
        flags += "V" if self.overflow else "-"
        flags += "--"  # Unused flags
        flags += "Z" if self.zero else "-"
        flags += "C" if self.carry else "-"

        print(
            f"A=${self.a:02X} X=${self.x:02X} Y=${self.y:02X} SP=${self.sp:02X} PC=${self.pc:04X} [{flags}] Cycles={self.cycle_count}"
        )

    def disassemble_opcode(self, pc: int) -> str:
        """Simple disassembler for debug output"""
        opcode = self.memory[pc]

        # Complete lookup for all implemented opcodes
        disasm_table = {
            # Load instructions
            0xA9: "LDA #$%02X",
            0xAD: "LDA $%04X",
            0xA5: "LDA $%02X",
            0xBD: "LDA $%04X,X",
            0xB9: "LDA $%04X,Y",
            0xB1: "LDA ($%02X),Y",
            0xA2: "LDX #$%02X",
            0xAE: "LDX $%04X",
            0xA6: "LDX $%02X",
            0xA0: "LDY #$%02X",
            0xAC: "LDY $%04X",
            0xA4: "LDY $%02X",
            # Store instructions
            0x8D: "STA $%04X",
            0x85: "STA $%02X",
            0x9D: "STA $%04X,X",
            0x99: "STA $%04X,Y",
            0x91: "STA ($%02X),Y",
            0x8E: "STX $%04X",
            0x86: "STX $%02X",
            0x8C: "STY $%04X",
            0x84: "STY $%02X",
            # Arithmetic instructions
            0x69: "ADC #$%02X",
            0xE9: "SBC #$%02X",
            # Compare instructions
            0xC9: "CMP #$%02X",
            0xCD: "CMP $%04X",
            0xC5: "CMP $%02X",
            0xD1: "CMP ($%02X),Y",
            0xD9: "CMP $%04X,Y",
            0xE0: "CPX #$%02X",
            0xC0: "CPY #$%02X",
            # Increment/Decrement
            0xEE: "INC $%04X",
            0xE6: "INC $%02X",
            0xCE: "DEC $%04X",
            0xC6: "DEC $%02X",
            0xE8: "INX",
            0xCA: "DEX",
            0xC8: "INY",
            0x88: "DEY",
            # Transfer instructions
            0xAA: "TAX",
            0xA8: "TAY",
            0x8A: "TXA",
            0x98: "TYA",
            # Branch instructions
            0xF0: "BEQ $%02X",
            0xD0: "BNE $%02X",
            0xB0: "BCS $%02X",
            0x90: "BCC $%02X",
            # Stack instructions
            0x48: "PHA",
            0x68: "PLA",
            # Logical instructions
            0x0A: "ASL A",
            0x05: "ORA $%02X",
            # Control instructions
            0x4C: "JMP $%04X",
            0x20: "JSR $%04X",
            0x60: "RTS",
            0x18: "CLC",
            0x38: "SEC",
            0x00: "BRK",
            0xEA: "NOP",
        }

        if opcode in disasm_table:
            template = disasm_table[opcode]
            if "%04X" in template:
                operand = self.memory[pc + 1] | (self.memory[pc + 2] << 8)
                return template % operand
            elif "%02X" in template:
                operand = self.memory[pc + 1]
                return template % operand
            else:
                return template
        else:
            return f"??? ${opcode:02X}"

    def run(
        self,
        start_pc: int,
        max_cycles: int = 1000000,
        trap_addresses: list[int] | None = None,
        trace_from: int | None = None,
        trace_to: int | None = None,
        trace_pc_addrs: set[int] | None = None,
        watch_addrs: set[int] | None = None,
        watch_memory: dict[int, int] | None = None,
        breakpoint_addrs: set[int] | None = None,
        debug_break_addrs: set[int] | None = None,
    ):
        """Main execution loop"""
        self.pc = start_pc
        self.cycle_count = 0
        trap_addresses = trap_addresses or []
        trace_pc_addrs = trace_pc_addrs or set()
        watch_addrs = watch_addrs or set()
        watch_memory = watch_memory or {}
        breakpoint_addrs = breakpoint_addrs or set()
        debug_break_addrs = debug_break_addrs or set()

        if self.trace and not self.quiet:
            print(f"Starting execution at ${start_pc:04X}")
            self.print_registers()

        try:
            while self.cycle_count < max_cycles:
                # Check for breakpoints
                if self.pc in breakpoint_addrs:
                    print(f"\n*** BREAKPOINT at ${self.pc:04X} after {self.cycle_count} cycles ***")
                    self.print_registers()

                    # Dump assembler key memory locations
                    if self.pc == 0x0300:  # LOOKUP_TABLE
                        print("  Instruction buffer:", " ".join(f"${self.memory[0x0005 + i]:02X}" for i in range(4)))
                        print(f"  Table pointer: ${self.memory[0x0F]:02X}{self.memory[0x0E]:02X}")
                    elif self.pc == 0x0E00:  # WRITE_INST
                        print(f"  Opcode: ${self.memory[0x0B]:02X}")
                        print(f"  Type: ${self.memory[0x0C]:02X}")
                        print(f"  Operand: ${self.memory[0x09]:02X}")
                        print(f"  Output ptr: ${self.memory[0x03]:02X}{self.memory[0x02]:02X}")

                    input("Press Enter to continue...")

                # Check for debug breakpoints (non-interactive)
                if self.pc in debug_break_addrs:
                    print(f"\n*** DEBUG BREAK at ${self.pc:04X} after {self.cycle_count} cycles ***")
                    self.print_registers()

                    # Dump assembler key memory locations
                    if self.pc == 0x0300:  # LOOKUP_TABLE
                        print("  Instruction buffer:", " ".join(f"${self.memory[0x0005 + i]:02X}" for i in range(4)))
                        print(f"  Table pointer: ${self.memory[0x0F]:02X}{self.memory[0x0E]:02X}")
                    elif self.pc == 0x0E00:  # WRITE_INST
                        print(f"  Opcode: ${self.memory[0x0B]:02X}")
                        print(f"  Type: ${self.memory[0x0C]:02X}")
                        print(f"  Operand: ${self.memory[0x09]:02X}")
                        print(f"  Output ptr: ${self.memory[0x03]:02X}{self.memory[0x02]:02X}")

                # Check for trap addresses
                if self.pc in trap_addresses:
                    if not self.quiet:
                        print(f"\n*** TRAP at ${self.pc:04X} after {self.cycle_count} cycles ***")
                        self.print_registers()
                    return "TRAP"

                # Fetch instruction
                instruction_pc = self.pc
                opcode = self.read_pc_byte()

                # Check if we should trace this instruction
                should_trace = (
                    self.trace
                    and (trace_from is None or self.cycle_count >= trace_from)
                    and (trace_to is None or self.cycle_count <= trace_to)
                    and (not trace_pc_addrs or instruction_pc in trace_pc_addrs)
                )

                # Trace before execution
                if should_trace:
                    disasm = self.disassemble_opcode(instruction_pc)
                    print(f"${instruction_pc:04X}: {opcode:02X} {disasm}")

                # Check for BRK
                if opcode == 0x00:
                    if not self.quiet:
                        print(f"\n*** BRK at ${instruction_pc:04X} after {self.cycle_count} cycles ***")
                        self.print_registers()
                    return "BRK"

                # Dispatch to instruction handler
                if opcode not in self.opcodes:
                    raise Exception(f"Undefined opcode ${opcode:02X} at ${instruction_pc:04X}")

                self.opcodes[opcode]()
                self.cycle_count += 1

                # Check for memory watch changes
                if watch_addrs:
                    for addr in watch_addrs:
                        old_val = watch_memory.get(addr, 0)
                        new_val = self.memory[addr]
                        if old_val != new_val:
                            print(
                                f"WATCH: ${addr:04X} changed from ${old_val:02X} to ${new_val:02X} at cycle {self.cycle_count}"
                            )
                            watch_memory[addr] = new_val

                # Trace after execution
                if should_trace:
                    self.print_registers()
                    print()

        except KeyboardInterrupt:
            if not self.quiet:
                print(f"\n*** INTERRUPTED at ${self.pc:04X} after {self.cycle_count} cycles ***")
            return "INTERRUPT"
        except Exception as e:
            print(f"\n*** ERROR at ${self.pc:04X} after {self.cycle_count} cycles: {e} ***")
            self.print_registers()
            raise

        if not self.quiet:
            print(f"\n*** MAX CYCLES REACHED ({max_cycles}) ***")
        return "MAX_CYCLES"


@click.command()
@click.option("--load", "load_specs", multiple=True, help="Load file at address (format: filename@address_hex)")
@click.option("--start", type=str, default="0200", help="Starting PC address in hex (default: 0200)")
@click.option(
    "--trap", "trap_specs", multiple=True, help="Trap addresses in hex (execution stops when PC reaches these)"
)
@click.option("--trace", is_flag=True, help="Enable instruction trace output")
@click.option("--trace-from", type=int, help="Start tracing from this cycle number")
@click.option("--trace-to", type=int, help="Stop tracing at this cycle number")
@click.option("--trace-pc", "trace_pc_specs", multiple=True, help="Only trace when PC is at these addresses (hex)")
@click.option("--quiet", is_flag=True, help="Suppress non-error output except final result")
@click.option("--watch", "watch_specs", multiple=True, help="Watch memory locations for changes (hex address)")
@click.option("--breakpoint", "breakpoint_specs", multiple=True, help="Pause at specific PC values (hex)")
@click.option(
    "--debug-break", "debug_break_specs", multiple=True, help="Debug break at PC values (no pause, just dump info)"
)
@click.option("--max-cycles", type=int, default=1000000, help="Maximum cycles to execute (default: 1000000)")
@click.option("--dump", type=str, help="Dump memory range after execution (format: start:end or start:end:filename)")
@click.option("--compare", type=str, help="Compare memory dump with file (format: start:end:filename)")
def main(
    load_specs,
    start,
    trap_specs,
    trace,
    trace_from,
    trace_to,
    trace_pc_specs,
    quiet,
    watch_specs,
    breakpoint_specs,
    debug_break_specs,
    max_cycles,
    dump,
    compare,
):
    """
    Minimal 6502 emulator for testing assembler bootstrap.

    Examples:

    \b
    # Test counter program
    uv run simple_6502_emulator.py --load counter.bin@2000 --start 2000 --trace

    \b
    # Test assembler self-assembly
    uv run simple_6502_emulator.py \\
        --load assembler.bin@0200 \\
        --load source.punch@1000 \\
        --start 0200 \\
        --trap 1000 \\
        --dump 2000:2FFF:output.bin
    """

    cpu = CPU6502()
    cpu.trace = trace
    cpu.quiet = quiet

    # Parse trace PC specs
    trace_pc_addrs = set()
    for pc_spec in trace_pc_specs:
        try:
            trace_pc_addrs.add(int(pc_spec, 16))
        except ValueError:
            click.echo(f"Error: Invalid hex PC address '{pc_spec}'", err=True)
            sys.exit(1)

    # Parse watch specs
    watch_addrs = set()
    for watch_spec in watch_specs:
        try:
            watch_addrs.add(int(watch_spec, 16))
        except ValueError:
            click.echo(f"Error: Invalid hex watch address '{watch_spec}'", err=True)
            sys.exit(1)

    # Parse breakpoint specs
    breakpoint_addrs = set()
    for bp_spec in breakpoint_specs:
        try:
            breakpoint_addrs.add(int(bp_spec, 16))
        except ValueError:
            click.echo(f"Error: Invalid hex breakpoint address '{bp_spec}'", err=True)
            sys.exit(1)

    # Parse debug break specs
    debug_break_addrs = set()
    for db_spec in debug_break_specs:
        try:
            debug_break_addrs.add(int(db_spec, 16))
        except ValueError:
            click.echo(f"Error: Invalid hex debug break address '{db_spec}'", err=True)
            sys.exit(1)

    # Load files into memory
    for spec in load_specs:
        if "@" not in spec:
            click.echo("Error: Load spec must be in format 'filename@address'", err=True)
            sys.exit(1)

        filename, addr_str = spec.rsplit("@", 1)
        try:
            address = int(addr_str, 16)
        except ValueError:
            click.echo(f"Error: Invalid hex address '{addr_str}'", err=True)
            sys.exit(1)

        try:
            cpu.load_file(filename, address)
            if not quiet:
                click.echo(f"Loaded {filename} at ${address:04X}")
        except Exception as e:
            click.echo(f"Error loading {filename}: {e}", err=True)
            sys.exit(1)

    # Parse trap addresses
    trap_addresses = []
    for trap_spec in trap_specs:
        try:
            trap_addr = int(trap_spec, 16)
            trap_addresses.append(trap_addr)
            if not trace:
                click.echo(f"Set trap at ${trap_addr:04X}")
        except ValueError:
            click.echo(f"Error: Invalid hex trap address '{trap_spec}'", err=True)
            sys.exit(1)

    # Parse start address
    try:
        start_pc = int(start, 16)
    except ValueError:
        click.echo(f"Error: Invalid hex start address '{start}'", err=True)
        sys.exit(1)

    # Run the emulation
    if not quiet:
        click.echo(f"Starting execution at ${start_pc:04X}")

    # Create watch memory snapshot if watching
    watch_memory = {addr: cpu.memory[addr] for addr in watch_addrs}

    result = cpu.run(
        start_pc,
        max_cycles,
        trap_addresses,
        trace_from,
        trace_to,
        trace_pc_addrs,
        watch_addrs,
        watch_memory,
        breakpoint_addrs,
        debug_break_addrs,
    )

    # Handle memory dump
    if dump:
        parts = dump.split(":")
        if len(parts) < 2 or len(parts) > 3:
            click.echo("Error: Dump format must be 'start:end' or 'start:end:filename'", err=True)
            sys.exit(1)

        try:
            dump_start = int(parts[0], 16)
            dump_end = int(parts[1], 16)
        except ValueError:
            click.echo("Error: Invalid hex address in dump range", err=True)
            sys.exit(1)

        if len(parts) == 3:
            # Dump to file
            cpu.dump_memory(dump_start, dump_end, parts[2])
        else:
            # Print to console
            length = dump_end - dump_start + 1
            cpu.print_memory(dump_start, length)

    # Handle comparison
    if compare:
        parts = compare.split(":")
        if len(parts) != 3:
            click.echo("Error: Compare format must be 'start:end:filename'", err=True)
            sys.exit(1)

        try:
            cmp_start = int(parts[0], 16)
            cmp_end = int(parts[1], 16)
        except ValueError:
            click.echo("Error: Invalid hex address in compare range", err=True)
            sys.exit(1)

        # Get memory from emulator
        emulated = cpu.dump_memory(cmp_start, cmp_end)

        # Load comparison file
        try:
            with open(parts[2], "rb") as f:
                expected = f.read()
        except FileNotFoundError:
            click.echo(f"Error: Comparison file '{parts[2]}' not found", err=True)
            sys.exit(1)

        # Compare
        if emulated == expected:
            click.echo(f"✓ Memory ${cmp_start:04X}-${cmp_end:04X} matches {parts[2]} ({len(emulated)} bytes)")
        else:
            click.echo(f"✗ Memory ${cmp_start:04X}-${cmp_end:04X} differs from {parts[2]}")

            # Show first difference
            for i, (expected_byte, actual_byte) in enumerate(zip(expected, emulated, strict=False)):
                if expected_byte != actual_byte:
                    addr = cmp_start + i
                    click.echo(
                        f"  First difference at ${addr:04X}: expected ${expected_byte:02X}, got ${actual_byte:02X}"
                    )
                    break

            # Show length difference if any
            if len(expected) != len(emulated):
                click.echo(f"  Length mismatch: expected {len(expected)} bytes, got {len(emulated)} bytes")

            sys.exit(1)

    # Exit with appropriate code based on result
    if result == "BRK":
        sys.exit(0)
    elif result == "TRAP":
        sys.exit(0)
    elif result == "MAX_CYCLES":
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
