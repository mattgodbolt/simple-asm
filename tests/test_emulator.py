"""Tests for the 6502 emulator."""

import pytest

from .conftest import assemble_bytes, load_binary


class TestCPU6502:
    """Test the 6502 CPU emulator."""

    def test_initialization(self, cpu):
        """Test CPU initializes correctly."""
        assert cpu.a == 0
        assert cpu.x == 0
        assert cpu.y == 0
        assert cpu.sp == 0xFF
        assert cpu.pc == 0
        assert not cpu.carry
        assert not cpu.zero
        assert not cpu.negative

    def test_opcode_coverage(self, cpu):
        """Test that all opcodes in dispatch table have disassembly entries."""
        missing_disasm = []

        for opcode in cpu.opcodes:
            # Set up test memory with operands
            test_program = assemble_bytes(opcode, 0x42, 0x43)
            load_binary(cpu, test_program, 0x1000)

            disasm = cpu.disassemble_opcode(0x1000)
            if disasm.startswith("???"):
                missing_disasm.append(opcode)

        if missing_disasm:
            pytest.fail(f"Missing disassembly for opcodes: {[f'${op:02X}' for op in missing_disasm]}")

    def test_undefined_opcode_raises_exception(self, cpu):
        """Test that undefined opcodes raise exceptions."""
        # Use undefined opcode $FF
        test_program = assemble_bytes(0xFF)
        load_binary(cpu, test_program, 0x1000)

        with pytest.raises(Exception, match="Undefined opcode"):
            cpu.run(0x1000, max_cycles=1)

    def test_basic_load_store(self, cpu):
        """Test basic LDA/STA operations."""
        # LDA #$42, STA $80, BRK
        test_program = assemble_bytes(
            0xA9,
            0x42,  # LDA #$42
            0x85,
            0x80,  # STA $80
            0x00,  # BRK
        )
        load_binary(cpu, test_program, 0x1000)

        result = cpu.run(0x1000, max_cycles=10)

        assert result == "BRK"
        assert cpu.a == 0x42
        assert cpu.memory[0x80] == 0x42

    def test_indirect_addressing(self, cpu):
        """Test indirect addressing modes work correctly."""
        # Set up indirect pointer at $80 -> $1234
        cpu.memory[0x80] = 0x34
        cpu.memory[0x81] = 0x12
        cpu.memory[0x1234] = 0x99  # Value to load

        # LDA ($80),Y with Y=0, BRK
        test_program = assemble_bytes(
            0xA0,
            0x00,  # LDY #$00
            0xB1,
            0x80,  # LDA ($80),Y
            0x00,  # BRK
        )
        load_binary(cpu, test_program, 0x1000)

        result = cpu.run(0x1000, max_cycles=10)

        assert result == "BRK"
        assert cpu.a == 0x99
