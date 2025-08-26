"""Tests for label support in Python assembler."""

import subprocess
import tempfile
from pathlib import Path

import pytest


class TestLabels:
    """Test label functionality."""

    def test_label_definition_and_reference(self):
        """Test that labels can be defined and referenced."""
        test_asm = """
        LOOP:
        LDA# 42
        JSR  :LOOP
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

            # LOOP is at address 8000, so JSR :LOOP should be JSR $8000
            # JSR is 20, followed by little-endian address 00 80
            assert data[0:4] == bytes([0xA9, 0x42, 0xEA, 0xEA])  # LDA #42
            assert data[4:8] == bytes([0x20, 0x00, 0x80, 0xEA])  # JSR $8000
            assert data[8:12] == bytes([0x00, 0xEA, 0xEA, 0xEA])  # BRK

            # Cleanup
            Path(f.name).unlink()
            bin_path.unlink()

    def test_multiple_labels(self):
        """Test multiple labels in the same program."""
        test_asm = """
        START:
        LDA# 42
        JSR  :END
        BRK

        END:
        STAZ 80
        JSR  :START
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

            # START at 8000, END at 800C
            assert data[0:4] == bytes([0xA9, 0x42, 0xEA, 0xEA])  # LDA #42
            assert data[4:8] == bytes([0x20, 0x0C, 0x80, 0xEA])  # JSR END ($800C)
            assert data[8:12] == bytes([0x00, 0xEA, 0xEA, 0xEA])  # BRK
            assert data[12:16] == bytes([0x85, 0x80, 0xEA, 0xEA])  # STAZ 80
            assert data[16:20] == bytes([0x20, 0x00, 0x80, 0xEA])  # JSR START ($8000)

            # Cleanup
            Path(f.name).unlink()
            bin_path.unlink()

    def test_punch_format_no_labels(self):
        """Test that punch format doesn't support labels."""
        test_punch = """
        LDA# 42
        JSR  :LABEL
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".punch", delete=False) as f:
            f.write(test_punch)
            f.flush()

            result = subprocess.run(["uv", "run", "python", "simple_asm.py", f.name], capture_output=True, text=True)

            # Should fail because punch format doesn't support labels
            assert result.returncode != 0
            assert (
                "Unknown label" in result.stdout
                or "Unknown label" in result.stderr
                or "Invalid operand" in result.stderr
            )

            # Cleanup
            Path(f.name).unlink()
