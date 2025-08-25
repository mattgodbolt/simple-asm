"""Shared test fixtures and helpers for pytest."""

from pathlib import Path

import pytest

from simple_6502_emulator import CPU6502


@pytest.fixture
def cpu():
    """Create a fresh CPU instance."""
    return CPU6502()


@pytest.fixture
def assembler_binary():
    """Load the assembler binary if it exists."""
    binary_path = Path("assembler_source.bin")
    if not binary_path.exists():
        pytest.skip("assembler_source.bin not found - run 'make assemble-assembler' first")

    with open(binary_path, "rb") as f:
        return f.read()


def load_binary(cpu: CPU6502, data: bytes, address: int = 0) -> None:
    """Load binary data into CPU memory at specified address."""
    cpu.memory[address : address + len(data)] = data


def load_source(cpu: CPU6502, source: bytes, address: int = 0x2000) -> None:
    """Load source code into CPU memory at specified address."""
    cpu.memory[address : address + len(source)] = source


def get_opcode_table_entry(data: bytes, index: int, table_offset: int = 0x1000) -> tuple[bytes, int, int]:
    """Extract an opcode table entry from binary data.

    Returns: (mnemonic, opcode, type)
    """
    offset = table_offset + (index * 6)
    if offset + 6 > len(data):
        raise IndexError(f"Entry {index} is beyond binary size")

    mnemonic = data[offset : offset + 4]
    opcode = data[offset + 4]
    optype = data[offset + 5]
    return mnemonic, opcode, optype


def find_in_opcode_table(data: bytes, mnemonic: bytes, table_offset: int = 0x1000) -> tuple[int, int, int] | None:
    """Find a mnemonic in the opcode table.

    Returns: (index, opcode, type) or None if not found
    """
    for i in range(20):  # Max 20 entries to prevent infinite loop
        try:
            entry_mnem, opcode, optype = get_opcode_table_entry(data, i, table_offset)
            if entry_mnem == mnemonic:
                return i, opcode, optype
        except IndexError:
            break
    return None


def assemble_bytes(*opcodes: int) -> bytes:
    """Helper to create a sequence of opcodes/operands."""
    return bytes(opcodes)
