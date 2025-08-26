# Simple 6502 Assembler Project

Research project exploring 6502 assembly and bootstrapping. Focus on historical accuracy and minimal complexity.

## Key Principles

- Keep the 6502 assembler brutally simple (must be hand-assemblable)
- Both formats (friendly .asm and punch .punch) must produce identical output
- Every instruction is exactly 4 bytes (padded with NOPs)
- No error checking - garbage in, garbage out
- Historical punch card workflow simulation

## Architecture

- Source at $1000, output at $2000
- Bootstrap: assembler runs at $0200 but assembles at $2000 (relocation)
- Fixed 4-byte instructions enable simple branch offset calculation
- Zero page variables for assembler state

### Branch Instruction Convention

Branch operands can be specified as:
1. **Labels** (preferred): `BEQ :END_LOOP` - resolved by punch card formatter
2. **Instruction counts** (numeric): `BEQ 05` means "skip 5 instructions"
   - Formula: actual_6502_offset = operand * 4 + 2
   - This makes it easier for humans to count instructions
   - Only use numeric when labels aren't practical

Both Python and 6502 assemblers produce identical branch offsets using standard 6502 conventions.

## Testing

Always verify both assemblers produce identical results. The Python version is the reference implementation.

Run full test suite with `make all` and bootstrap test with `make test-bootstrap`.

## Important Environment Notes

- NEVER change directory from the project root
- ALWAYS use `uv run python` instead of just `python` to ensure correct Python version

## File Naming

- .asm files: friendly format with comments
- .punch files: machine format, no comments
- .bin files: assembled machine code

## Relocation System

- `!xxxx` sets relocation offset
- `@xxxx` sets effective address and fills gaps
- Enables complex memory layouts for bootstrap scenarios
