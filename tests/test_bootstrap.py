"""Tests for the bootstrap process."""

import pytest

from .conftest import find_in_opcode_table, get_opcode_table_entry, load_binary, load_source


class TestBootstrap:
    """Test the bootstrap process."""

    def test_opcode_table_format(self, assembler_binary):
        """Test that the opcode table is correctly formatted."""
        expected_entries = [
            (b"LDA#", 0xA9, 1),
            (b"STAZ", 0x85, 1),
            (b"INCZ", 0xE6, 1),
            (b"LDAZ", 0xA5, 1),
            (b"CMP#", 0xC9, 1),
            (b"STAY", 0x99, 2),
            (b"STIY", 0x91, 1),
            (b"CMPY", 0xD9, 2),
        ]

        for i, (expected_mnemonic, expected_opcode, expected_type) in enumerate(expected_entries):
            mnemonic, opcode, optype = get_opcode_table_entry(assembler_binary, i)

            assert mnemonic == expected_mnemonic, f"Entry {i}: mnemonic mismatch"
            assert opcode == expected_opcode, f"Entry {i}: opcode mismatch"
            assert optype == expected_type, f"Entry {i}: type mismatch"

    def test_opcode_lookup_logic(self, assembler_binary):
        """Test that opcodes can be found in the table."""
        # Test that we can find "BRK " in the table
        result = find_in_opcode_table(assembler_binary, b"BRK ")

        assert result is not None, "Could not find BRK in opcode table"
        index, opcode, optype = result
        assert opcode == 0x00, f"BRK should have opcode $00, got ${opcode:02X}"
        assert optype == 0, f"BRK should have type 0, got {optype}"

    def test_assembler_can_assemble_simple_instruction(self, cpu, assembler_binary):
        """Test that the assembler can successfully assemble a simple instruction."""
        load_binary(cpu, assembler_binary)
        load_source(cpu, b"BRK \nEND \n")

        # Run assembler until completion (trap at $8000 when done)
        result = cpu.run(0x0200, max_cycles=50000, trap_addresses=[0x8000])

        # Verify we reached $8000 successfully
        assert result == "TRAP", f"Should have trapped at $8000, got {result}"

        # Check that assembler successfully completed and wrote BRK instruction
        # BRK instruction should be at $8000: 00 EA EA EA (BRK + 3 NOPs)
        assert cpu.memory[0x8000] == 0x00, f"Expected BRK opcode (00) at $8000, got ${cpu.memory[0x8000]:02X}"
        assert cpu.memory[0x8001] == 0xEA, f"Expected NOP (EA) at $8001, got ${cpu.memory[0x8001]:02X}"
        assert cpu.memory[0x8002] == 0xEA, f"Expected NOP (EA) at $8002, got ${cpu.memory[0x8002]:02X}"
        assert cpu.memory[0x8003] == 0xEA, f"Expected NOP (EA) at $8003, got ${cpu.memory[0x8003]:02X}"
        assert cpu.pc == 0x8000, f"Should have jumped to assembled code at $8000, PC=${cpu.pc:04X}"

    def test_bootstrap_integration(self, cpu, assembler_binary):
        """Integration test: verify the complete bootstrap process works."""
        from pathlib import Path

        # Load the actual punch card source
        punch_file = Path("assembler_source.punch")
        if not punch_file.exists():
            pytest.skip("assembler_source.punch not found")

        load_binary(cpu, assembler_binary)
        with open(punch_file, "rb") as f:
            punch_data = f.read()
        load_source(cpu, punch_data)

        # Run the full bootstrap (may take many cycles)
        result = cpu.run(0x0200, max_cycles=300000, trap_addresses=[0x8000])

        # Verify bootstrap completed successfully
        assert result == "TRAP", f"Bootstrap should complete by trapping at $8000, got {result}"
        assert cpu.pc == 0x8000, f"Should have trapped at $8000, PC=${cpu.pc:04X}"

        # Verify some key assembled instructions exist at expected locations
        # This is a basic sanity check - we don't verify the entire output
        # since that's covered by make test-bootstrap
        assert cpu.memory[0x8200] != 0x00, "Expected assembled code to start around $8200"
