"""Tests for the assembler functionality."""

import subprocess
import tempfile
from pathlib import Path

import pytest


class TestAssembler:
    """Test the assembler functionality."""

    def test_string_data_directive(self):
        """Test that string data directives work correctly."""
        # Create a test assembly file with string data
        test_asm = """
        LDA# 42
        "HELLO"
        BRK
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
            f.write(test_asm)
            f.flush()

            # Assemble it
            result = subprocess.run(["uv", "run", "python", "simple_asm.py", f.name], capture_output=True, text=True)

            if result.returncode != 0:
                pytest.fail(f"Assembly failed: {result.stderr}")

            # Check the binary output
            bin_path = Path(f.name).with_suffix(".bin")
            assert bin_path.exists(), "Binary output file not created"

            with open(bin_path, "rb") as bf:
                data = bf.read()

            # Should contain: LDA#42 (A9 42 EA EA) + "HELLO" (48 45 4C 4C 4F) + BRK (00 EA EA EA)
            assert data[0:4] == bytes([0xA9, 0x42, 0xEA, 0xEA])  # LDA #42
            assert data[4:9] == b"HELLO"  # String data
            assert data[9:13] == bytes([0x00, 0xEA, 0xEA, 0xEA])  # BRK

            # Cleanup
            Path(f.name).unlink()
            bin_path.unlink()

    def test_hex_data_directive(self):
        """Test that hex data directives work correctly."""
        test_asm = """
        LDA# 42
        #DEADBEEF
        BRK
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
            f.write(test_asm)
            f.flush()

            result = subprocess.run(["uv", "run", "python", "simple_asm.py", f.name], capture_output=True, text=True)

            if result.returncode != 0:
                pytest.fail(f"Assembly failed: {result.stderr}")

            bin_path = Path(f.name).with_suffix(".bin")
            with open(bin_path, "rb") as bf:
                data = bf.read()

            # Should contain: LDA#42 + hex data + BRK
            assert data[0:4] == bytes([0xA9, 0x42, 0xEA, 0xEA])  # LDA #42
            assert data[4:8] == bytes([0xDE, 0xAD, 0xBE, 0xEF])  # Hex data
            assert data[8:12] == bytes([0x00, 0xEA, 0xEA, 0xEA])  # BRK

            # Cleanup
            Path(f.name).unlink()
            bin_path.unlink()

    def test_relocation_directive(self):
        """Test that relocation directives work correctly."""
        test_asm = """
        @0300
        LDA# 42
        BRK
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
            f.write(test_asm)
            f.flush()

            result = subprocess.run(["uv", "run", "python", "simple_asm.py", f.name], capture_output=True, text=True)

            if result.returncode != 0:
                pytest.fail(f"Assembly failed: {result.stderr}")

            bin_path = Path(f.name).with_suffix(".bin")
            with open(bin_path, "rb") as bf:
                data = bf.read()

            # Data should start at offset 0x300, first 0x300 bytes should be zeros
            assert data[0:0x300] == bytes(0x300)  # Zeros
            assert data[0x300:0x304] == bytes([0xA9, 0x42, 0xEA, 0xEA])  # LDA #42 at $0300
            assert data[0x304:0x308] == bytes([0x00, 0xEA, 0xEA, 0xEA])  # BRK

            # Cleanup
            Path(f.name).unlink()
            bin_path.unlink()

    def test_format_conversion(self):
        """Test that friendly format converts to punch format correctly."""
        friendly_asm = """
        ; This is a comment
        LDA# 42    ; Load 42
        STAZ 80    ; Store at $80
        BRK        ; Stop
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
            f.write(friendly_asm)
            f.flush()

            punch_path = Path(f.name).with_suffix(".punch")

            # Convert to punch format
            result = subprocess.run(
                ["uv", "run", "python", "punch_card_formatter.py", f.name, str(punch_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                pytest.fail(f"Conversion failed: {result.stderr}")

            assert punch_path.exists(), "Punch file not created"

            # Check punch file content
            with open(punch_path) as pf:
                content = pf.read()
                lines = content.rstrip("\n").split("\n")  # Remove trailing newline but preserve spaces

            expected_lines = ["LDA# 42", "STAZ 80", "BRK "]
            assert lines == expected_lines, f"Expected {expected_lines}, got {lines}"

            # Cleanup
            Path(f.name).unlink()
            punch_path.unlink()
