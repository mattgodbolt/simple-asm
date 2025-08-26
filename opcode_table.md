# Opcode Table Specification

## Complete Table for Minimal Assembler

The opcode table starts at $0400 with 6-byte entries. Here's the complete specification:

```
Entry | Mnemonic | Opcode | Type | Description
------|----------|--------|------|------------------
  0   | "LDA#"   | $A9    | 1    | Load A immediate
  1   | "LDA "   | $AD    | 2    | Load A absolute
  2   | "LDAZ"   | $A5    | 1    | Load A zero page
  3   | "LDAX"   | $BD    | 2    | Load A absolute,X
  4   | "LDAY"   | $B9    | 2    | Load A absolute,Y

  5   | "LDX#"   | $A2    | 1    | Load X immediate
  6   | "LDX "   | $AE    | 2    | Load X absolute
  7   | "LDXZ"   | $A6    | 1    | Load X zero page

  8   | "LDY#"   | $A0    | 1    | Load Y immediate
  9   | "LDY "   | $AC    | 2    | Load Y absolute
 10   | "LDYZ"   | $A4    | 1    | Load Y zero page

 11   | "STA "   | $8D    | 2    | Store A absolute
 12   | "STAZ"   | $85    | 1    | Store A zero page
 13   | "STAX"   | $9D    | 2    | Store A absolute,X
 14   | "STAY"   | $99    | 2    | Store A absolute,Y

 15   | "STX "   | $8E    | 2    | Store X absolute
 16   | "STXZ"   | $86    | 1    | Store X zero page

 17   | "STY "   | $8C    | 2    | Store Y absolute
 18   | "STYZ"   | $84    | 1    | Store Y zero page

 19   | "ADC#"   | $69    | 1    | Add with carry immediate
 20   | "SBC#"   | $E9    | 1    | Subtract with carry immediate

 21   | "CMP#"   | $C9    | 1    | Compare A immediate
 22   | "CMP "   | $CD    | 2    | Compare A absolute
 23   | "CMPZ"   | $C5    | 1    | Compare A zero page

 24   | "CPX#"   | $E0    | 1    | Compare X immediate
 25   | "CPY#"   | $C0    | 1    | Compare Y immediate

 26   | "INC "   | $EE    | 2    | Increment absolute
 27   | "INCZ"   | $E6    | 1    | Increment zero page
 28   | "DEC "   | $CE    | 2    | Decrement absolute
 29   | "DECZ"   | $C6    | 1    | Decrement zero page

 30   | "INX "   | $E8    | 0    | Increment X
 31   | "DEX "   | $CA    | 0    | Decrement X
 32   | "INY "   | $C8    | 0    | Increment Y
 33   | "DEY "   | $88    | 0    | Decrement Y

 34   | "TAX "   | $AA    | 0    | Transfer A to X
 35   | "TAY "   | $A8    | 0    | Transfer A to Y
 36   | "TXA "   | $8A    | 0    | Transfer X to A
 37   | "TYA "   | $98    | 0    | Transfer Y to A

 38   | "JMP "   | $4C    | 2    | Jump absolute
 39   | "JSR "   | $20    | 2    | Jump to subroutine
 40   | "RTS "   | $60    | 0    | Return from subroutine

 41   | "BEQ "   | $F0    | 3    | Branch if equal
 42   | "BNE "   | $D0    | 3    | Branch if not equal
 43   | "BCS "   | $B0    | 3    | Branch if carry set
 44   | "BCC "   | $90    | 3    | Branch if carry clear

 45   | "PHA "   | $48    | 0    | Push A
 46   | "PLA "   | $68    | 0    | Pull A

 47   | "CLC "   | $18    | 0    | Clear carry
 48   | "SEC "   | $38    | 0    | Set carry

 49   | "NOP "   | $EA    | 0    | No operation
 50   | "BRK "   | $00    | 0    | Break
 51   | "END "   | $FF    | 0    | End of source (special)
```

## Data Layout in Memory

Each entry is 6 bytes: 4 bytes mnemonic + 1 byte opcode + 1 byte type:
```
Entry 0: 4C 44 41 23    ; "LDA#"
         A9 01          ; $A9, type 1
Entry 1: 4C 44 41 20    ; "LDA "
         AD 02          ; $AD, type 2
Entry 2: 4C 44 41 5A    ; "LDAZ"
         A5 01          ; $A5, type 1
... etc
```

## Type Codes
- **Type 0**: No operand (implied instructions)
  - Output: [opcode] EA EA EA

- **Type 1**: Single byte operand
  - Output: [opcode] [operand] EA EA

- **Type 2**: Two byte operand (little-endian)
  - Output: [opcode] [low-byte] [high-byte] EA

- **Type 3**: Branch offset (multiply by 4 for 4-byte instruction spacing)
  - Input: signed instruction count (-128 to +127)
  - Output: [opcode] [offset*4] EA EA

## Special Cases

### END Marker
The "END " opcode ($FF) is not a real 6502 instruction - it's used by the assembler to detect end of source code.

### Branch Calculation Examples
- `BNE  01` = branch forward 1 instruction = offset +4 = $04
- `BEQ  03` = branch forward 3 instructions = offset +12 = $0C
- `BNE  FF` = branch back 1 instruction = offset -4 = $FC
- `BEQ  FD` = branch back 3 instructions = offset -12 = $F4

### Table End Detection
The assembler stops searching when it finds an entry starting with $00 or reaches the table end.

## Total Size
- 52 entries × 6 bytes = 312 bytes
- Fits in opcode table area with room for expansion
