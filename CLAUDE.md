# Simple 6502 Assembler Project

Research project exploring 6502 assembly and bootstrapping. Focus on historical accuracy and minimal complexity.

## Key Principles

- Keep the 6502 assembler brutally simple (must be hand-assemblable)
- Both formats (friendly .asm and punch .punch) must produce identical output
- Native 6502 instruction sizes (no padding)
- No error checking - garbage in, garbage out
- Historical punch card workflow simulation

## Architecture

- Source at $1000, output at $2000
- Bootstrap: assembler runs at $0200 but assembles at $2000 (relocation)
- Native 6502 branch offsets (PC+2 relative)
- Zero page variables for assembler state

### Assembly Coding Standards

**Memory Layout:**
- Use labels for all jump targets. Only use `@xxxx` directives for critical memory locations (e.g., opcode table at $1000)
- Use `@` to ensure critical code sections land at predictable addresses

**Control Flow:**
- Always use labels for all branch and jump targets: `BEQ :LOOP_END`, `JMP :MAIN_LOOP`
- NO exceptions - never use numeric offsets like "01"
- Branch offsets use native 6502 format (PC+2 relative)

**Code Documentation:**
- Do NOT include machine code bytes in comments (e.g. avoid `; A9 42 EA EA`)
- When loading address table values, clearly comment the purpose:
  - `LDA# 10` ; High byte of opcode table ($1000)
  - `LDA# 00` ; Low byte of opcode table ($1000)
- Comment the intent and memory layout, not the encoding

Both Python and 6502 assemblers produce identical output using native 6502 instruction formats.

## Testing

Always verify both assemblers produce identical results. The Python version is the reference implementation.

Run full test suite with `make all` and bootstrap test with `make test-bootstrap`.

## Important Environment Notes

- NEVER change directory from the project root
- ALWAYS use `uv run python` instead of just `python` to ensure correct Python version
- ALWAYS create temporary files in `./tmp` directory, never in project root
- ALWAYS use file tools (Write, Edit) instead of shell commands (cat, echo) for file operations

## File Naming

- .asm files: friendly format with comments
- .punch files: machine format, no comments
- .bin files: assembled machine code

## Relocation System

- `!xxxx` sets relocation offset
- `@xxxx` sets effective address and fills gaps
- Enables complex memory layouts for bootstrap scenarios
