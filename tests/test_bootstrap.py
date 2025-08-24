"""Tests for the bootstrap process."""

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

    def test_assembler_reads_source(self, cpu, assembler_binary):
        """Test that the assembler correctly reads source into opcode buffer."""
        load_binary(cpu, assembler_binary)
        load_source(cpu, b"BRK \n")

        # Run assembler until opcode reading is complete (trap after opcode advance)
        # Opcode reading completes at $0238, so we trap there
        cpu.run(0x0200, max_cycles=10000, trap_addresses=[0x0238])

        # Check that assembler read "BRK " into the opcode buffer
        opcode_buffer = bytes(cpu.memory[0x05:0x09])
        assert opcode_buffer == b"BRK ", f"Opcode buffer should contain 'BRK ', got {opcode_buffer!r}"
        assert cpu.pc == 0x0238, f"Should have stopped after opcode reading, PC=${cpu.pc:04X}"

    def test_table_pointer_setup(self, cpu, assembler_binary):
        """Test that the assembler sets up the table pointer correctly."""
        load_binary(cpu, assembler_binary)
        load_source(cpu, b"BRK \n")

        # Run assembler until table pointer is set up (trap at address after table setup)
        # Table pointer setup ends at $0284, so we trap there
        cpu.run(0x0200, max_cycles=10000, trap_addresses=[0x0284])

        # Check table pointer at $0E-$0F was set up correctly
        table_ptr = cpu.memory[0x0E] | (cpu.memory[0x0F] << 8)
        assert table_ptr == 0x0500, f"Table pointer should be $0500, got ${table_ptr:04X}"
        assert cpu.pc == 0x0284, f"Should have stopped at table setup completion, PC=${cpu.pc:04X}"
