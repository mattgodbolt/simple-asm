# Minimal 6502 Assembler Design

## Overview
A hand-assemblable 6502 assembler with the absolute minimum complexity needed to bootstrap a better assembler.

## Core Constraints
- Source code is read from address `$1000` (all numbers in hex)
- Output defaults to address `$2000` (can be relocated with `!` directive)
- After assembly completes, jump to the assembled program location
- Every instruction is padded to exactly **4 bytes** using NOPs (`$EA`)
- No labels supported by the 6502 assembler itself (but punch card format supports them)
- Addressing mode is encoded in the opcode name itself

## Instruction Format

### Source Format
```
OPCD HHHHH
```
- `OPCD`: 4-character opcode (right-padded with spaces if shorter)
- Space(s)
- `HHH`: Hex operand (1-4 digits, no $ prefix needed)

### Output Format
All instructions generate exactly 4 bytes:
```
[opcode] [operand-low] [operand-high/NOP] [NOP]
```

## Supported Instructions

### Memory Operations
| Mnemonic | Opcode | Mode | Example | Output |
|----------|--------|------|---------|--------|
| `LDA#` | `$A9` | Immediate | `LDA# 42` | `A9 42 EA EA` |
| `LDAZ` | `$A5` | Zero Page | `LDAZ 80` | `A5 80 EA EA` |
| `LDA ` | `$AD` | Absolute | `LDA  3000` | `AD 00 30 EA` |
| `STA ` | `$8D` | Absolute | `STA  2100` | `8D 00 21 EA` |
| `STAZ` | `$85` | Zero Page | `STAZ 80` | `85 80 EA EA` |
| `LDX#` | `$A2` | Immediate | `LDX# 00` | `A2 00 EA EA` |
| `LDY#` | `$A0` | Immediate | `LDY# FF` | `A0 FF EA EA` |
| `STX ` | `$8E` | Absolute | `STX  2000` | `8E 00 20 EA` |
| `STY ` | `$8C` | Absolute | `STY  2000` | `8C 00 20 EA` |

### Indexed Operations
| Mnemonic | Opcode | Mode | Example | Output |
|----------|--------|------|---------|--------|
| `LDAX` | `$BD` | Absolute,X | `LDAX 3000` | `BD 00 30 EA` |
| `LDAY` | `$B9` | Absolute,Y | `LDAY 3000` | `B9 00 30 EA` |
| `STAX` | `$9D` | Absolute,X | `STAX 2100` | `9D 00 21 EA` |
| `STAY` | `$99` | Absolute,Y | `STAY 2100` | `99 00 21 EA` |

### Arithmetic
| Mnemonic | Opcode | Mode | Example | Output |
|----------|--------|------|---------|--------|
| `ADC#` | `$69` | Immediate | `ADC# 01` | `69 01 EA EA` |
| `SBC#` | `$E9` | Immediate | `SBC# 01` | `E9 01 EA EA` |
| `CMP#` | `$C9` | Immediate | `CMP# 00` | `C9 00 EA EA` |
| `CMPZ` | `$C5` | Zero Page | `CMPZ 80` | `C5 80 EA EA` |
| `CMP ` | `$CD` | Absolute | `CMP  2000` | `CD 00 20 EA` |
| `INC ` | `$EE` | Absolute | `INC  2000` | `EE 00 20 EA` |
| `DEC ` | `$CE` | Absolute | `DEC  2000` | `CE 00 20 EA` |

### Register Operations
| Mnemonic | Opcode | Mode | Example | Output |
|----------|--------|------|---------|--------|
| `INX ` | `$E8` | Implied | `INX` | `E8 EA EA EA` |
| `DEX ` | `$CA` | Implied | `DEX` | `CA EA EA EA` |
| `INY ` | `$C8` | Implied | `INY` | `C8 EA EA EA` |
| `DEY ` | `$88` | Implied | `DEY` | `88 EA EA EA` |
| `TAX ` | `$AA` | Implied | `TAX` | `AA EA EA EA` |
| `TAY ` | `$A8` | Implied | `TAY` | `A8 EA EA EA` |
| `TXA ` | `$8A` | Implied | `TXA` | `8A EA EA EA` |
| `TYA ` | `$98` | Implied | `TYA` | `98 EA EA EA` |

### Control Flow
| Mnemonic | Opcode | Mode | Example | Output |
|----------|--------|------|---------|--------|
| `JMP ` | `$4C` | Absolute | `JMP  2000` | `4C 00 20 EA` |
| `BEQ ` | `$F0` | Relative | `BEQ  03` | `F0 0C EA EA` |
| `BNE ` | `$D0` | Relative | `BNE  FD` | `D0 F4 EA EA` |
| `BCS ` | `$B0` | Relative | `BCS  02` | `B0 08 EA EA` |
| `BCC ` | `$90` | Relative | `BCC  01` | `90 04 EA EA` |

### Stack Operations
| Mnemonic | Opcode | Mode | Example | Output |
|----------|--------|------|---------|--------|
| `PHA ` | `$48` | Implied | `PHA` | `48 EA EA EA` |
| `PLA ` | `$68` | Implied | `PLA` | `68 EA EA EA` |

### Flag Operations
| Mnemonic | Opcode | Mode | Example | Output |
|----------|--------|------|---------|--------|
| `CLC ` | `$18` | Implied | `CLC` | `18 EA EA EA` |
| `SEC ` | `$38` | Implied | `SEC` | `38 EA EA EA` |

### Special Operations
| Mnemonic | Opcode | Mode | Example | Output |
|----------|--------|------|---------|--------|
| `NOP ` | `$EA` | Implied | `NOP` | `EA EA EA EA` |
| `BRK ` | `$00` | Implied | `BRK` | `00 EA EA EA` |
| `RTS ` | `$60` | Implied | `RTS` | `60 EA EA EA` |
| `JSR ` | `$20` | Absolute | `JSR  2100` | `20 00 21 EA` |

## Branch Offset Calculation
Branch operands can be specified as:
1. **Instruction counts** (preferred when writing by hand): `BEQ 03` = skip 3 instructions
2. **Raw 6502 offsets** (what the CPU uses): standard relative to PC+2

Formula for instruction counts: `6502_offset = instruction_count * 4 + 2`

Examples:
- `BNE 03`: Skip 3 instructions = 6502 offset +14 = `$0E`
- `BEQ FD`: Back 3 instructions = 6502 offset -10 = `$F6`

Note: Labels are converted to these offsets by the punch card formatter.

## Assembly Process

1. **Initialize**: Set read pointer to `$1000`, write pointer to `$2000`
2. **Main Loop**:
   - Read 4 characters for opcode
   - Skip spaces
   - Read hex operand (if present)
   - Look up opcode in table
   - Write opcode byte
   - Write operand bytes (or NOPs)
   - Pad to 4 bytes with NOPs
   - Advance write pointer by 4
3. **Terminate**: When "END " found or source exhausted
4. **Execute**: Jump to `$2000`

## Opcode Table Structure
Each entry needs:
- 4-byte mnemonic (for comparison)
- 1-byte opcode value
- 1-byte operand type:
  - `0`: No operand (implied)
  - `1`: 1-byte operand (immediate/zero page)
  - `2`: 2-byte operand (absolute)
  - `3`: 1-byte relative (needs *4 conversion)

## Example Program
```
LDA# 00     ; A9 00 EA EA - Initialize accumulator
STA  2100   ; 8D 00 21 EA - Store at $2100
INC  2100   ; EE 00 21 EA - Increment value
LDA  2100   ; AD 00 21 EA - Load it back
CMP# 0A     ; C9 0A EA EA - Compare with 10
BNE  FD     ; D0 F4 EA EA - Branch back 3 instructions if not equal
BRK         ; 00 EA EA EA - Done
```

## Memory Map
```
$0000-001F: Zero page variables (assembler workspace)
$0020-00FF: Zero page (available for assembled programs)
$0100-01FF: Stack (6502 hardware stack)
$0200-03FF: Assembler code (~512 bytes max)
$0400-04FF: Opcode lookup table (6 bytes per entry)
$0500-0FFF: Reserved/workspace
$1000-1FFF: Source code (ASCII input)
$2000-2FFF: Assembled output
```

## Zero Page Variables ($00-$1F)
```
$00-01: Source pointer (16-bit, starts at $1000)
$02-03: Output pointer (16-bit, starts at $2000)
$04:    Current character from source
$05-08: Opcode buffer (4 ASCII chars)
$09:    Operand low byte
$0A:    Operand high byte
$0B:    Found opcode value (from table)
$0C:    Operand type (0=none, 1=byte, 2=word, 3=branch)
$0D:    Scratch byte
$0E-0F: Table search pointer
$10:    Loop counter/temp
$11-1F: Reserved for expansion
```

## Opcode Table Format (at $0400)
Each entry is exactly 6 bytes:
```
Bytes 0-3: ASCII mnemonic (e.g., "LDA#", "BNE ", "JSR ")
Byte 4:    6502 opcode value
Byte 5:    Operand type:
           0 = No operand (implied)
           1 = 1-byte operand
           2 = 2-byte operand (little-endian)
           3 = Branch offset (multiply operand by 4)
```

## Memory Requirements
- Zero page: 32 bytes
- Assembler code: ~400 bytes (estimated)
- Opcode table: ~180 bytes (30 entries × 6 bytes)
- Total: ~612 bytes

## Advanced Features

### Data Definition
```
"TEXT"      ; String literal → ASCII bytes
#DEADBEEF   ; Hex data → raw bytes
```

### Relocation Support
```
!1E00       ; Set relocation offset (output_addr - effective_addr)
@0200       ; Set effective address to $0200, skip forward in address space
```

This enables bootstrap: code assembled to run at $0200 but stored at $2000.

## Label Support (Python Assembler Only)

The friendly format supports labels for better readability:

### Two-Pass Assembly
1. **First pass**: Collect label definitions and calculate addresses
2. **Second pass**: Resolve label references to addresses

### Label Syntax
```assembly
MAIN_LOOP:          ; Label definition (anywhere on line)
  LDA# 42           ; Instructions can be indented
  BEQ :END_PROGRAM  ; Label reference with : prefix
  JSR :SUBROUTINE   ; Works with JSR and JMP too
  JMP :MAIN_LOOP    ; Jump back to label

END_PROGRAM:
  BRK

SUBROUTINE:
  RTS
```

### Punch Card Conversion
Labels are resolved during conversion to punch format:
- `punch_card_formatter.py` handles all label resolution
- The 6502 assembler only sees numeric offsets
- Both assemblers produce identical machine code

## Notes
- Relocation allows flexible memory layouts for bootstrap scenarios
- Data definition enables opcode tables and strings inline with code
- No error checking - garbage in, garbage out
- All hex numbers are raw (no $ prefix)
- Mnemonics are exactly 4 characters (space-padded)
- Zero page provides fast access to all key variables
