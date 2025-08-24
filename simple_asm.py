#!/usr/bin/env python3
"""
Minimal 6502 Assembler - Python Reference Implementation

This is a reference implementation that exactly matches the behavior 
of our hand-assembled 6502 assembler. It's used to verify the design
and test the assembler's ability to assemble itself.
"""

import sys
from typing import Dict, List, Optional, Tuple


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
        return ''.join(chars)
    
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
        "STAY": (0x91, 1),  # Store A (zero page),Y
        "STYA": (0x99, 2),  # Store A absolute,Y
        
        "STX ": (0x8E, 2),  # Store X absolute
        "STXZ": (0x86, 1),  # Store X zero page
        
        "STY ": (0x8C, 2),  # Store Y absolute
        "STYZ": (0x84, 1),  # Store Y zero page
        
        "ADC#": (0x69, 1),  # Add with carry immediate
        "SBC#": (0xE9, 1),  # Subtract with carry immediate
        
        "ASL ": (0x0A, 0),  # Arithmetic shift left A
        "ORA ": (0x05, 1),  # OR A with zero page
        
        "CMP#": (0xC9, 1),  # Compare A immediate
        "CMP ": (0xCD, 2),  # Compare A absolute
        "CMPZ": (0xC5, 1),  # Compare A zero page
        "CMPY": (0xD1, 1),  # Compare A (zero page),Y
        
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
        self.source_ptr = 0x1000  # Source starts at $1000
        self.output_ptr = 0x2000  # Output starts at $2000
    
    def assemble_from_string(self, source: str) -> bytes:
        """Assemble source code from string"""
        # Load source into memory at $1000
        self.memory.write_string(self.source_ptr, source)
        return self.assemble()
    
    def assemble(self) -> bytes:
        """Main assembly loop - matches 6502 version exactly"""
        output = []
        
        while True:
            # Skip any leading whitespace
            self._skip_spaces()
            
            # Read 4-character opcode
            opcode = self._read_opcode()
            if not opcode:
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
                # Read as big-endian, store as little-endian
                value = self._read_hex_word()
                operand_low = value & 0xFF
                operand_high = (value >> 8) & 0xFF
            elif operand_type == 3:  # Branch offset
                offset = self._read_hex_byte()
                # Convert signed byte to branch offset
                if offset > 127:
                    offset = offset - 256
                operand_low = (offset * 4) & 0xFF
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
            elif operand_type == 1:  # Single byte operand
                instruction = [opcode_byte, operand_low, 0xEA, 0xEA]
            # Type 2 and 3 use the default format above
            
            output.extend(instruction)
        
        return bytes(output)
    
    def _read_opcode(self) -> str:
        """Read 4-character opcode from source"""
        while True:
            chars = []
            for _ in range(4):
                byte = self.memory.read_byte(self.source_ptr)
                if byte == 0:  # End of source
                    return ""
                char = chr(byte)
                
                # Skip comment lines - if first char is semicolon, skip to end of line
                if char == ';' and len(chars) == 0:
                    self._skip_to_newline()
                    break  # Start over with next line
                
                # Stop if we hit whitespace or end of line
                if char in ' \t\n\r':
                    break
                chars.append(char)
                self.source_ptr += 1
            
            # If we got some characters, pad and return
            if chars:
                # Pad to exactly 4 characters with spaces if needed
                while len(chars) < 4:
                    chars.append(' ')
                return ''.join(chars)
            
            # If we got no characters, skip to next non-whitespace and try again
            self._skip_spaces()
    
    def _skip_to_newline(self) -> None:
        """Skip characters until we hit a newline"""
        while True:
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:  # End of source
                break
            char = chr(byte)
            self.source_ptr += 1
            if char in '\n\r':
                break
    
    def _skip_spaces(self) -> None:
        """Skip whitespace characters"""
        while True:
            byte = self.memory.read_byte(self.source_ptr)
            if byte == 0:  # End of source
                break
            char = chr(byte)
            if char not in ' \t\n\r':
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
            if char in '0123456789ABCDEFabcdef':
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
            if char in '0123456789ABCDEFabcdef':
                hex_chars += char.upper()
                self.source_ptr += 1
            else:
                break
        return int(hex_chars, 16) if hex_chars else 0


def format_hex_dump(data: bytes, base_address: int = 0x2000) -> str:
    """Format binary data as hex dump"""
    lines = []
    for i in range(0, len(data), 16):
        addr = base_address + i
        chunk = data[i:i+16]
        hex_part = ' '.join(f"{b:02X}" for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        lines.append(f"{addr:04X}: {hex_part:<48} {ascii_part}")
    return '\n'.join(lines)


def main():
    """Command line interface"""
    if len(sys.argv) != 2:
        print("Usage: simple-asm <source_file>")
        sys.exit(1)
    
    source_file = sys.argv[1]
    
    try:
        with open(source_file, 'r') as f:
            source = f.read()
        
        assembler = SimpleAssembler()
        output = assembler.assemble_from_string(source)
        
        print(f"Assembled {len(output)} bytes:")
        print(format_hex_dump(output))
        
        # Write binary output
        if source_file.endswith('.asm'):
            output_file = source_file.replace('.asm', '.bin')
        elif source_file.endswith('.punch'):
            output_file = source_file.replace('.punch', '.bin')
        else:
            output_file = source_file + '.bin'
        
        with open(output_file, 'wb') as f:
            f.write(output)
        print(f"\nBinary written to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()