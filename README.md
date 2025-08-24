# Simple 6502 Assembler

A minimal 6502 assembler system for bootstrapping research. This implements the historical workflow of writing assembly on paper, converting to punch cards, then feeding to a machine assembler.

## What This Is

Two assemblers that produce identical output:
- Python reference implementation (friendly format with comments)
- Hand-assembled 6502 assembler (punch card format, minimal parsing)

The 6502 assembler can assemble itself, demonstrating a complete bootstrap process.

## Quick Start

```bash
make all          # Build and test everything
make run-counter  # Run example program
make test-bootstrap  # Test self-assembly
```

## Format Support

Assembly source supports two formats:
- Friendly format: comments, flexible whitespace, human readable
- Punch card format: minimal, machine readable, no comments

Data definition:
- `"TEXT"` - string literals
- `#DEADBEEF` - hex data

Relocation for bootstrap:
- `!1E00` - set relocation offset  
- `@0200` - set effective address

## Files

- `simple_asm.py` - Python reference assembler
- `simple_6502_emulator.py` - 6502 CPU emulator  
- `punch_card_formatter.py` - Format converter
- `assembler_source.asm` - The 6502 assembler source
- `example_*.asm` - Test programs

This is research into early computing constraints and self-hosting compilers, not a practical development tool.