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

import argparse
import sys


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
    if operand.startswith("$"):
        operand = operand[1:]

    # Validate hex digits
    for char in operand:
        if char not in "0123456789ABCDEF":
            raise ValueError(f"Invalid hex operand: '{operand}'")

    return operand


def parse_line(line: str) -> tuple | None:
    """
    Parse a single line into (opcode, operand) or None if blank/comment

    Returns:
        None for blank lines or comments
        ("LABEL", label_name) for labels ending with :
        (opcode, operand) tuple for instructions
    """
    # Strip whitespace
    line = line.strip()

    # Skip empty lines
    if not line:
        return None

    # Skip comments
    if line.startswith(";"):
        return None

    # Handle labels (ends with :)
    if line.endswith(":"):
        label_name = line[:-1].strip()
        if not label_name:
            raise ValueError("Empty label name")
        return ("LABEL", label_name)

    # Handle data lines and directives, but strip comments from them
    if line.startswith('"') or line.startswith("#") or line.startswith("!") or line.startswith("@"):
        # For string literals, only strip comments AFTER the closing quote
        if line.startswith('"'):
            # Find the closing quote
            closing_quote = line.find('"', 1)
            if closing_quote != -1:
                # Check for comment after the closing quote
                after_quote = line[closing_quote + 1 :]
                if ";" in after_quote:
                    line = line[: closing_quote + 1 + after_quote.index(";")].strip()
        else:
            # For other directives (@, #, !), strip any comments
            if ";" in line:
                line = line[: line.index(";")].strip()

        if not line:
            return None
        return ("DATA", line)

    # Remove inline comments
    if ";" in line:
        line = line[: line.index(";")].strip()
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
        operand = parts[1]  # Don't normalize yet, might be a label
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


def resolve_branch_offset(from_address: int, to_address: int) -> str:
    """Convert address difference to instruction count format for consistency"""
    # 6502 branch is relative to PC after the 2-byte branch instruction
    pc_after_branch = from_address + 2  # 6502 PC after branch instruction
    offset_bytes = to_address - pc_after_branch

    # Validate 6502 branch limits
    if offset_bytes > 127 or offset_bytes < -128:
        raise ValueError(f"Branch target too far: {offset_bytes} bytes")

    # Convert from 6502 offset back to instruction count format
    # Formula: 6502_offset = instruction_count * 4 + 2
    # Reverse: instruction_count = (6502_offset - 2) / 4
    if offset_bytes >= 2:
        # Forward branch - subtract 2 and divide by 4
        instruction_count = (offset_bytes - 2) // 4
        if (offset_bytes - 2) % 4 != 0:
            raise ValueError(f"Branch offset {offset_bytes} doesn't align to 4-byte instructions")
        return f"{instruction_count:02X}"
    else:
        # Backward branch or short forward - need to handle carefully
        # For backward: offset_bytes is negative, so we need two's complement
        if offset_bytes < 0:
            # Two's complement, then apply reverse formula
            positive_offset = 256 + offset_bytes  # Convert from two's complement
            instruction_count = (positive_offset - 2) // 4
            if (positive_offset - 2) % 4 != 0:
                raise ValueError(f"Branch offset {offset_bytes} doesn't align to 4-byte instructions")
            # Convert back to two's complement instruction count
            if instruction_count > 127:
                instruction_count = instruction_count - 256
            return f"{instruction_count & 0xFF:02X}"
        else:
            # offset_bytes is 0 or 1 - these are too small for our formula
            raise ValueError(f"Branch offset {offset_bytes} too small for instruction count format")


def convert_to_punch_format(source_lines: list[str]) -> list[str]:
    """Convert friendly source to punch card format with label resolution"""
    # First pass: parse all lines and collect labels with their effective addresses
    parsed_lines: list[tuple[str, str, int]] = []
    labels = {}  # label_name -> effective_address
    effective_address = 0x8000  # Track current effective address

    for line_no, line in enumerate(source_lines, 1):
        try:
            parsed = parse_line(line)
            if parsed is not None:
                opcode, operand = parsed
                if opcode == "LABEL":
                    # Record label position at current effective address
                    labels[operand] = effective_address
                elif opcode == "DATA" and operand.startswith("@"):
                    # Address directive - update effective address
                    hex_part = operand[1:]  # Remove @
                    effective_address = int(hex_part, 16)
                    parsed_lines.append((opcode, operand, line_no))
                else:
                    # Regular instruction or other directive
                    parsed_lines.append((opcode, operand, line_no))
                    # Advance effective address for instructions (not directives)
                    if opcode not in ["DATA"]:  # DATA includes !, @, #, " directives
                        effective_address += 4
        except ValueError as e:
            raise ValueError(f"Line {line_no}: {e}") from e

    # Second pass: resolve branches and format instructions
    punch_instructions = []
    branch_ops = {"BEQ ", "BNE ", "BCC ", "BCS ", "BMI ", "BPL ", "BVC ", "BVS "}
    current_address = 0x8000  # Track current address during second pass

    for opcode, operand, line_no in parsed_lines:
        try:
            if opcode == "DATA":
                # Handle data directives
                if operand.startswith("@"):
                    # Address directive - update current address
                    hex_part = operand[1:]  # Remove @
                    current_address = int(hex_part, 16)
                punch_instructions.append(operand)
            elif opcode in branch_ops and operand.startswith(":"):
                # Resolve branch to label (operand has : prefix)
                label_name = operand[1:]  # Strip : prefix
                if label_name not in labels:
                    raise ValueError(f"Undefined label: {label_name}")
                target_address = labels[label_name]
                offset = resolve_branch_offset(current_address, target_address)
                instruction = format_instruction(opcode, offset)
                punch_instructions.append(instruction)
                current_address += 4
            elif opcode in branch_ops:
                # Regular branch with hex operand
                operand = normalize_operand(operand)
                instruction = format_instruction(opcode, operand)
                punch_instructions.append(instruction)
                current_address += 4
            elif opcode.strip() in {"JMP", "JSR"} and operand.startswith(":"):
                # Resolve JMP/JSR to label (operand has : prefix)
                label_name = operand[1:]  # Strip : prefix
                if label_name not in labels:
                    raise ValueError(f"Undefined label: {label_name}")
                # Convert label address to 4-digit hex
                address = labels[label_name]
                hex_address = f"{address:04X}"
                instruction = format_instruction(opcode, hex_address)
                punch_instructions.append(instruction)
                current_address += 4
            elif opcode.strip() in {"JMP", "JSR"}:
                # Regular JMP/JSR with address operand
                operand = normalize_operand(operand)
                instruction = format_instruction(opcode, operand)
                punch_instructions.append(instruction)
                current_address += 4
            else:
                # Regular instruction - normalize operand if it's not a label reference
                if operand and not operand.startswith(":"):
                    operand = normalize_operand(operand)
                instruction = format_instruction(opcode, operand)
                punch_instructions.append(instruction)
                # Advance address for instructions (not data directives)
                if opcode not in ["DATA"]:
                    current_address += 4
        except ValueError as e:
            raise ValueError(f"Line {line_no}: {e}") from e

    return punch_instructions


def format_as_continuous(instructions: list[str]) -> str:
    """Format with newlines between instructions (simplified punch card format)"""
    return "\n".join(instructions) + "\n"


def format_as_80_column_cards(instructions: list[str]) -> list[str]:
    """Format as 80-column punch cards (one instruction per card)"""
    cards = []
    for i, instruction in enumerate(instructions):
        # Pad to 80 columns (punch cards were typically 80 columns)
        card = f"{i + 1:04d} {instruction}".ljust(80)
        cards.append(card)
    return cards


def main():
    parser = argparse.ArgumentParser(description="Convert friendly assembly to punch card format")
    parser.add_argument("input_file", help="Input assembly file")
    parser.add_argument("output_file", help="Output punch card file")
    parser.add_argument(
        "--80col",
        action="store_true",
        dest="col80",
        help="Format as 80-column cards (one instruction per line with line numbers)",
    )
    parser.add_argument("--verify", action="store_true", help="Verify by assembling both formats and comparing output")

    args = parser.parse_args()

    try:
        # Read input file
        with open(args.input_file) as f:
            source_lines = f.readlines()

        # Convert to punch format
        instructions = convert_to_punch_format(source_lines)

        if not instructions:
            print("Warning: No instructions found in input file")
            return

        # Format output
        if args.col80:
            output_lines = format_as_80_column_cards(instructions)
            output_content = "\n".join(output_lines) + "\n"
        else:
            output_content = format_as_continuous(instructions)

        # Write output
        with open(args.output_file, "w") as f:
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
                with open(args.input_file) as f:
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
