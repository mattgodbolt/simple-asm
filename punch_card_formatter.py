#!/usr/bin/env python3
"""
Punch Card Formatter

Converts "friendly" assembly source (with comments, newlines, flexible formatting)
into the strict format required by the 6502 assembler. This mirrors the historical
process of writing readable code on paper, then punching it onto cards in the
rigid format required by the machine.

Usage:
    python punch_card_formatter.py input.asm output.punch
    python punch_card_formatter.py --80col input.asm output.punch  # 80-column cards
"""

import sys
import argparse
from typing import List, Optional


def normalize_opcode(opcode: str) -> str:
    """Ensure opcode is exactly 4 characters, space-padded on right"""
    opcode = opcode.strip().upper()
    if len(opcode) > 4:
        raise ValueError(f"Opcode too long: '{opcode}' (max 4 chars)")
    return opcode.ljust(4)


def normalize_operand(operand: str) -> str:
    """Normalize hex operand - uppercase, proper length"""
    if not operand:
        return ""
    
    operand = operand.strip().upper()
    
    # Remove any $ prefix if present
    if operand.startswith('$'):
        operand = operand[1:]
    
    # Validate hex digits
    for char in operand:
        if char not in '0123456789ABCDEF':
            raise ValueError(f"Invalid hex operand: '{operand}'")
    
    return operand


def parse_line(line: str) -> Optional[tuple]:
    """
    Parse a single line into (opcode, operand) or None if blank/comment
    
    Returns:
        None for blank lines or comments
        (opcode, operand) tuple for instructions
    """
    # Strip whitespace
    line = line.strip()
    
    # Skip empty lines
    if not line:
        return None
    
    # Skip comments
    if line.startswith(';'):
        return None
    
    # Pass through data lines and directives unchanged
    if line.startswith('"') or line.startswith('#') or line.startswith('!') or line.startswith('@'):
        return ("DATA", line)
    
    # Remove inline comments
    if ';' in line:
        line = line[:line.index(';')].strip()
        if not line:
            return None
    
    # Split opcode and operand
    parts = line.split(None, 1)  # Split on any whitespace, max 2 parts
    
    if len(parts) == 1:
        # Just opcode, no operand
        opcode = normalize_opcode(parts[0])
        return (opcode, "")
    elif len(parts) == 2:
        # Opcode and operand
        opcode = normalize_opcode(parts[0])
        operand = normalize_operand(parts[1])
        return (opcode, operand)
    else:
        # Should never happen due to split(None, 1)
        raise ValueError(f"Cannot parse line: '{line}'")


def format_instruction(opcode: str, operand: str) -> str:
    """Format instruction for punch card output"""
    if opcode == "DATA":
        return operand  # Data lines pass through unchanged
    elif operand:
        return f"{opcode} {operand}"  # Space between opcode and operand
    else:
        return opcode


def convert_to_punch_format(source_lines: List[str]) -> List[str]:
    """Convert friendly source to punch card format"""
    punch_instructions = []
    
    for line_no, line in enumerate(source_lines, 1):
        try:
            parsed = parse_line(line)
            if parsed is not None:
                opcode, operand = parsed
                instruction = format_instruction(opcode, operand)
                punch_instructions.append(instruction)
        except ValueError as e:
            raise ValueError(f"Line {line_no}: {e}")
    
    return punch_instructions


def format_as_continuous(instructions: List[str]) -> str:
    """Format with newlines between instructions (simplified punch card format)"""
    return '\n'.join(instructions) + '\n'


def format_as_80_column_cards(instructions: List[str]) -> List[str]:
    """Format as 80-column punch cards (one instruction per card)"""
    cards = []
    for i, instruction in enumerate(instructions):
        # Pad to 80 columns (punch cards were typically 80 columns)
        card = f"{i+1:04d} {instruction}".ljust(80)
        cards.append(card)
    return cards


def main():
    parser = argparse.ArgumentParser(
        description="Convert friendly assembly to punch card format"
    )
    parser.add_argument("input_file", help="Input assembly file")
    parser.add_argument("output_file", help="Output punch card file")
    parser.add_argument(
        "--80col", 
        action="store_true",
        dest="col80",
        help="Format as 80-column cards (one instruction per line with line numbers)"
    )
    parser.add_argument(
        "--verify",
        action="store_true", 
        help="Verify by assembling both formats and comparing output"
    )
    
    args = parser.parse_args()
    
    try:
        # Read input file
        with open(args.input_file, 'r') as f:
            source_lines = f.readlines()
        
        # Convert to punch format
        instructions = convert_to_punch_format(source_lines)
        
        if not instructions:
            print("Warning: No instructions found in input file")
            return
        
        # Format output
        if args.col80:
            output_lines = format_as_80_column_cards(instructions)
            output_content = '\n'.join(output_lines) + '\n'
        else:
            output_content = format_as_continuous(instructions)
        
        # Write output
        with open(args.output_file, 'w') as f:
            f.write(output_content)
        
        print(f"Converted {len(source_lines)} source lines to {len(instructions)} instructions")
        print(f"Output written to {args.output_file}")
        
        if args.col80:
            print(f"Format: 80-column punch cards ({len(output_lines)} cards)")
        else:
            print(f"Format: Newline-separated instructions ({len(instructions)} lines)")
        
        # Verification if requested
        if args.verify:
            print("\nVerification:")
            try:
                import simple_asm
                
                # Assemble original
                assembler1 = simple_asm.SimpleAssembler()
                with open(args.input_file, 'r') as f:
                    original_source = f.read()
                output1 = assembler1.assemble_from_string(original_source)
                
                # Assemble punch card version
                assembler2 = simple_asm.SimpleAssembler()
                output2 = assembler2.assemble_from_string(output_content)
                
                if output1 == output2:
                    print("✓ Both formats produce identical machine code")
                else:
                    print("✗ Machine code differs!")
                    print(f"  Original: {len(output1)} bytes")
                    print(f"  Punch:    {len(output2)} bytes")
                    
            except ImportError:
                print("Cannot verify - simple_asm module not found")
            except Exception as e:
                print(f"Verification failed: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()