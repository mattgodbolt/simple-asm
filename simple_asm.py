#!/usr/bin/env python3
"""
Minimal 6502 Assembler - Python Reference Implementation

This is a reference implementation that exactly matches the behavior
of our hand-assembled 6502 assembler. It's used to verify the design
and test the assembler's ability to assemble itself.
"""

import sys


class Memory:
    """Simulates 64K of memory"""

    def __init__(self):
        self.data = [0] * 65536

    def read_byte(self, address: int) -> int:
        return self.data[address & 0xFFFF]

    def write_byte(self, address: int, value: int) -> None:
        self.data[address & 0xFFFF] = value & 0xFF

    def read_string(self, address: int, length: int) -> str:
        """Read ASCII string from memory"""
        chars = []
        for i in range(length):
            byte = self.read_byte(address + i)
            if byte == 0:  # Null terminator
                break
            chars.append(chr(byte))
        return "".join(chars)

    def write_string(self, address: int, text: str) -> None:
        """Write ASCII string to memory"""
        for i, char in enumerate(text):
            self.write_byte(address + i, ord(char))


class SimpleAssembler:
    """Minimal 6502 Assembler matching our hand-coded version"""

    # Opcode table - exactly matches the 6502 version at $0400
    OPCODES = {
        "LDA#": (0xA9, 1),  # Load A immediate
        "LDA ": (0xAD, 2),  # Load A absolute
        "LDAZ": (0xA5, 1),  # Load A zero page
        "LDAX": (0xBD, 2),  # Load A absolute,X
        "LDAY": (0xB1, 1),  # Load A (zero page),Y
        "LDYA": (0xB9, 2),  # Load A absolute,Y
        "LDX#": (0xA2, 1),  # Load X immediate
        "LDX ": (0xAE, 2),  # Load X absolute
        "LDXZ": (0xA6, 1),  # Load X zero page
        "LDY#": (0xA0, 1),  # Load Y immediate
        "LDY ": (0xAC, 2),  # Load Y absolute
        "LDYZ": (0xA4, 1),  # Load Y zero page
        "STA ": (0x8D, 2),  # Store A absolute
        "STAZ": (0x85, 1),  # Store A zero page
        "STAX": (0x9D, 2),  # Store A absolute,X
        "STIY": (0x91, 1),  # Store A (zero page),Y
        "STAY": (0x99, 2),  # Store A absolute,Y
        "STX ": (0x8E, 2),  # Store X absolute
        "STXZ": (0x86, 1),  # Store X zero page
        "STY ": (0x8C, 2),  # Store Y absolute
        "STYZ": (0x84, 1),  # Store Y zero page
        "ADC#": (0x69, 1),  # Add with carry immediate
        "SBC#": (0xE9, 1),  # Subtract with carry immediate
        "ASL ": (0x0A, 0),  # Arithmetic shift left A
        "ORA ": (0x0D, 2),  # OR A with absolute
        "ORAZ": (0x05, 1),  # OR A with zero page
        "CMP#": (0xC9, 1),  # Compare A immediate
        "CMP ": (0xCD, 2),  # Compare A absolute
        "CMPZ": (0xC5, 1),  # Compare A zero page
        "CPIY": (0xD1, 1),  # Compare A (zero page),Y
        "CMPY": (0xD9, 2),  # Compare A absolute,Y
        "CPX#": (0xE0, 1),  # Compare X immediate
        "CPY#": (0xC0, 1),  # Compare Y immediate
        "INC ": (0xEE, 2),  # Increment absolute
        "INCZ": (0xE6, 1),  # Increment zero page
        "DEC ": (0xCE, 2),  # Decrement absolute
        "DECZ": (0xC6, 1),  # Decrement zero page
        "INX ": (0xE8, 0),  # Increment X
        "DEX ": (0xCA, 0),  # Decrement X
        "INY ": (0xC8, 0),  # Increment Y
        "DEY ": (0x88, 0),  # Decrement Y
        "TAX ": (0xAA, 0),  # Transfer A to X
        "TAY ": (0xA8, 0),  # Transfer A to Y
        "TXA ": (0x8A, 0),  # Transfer X to A
        "TYA ": (0x98, 0),  # Transfer Y to A
        "JMP ": (0x4C, 2),  # Jump absolute
        "JSR ": (0x20, 2),  # Jump to subroutine
        "RTS ": (0x60, 0),  # Return from subroutine
        "BEQ ": (0xF0, 3),  # Branch if equal
        "BNE ": (0xD0, 3),  # Branch if not equal
        "BCS ": (0xB0, 3),  # Branch if carry set
        "BCC ": (0x90, 3),  # Branch if carry clear
        "PHA ": (0x48, 0),  # Push A
        "PLA ": (0x68, 0),  # Pull A
        "CLC ": (0x18, 0),  # Clear carry
        "SEC ": (0x38, 0),  # Set carry
        "NOP ": (0xEA, 0),  # No operation
        "BRK ": (0x00, 0),  # Break
        "END ": (0xFF, 0),  # End of source (special)
    }

    def __init__(self):
        self.memory = Memory()
        self.source_ptr = 0x2000  # Source starts at $2000
        self.output_ptr = 0x8000  # Output starts at $8000
        self.effective_pc = 0x8000  # Effective address (where code thinks it is)
        self.reloc_offset = 0  # Offset to add to effective address for output
        self.labels = {}  # Label name -> effective address mapping

    def assemble_from_string(self, source: str) -> bytes:
        """Assemble source code from string"""
        # Load source into memory at $2000
        self.memory.write_string(self.source_ptr, source)
        return self.assemble()

    def assemble(self) -> bytes:
        """Main assembly loop - matches 6502 version exactly"""
        # First pass: collect labels
        self._first_pass()

        # Reset for second pass
        self.source_ptr = 0x2000
        self.effective_pc = 0x8000

        # Second pass: generate code
        output = []

        while True:
            # Skip spaces and tabs (but not newlines)
            self._skip_spaces()

            # Peek at first character
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:  # End of source
                break

            char = chr(byte)

            # Dispatch based on first character
            if char == ";":
                # Comment - skip to end of line
                self._skip_to_newline()
            elif char == "\n" or char == "\r":
                # Newline - just skip it
                self.source_ptr += 1
            elif char == '"':
                # String data
                data = self._read_string()
                output.extend(data)
                self.effective_pc += len(data)
            elif char == "#":
                # Hex data
                data = self._read_hex_data()
                output.extend(data)
                self.effective_pc += len(data)
            elif char == "!":
                # Relocation directive: !0000 sets effective_pc
                new_effective_pc = self._read_reloc_directive()
                self.effective_pc = new_effective_pc
            elif char == "@":
                # Address directive: @0400
                target_addr = self._read_address_directive()
                self._skip_to_address(target_addr, output)
            else:
                # Check if this is a label definition (ends with :)
                save_ptr = self.source_ptr
                word = self._read_word()

                if word.endswith(":"):
                    # This is a label definition
                    label_name = word[:-1]  # Remove the colon
                    self.labels[label_name] = self.effective_pc
                    self._skip_to_newline()
                    continue
                else:
                    # Not a label, restore pointer and treat as opcode
                    self.source_ptr = save_ptr

                # Must be an opcode
                opcode = self._read_opcode()
                if not opcode or not opcode.strip():
                    break

                # Skip spaces after opcode
                self._skip_spaces()

                # Look up in opcode table
                if opcode not in self.OPCODES:
                    raise ValueError(f"Unknown opcode: '{opcode}'")

                opcode_byte, operand_type = self.OPCODES[opcode]

                # Handle END marker
                if opcode == "END ":
                    break

                # Read operand based on type
                if operand_type == 0:  # No operand
                    operand_low, operand_high = 0, 0
                elif operand_type == 1:  # Single byte
                    operand_low = self._read_hex_byte()
                    operand_high = 0
                elif operand_type == 2:  # Two bytes (little-endian)
                    # Check if this is a label reference
                    operand_value = self._read_operand_value()
                    operand_low = operand_value & 0xFF
                    operand_high = (operand_value >> 8) & 0xFF
                elif operand_type == 3:  # Branch offset
                    # Check if it's a label reference
                    self._skip_spaces()
                    if self.memory.read_byte(self.source_ptr) == ord(":"):
                        self.source_ptr += 1  # Skip the ':'
                        label_name = self._read_word()
                        if label_name not in self.labels:
                            raise ValueError(f"Unknown label: {label_name}")
                        # Calculate branch offset from current PC to label
                        target = self.labels[label_name]
                        # 6502 branch is relative to PC after the 2-byte branch instruction
                        pc_after_branch = self.effective_pc + 2
                        offset_bytes = target - pc_after_branch
                        # Validate 6502 branch limits
                        if offset_bytes > 127 or offset_bytes < -128:
                            raise ValueError(f"Branch to {label_name} too far: {offset_bytes} bytes")
                        operand_low = offset_bytes & 0xFF
                        operand_high = 0
                    else:
                        # Regular hex offset (already a 6502 branch offset)
                        offset = self._read_hex_byte()
                        operand_low = offset
                        operand_high = 0
                else:
                    raise ValueError(f"Invalid operand type: {operand_type}")

                # Skip any trailing whitespace after operand
                self._skip_spaces()

                # Generate 4-byte instruction
                instruction = [opcode_byte, operand_low, operand_high, 0xEA]

                # Adjust based on operand type
                if operand_type == 0:  # No operand - pad with NOPs
                    instruction = [opcode_byte, 0xEA, 0xEA, 0xEA]
                elif operand_type == 1 or operand_type == 3:  # Single byte operand (including branches)
                    instruction = [opcode_byte, operand_low, 0xEA, 0xEA]
                # Type 2 uses the default format above (2-byte operand)

                output.extend(instruction)
                # Update effective PC (each instruction is 4 bytes)
                self.effective_pc += 4

        return bytes(output)

    def _read_opcode(self) -> str:
        """Read 4-character opcode from source"""
        chars = []
        for _ in range(4):
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:  # End of source
                return ""
            char = chr(byte)

            # Stop if we hit whitespace or end of line
            if char in " \t\n\r":
                break
            chars.append(char)
            self.source_ptr += 1

        # Pad to exactly 4 characters with spaces if needed
        while len(chars) < 4:
            chars.append(" ")

        return "".join(chars)

    def _read_word(self) -> str:
        """Read a word (until whitespace or special character)"""
        chars = []
        while True:
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:
                break
            char = chr(byte)
            if char in " \t\n\r":
                break
            chars.append(char)
            self.source_ptr += 1
        return "".join(chars)

    def _skip_to_newline(self):
        """Skip to the next newline"""
        while True:
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:
                break
            char = chr(byte)
            self.source_ptr += 1
            if char == "\n":
                break

    def _read_operand_value(self) -> int:
        """Read an operand value - either hex digits or :LABEL reference"""
        self._skip_spaces()

        # Check if it's a label reference
        if self.memory.read_byte(self.source_ptr) == ord(":"):
            self.source_ptr += 1  # Skip the ':'
            label_name = self._read_word()
            if label_name not in self.labels:
                raise ValueError(f"Unknown label: {label_name}")
            # Labels contain effective addresses
            return self.labels[label_name]
        else:
            # Regular hex value
            return self._read_hex_word()

    def _first_pass(self):
        """First pass: collect all labels"""
        save_source_ptr = self.source_ptr
        save_effective_pc = self.effective_pc

        self.source_ptr = 0x2000
        self.effective_pc = 0x8000

        while True:
            # Skip spaces and tabs (but not newlines)
            self._skip_spaces()

            # Peek at first character
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:  # End of source
                break

            char = chr(byte)

            if char == "\n":
                # Newline - just skip it
                self.source_ptr += 1
            elif char == ";":
                # Comment - skip to end of line
                self._skip_to_newline()
            elif char == '"':
                # String data - skip
                data_len = self._measure_string()
                self.effective_pc += data_len
            elif char == "#":
                # Hex data - skip
                data_len = self._measure_hex_data()
                self.effective_pc += data_len
            elif char == "!":
                # Relocation directive: !0000 sets effective_pc
                new_effective_pc = self._read_reloc_directive()
                self.effective_pc = new_effective_pc
            elif char == "@":
                # Address directive
                target_addr = self._read_address_directive()
                self._skip_to_address_in_first_pass(target_addr)
            else:
                # Check if this is a label definition (ends with :)
                save_ptr = self.source_ptr
                word = self._read_word()

                if word.endswith(":"):
                    # This is a label definition
                    label_name = word[:-1]  # Remove the colon
                    self.labels[label_name] = self.effective_pc
                    self._skip_to_newline()
                    continue
                else:
                    # Not a label, restore pointer and treat as opcode
                    self.source_ptr = save_ptr

                # Must be an opcode - skip it and advance effective PC
                opcode = self._read_opcode()
                if not opcode or not opcode.strip():
                    break

                # Skip spaces after opcode
                self._skip_spaces()

                # Look up in opcode table
                if opcode not in self.OPCODES:
                    raise ValueError(f"Unknown opcode: '{opcode}'")

                opcode_byte, operand_type = self.OPCODES[opcode]

                # Handle END marker
                if opcode == "END ":
                    break

                # Skip operand reading in first pass
                self._skip_operand(operand_type)

                # Each instruction is 4 bytes
                self.effective_pc += 4

        # Restore original state
        self.source_ptr = save_source_ptr
        self.effective_pc = save_effective_pc

    def _measure_string(self) -> int:
        """Measure length of string without processing"""
        self.source_ptr += 1  # Skip opening quote
        count = 0
        while True:
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0 or chr(byte) == '"':
                break
            count += 1
            self.source_ptr += 1
        if self.memory.read_byte(self.source_ptr) == ord('"'):
            self.source_ptr += 1  # Skip closing quote
        return count

    def _measure_hex_data(self) -> int:
        """Measure length of hex data without processing"""
        self.source_ptr += 1  # Skip '#'

        hex_chars = 0
        while True:
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:
                break
            char = chr(byte)
            if char in "0123456789ABCDEFabcdef":
                hex_chars += 1
                self.source_ptr += 1
            else:
                break

        # Each pair of hex chars = 1 byte
        return (hex_chars + 1) // 2

    def _skip_to_address_in_first_pass(self, target_addr: int):
        """Skip to address in first pass"""
        # Fill with zeros to target address
        gap_size = target_addr - self.effective_pc
        if gap_size > 0:
            self.effective_pc = target_addr

    def _skip_operand(self, operand_type: int):
        """Skip operand reading in first pass"""
        if operand_type == 0:  # No operand
            pass
        elif operand_type == 1:  # Single byte
            self._skip_hex_byte()
        elif operand_type == 2:  # Two bytes
            self._skip_operand_value()
        elif operand_type == 3:  # Branch offset
            # Skip branch operand (hex or label)
            self._skip_spaces()
            if self.memory.read_byte(self.source_ptr) == ord(":"):
                self.source_ptr += 1  # Skip ':'
                self._read_word()  # Skip label name
            else:
                self._skip_hex_byte()

    def _skip_hex_byte(self):
        """Skip hex byte reading"""
        self._skip_spaces()
        for _ in range(2):  # Skip 2 hex digits
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:
                break
            char = chr(byte)
            if char in "0123456789ABCDEFabcdef":
                self.source_ptr += 1

    def _skip_operand_value(self):
        """Skip operand value (hex or label)"""
        self._skip_spaces()
        if self.memory.read_byte(self.source_ptr) == ord(":"):
            self.source_ptr += 1  # Skip ':'
            self._read_word()  # Skip label name
        else:
            for _ in range(4):  # Skip 4 hex digits
                byte = self.memory.read_byte(self.source_ptr)
                if byte == 0:
                    break
                char = chr(byte)
                if char in "0123456789ABCDEFabcdef":
                    self.source_ptr += 1

    def _skip_spaces(self) -> None:
        """Skip spaces and tabs only (not newlines)"""
        while True:
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:  # End of source
                break
            char = chr(byte)
            if char not in " \t":
                break
            self.source_ptr += 1

    def _read_hex_byte(self) -> int:
        """Read 2 hex digits and return as byte"""
        self._skip_spaces()  # Skip any leading spaces
        hex_chars = ""
        for _ in range(2):
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:
                break
            char = chr(byte)
            if char in "0123456789ABCDEFabcdef":
                hex_chars += char.upper()
                self.source_ptr += 1
            else:
                break
        return int(hex_chars, 16) if hex_chars else 0

    def _read_hex_word(self) -> int:
        """Read 4 hex digits and return as word"""
        self._skip_spaces()  # Skip any leading spaces
        hex_chars = ""
        for _ in range(4):
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:
                break
            char = chr(byte)
            if char in "0123456789ABCDEFabcdef":
                hex_chars += char.upper()
                self.source_ptr += 1
            else:
                break
        return int(hex_chars, 16) if hex_chars else 0

    def _read_string(self) -> list:
        """Read a string literal: "text" and return as list of bytes"""
        # Skip opening quote
        self.source_ptr += 1

        data = []
        while True:
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:
                raise ValueError("Unterminated string literal")

            char = chr(byte)
            if char == '"':
                # Found closing quote
                self.source_ptr += 1
                break
            else:
                # Just add the character as-is
                data.append(ord(char))
                self.source_ptr += 1

        # Skip to end of line
        self._skip_to_newline()
        return data

    def _read_hex_data(self) -> list:
        """Read hex data: #AABBCCDD and return as list of bytes"""
        # Skip # character
        self.source_ptr += 1

        data = []
        hex_chars = ""

        while True:
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:
                break

            char = chr(byte)
            if char in "0123456789ABCDEFabcdef":
                hex_chars += char.upper()
                self.source_ptr += 1
            elif char in " \t\r\n":
                break  # End of hex data
            else:
                raise ValueError(f"Invalid hex character: '{char}'")

        # Convert hex string to bytes (must be even length)
        if len(hex_chars) % 2 != 0:
            raise ValueError(f"Hex data must have even number of digits: #{hex_chars}")

        for i in range(0, len(hex_chars), 2):
            hex_byte = hex_chars[i : i + 2]
            data.append(int(hex_byte, 16))

        # Skip to end of line
        self._skip_to_newline()
        return data

    def _read_reloc_directive(self) -> int:
        """Read relocation directive: !0000 and return as integer"""
        # Skip ! character
        self.source_ptr += 1

        hex_chars = ""
        for _ in range(4):
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:
                raise ValueError("Incomplete relocation offset")

            char = chr(byte)
            if char in "0123456789ABCDEFabcdef":
                hex_chars += char.upper()
                self.source_ptr += 1
            else:
                break

        if len(hex_chars) != 4:
            raise ValueError(f"Relocation offset must be 4 hex digits: !{hex_chars}")

        # Skip to end of line
        self._skip_to_newline()
        return int(hex_chars, 16)

    def _read_address_directive(self) -> int:
        """Read address directive: @0400 and return as integer"""
        # Skip @ character
        self.source_ptr += 1

        hex_chars = ""
        for _ in range(4):
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:
                raise ValueError("Incomplete address directive")

            char = chr(byte)
            if char in "0123456789ABCDEFabcdef":
                hex_chars += char.upper()
                self.source_ptr += 1
            else:
                break

        if len(hex_chars) != 4:
            raise ValueError(f"Address directive must be 4 hex digits: @{hex_chars}")

        # Skip to end of line
        self._skip_to_newline()
        return int(hex_chars, 16)

    def _skip_to_address(self, target_addr: int, output: list) -> None:
        """Skip effective PC forward to target address, filling gap with zeros"""
        if target_addr < self.effective_pc:
            raise ValueError(f"Cannot go backwards: @{target_addr:04X} < {self.effective_pc:04X}")

        # Fill gap with zeros
        gap_size = target_addr - self.effective_pc
        output.extend([0] * gap_size)

        # Update effective PC
        self.effective_pc = target_addr


def format_hex_dump(data: bytes, base_address: int = 0x8000) -> str:
    """Format binary data as hex dump"""
    lines = []
    for i in range(0, len(data), 16):
        addr = base_address + i
        chunk = data[i : i + 16]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{addr:04X}: {hex_part:<48} {ascii_part}")
    return "\n".join(lines)


def main():
    """Command line interface"""
    if len(sys.argv) != 2:
        print("Usage: simple-asm <source_file>")
        sys.exit(1)

    source_file = sys.argv[1]

    try:
        with open(source_file) as f:
            source = f.read()

        assembler = SimpleAssembler()
        output = assembler.assemble_from_string(source)

        print(f"Assembled {len(output)} bytes:")
        print(format_hex_dump(output))

        # Write binary output
        if source_file.endswith(".asm"):
            output_file = source_file.replace(".asm", ".bin")
        elif source_file.endswith(".punch"):
            output_file = source_file.replace(".punch", ".bin")
        else:
            output_file = source_file + ".bin"

        with open(output_file, "wb") as f:
            f.write(output)
        print(f"\nBinary written to {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
