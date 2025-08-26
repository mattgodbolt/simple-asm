#!/usr/bin/env python3
"""
Test branch offset consistency between direct assembly and punch format
"""

import pytest

from punch_card_formatter import convert_to_punch_format
from simple_asm import SimpleAssembler


def test_branch_offset_consistency():
    """Test that direct assembly and punch format produce identical branch offsets"""

    # Simple test case with branch labels
    test_source = """!0000
@8200
LDA# 00
STAZ 00
MAIN_LOOP:
LDY# 00
LDAY 00
CMP# 20
BEQ  :SKIP_SECTION
CMP# 0A
BNE  :MAIN_LOOP
SKIP_SECTION:
LDA# FF
BRK
"""

    # Assemble directly
    assembler1 = SimpleAssembler()
    direct_output = assembler1.assemble_from_string(test_source)

    # Convert to punch format and assemble
    source_lines = test_source.strip().split("\n")
    punch_instructions = convert_to_punch_format(source_lines)
    punch_source = "\n".join(punch_instructions)

    assembler2 = SimpleAssembler()
    punch_output = assembler2.assemble_from_string(punch_source)

    # Compare outputs
    assert direct_output == punch_output, (
        f"Direct and punch outputs differ!\nDirect: {direct_output.hex()}\nPunch: {punch_output.hex()}"
    )


def test_punch_formatter_branch_calculation():
    """Test punch formatter branch offset calculation specifically"""
    from punch_card_formatter import resolve_branch_offset

    # Test case: BEQ from 0x8210 to 0x8218 (forward 8 bytes)
    # Expected: 6502 branch offset should be +6 (relative to PC+2)
    result = resolve_branch_offset(0x8210, 0x8218)
    assert result == "06", f"Expected '06', got '{result}'"

    # Test case: BNE from 0x8214 to 0x8208 (backward 12 bytes)
    # Expected: 6502 branch offset should be -14 (relative to PC+2), which is 0xF2 in two's complement
    result = resolve_branch_offset(0x8214, 0x8208)
    expected_offset = 0x8208 - (0x8214 + 2)  # -14
    expected_hex = f"{(256 + expected_offset) & 0xFF:02X}"
    assert result == expected_hex, f"Expected '{expected_hex}', got '{result}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
