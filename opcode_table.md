# Opcode Table Specification

## Complete Table for Minimal Assembler

The opcode table starts at $0400 with 6-byte entries. Here's the complete specification:

```
Address  | Mnemonic | Opcode | Type | Description
---------|----------|--------|------|------------------
$0400-05 | "LDA#"   | $A9    | 1    | Load A immediate
$0406-0B | "LDA "   | $AD    | 2    | Load A absolute  
$040C-11 | "LDAZ"   | $A5    | 1    | Load A zero page
$0412-17 | "LDAX"   | $BD    | 2    | Load A absolute,X
$0418-1D | "LDAY"   | $B9    | 2    | Load A absolute,Y

$041E-23 | "LDX#"   | $A2    | 1    | Load X immediate
$0424-29 | "LDX "   | $AE    | 2    | Load X absolute
$042A-2F | "LDXZ"   | $A6    | 1    | Load X zero page

$0430-35 | "LDY#"   | $A0    | 1    | Load Y immediate  
$0436-3B | "LDY "   | $AC    | 2    | Load Y absolute
$043C-41 | "LDYZ"   | $A4    | 1    | Load Y zero page

$0442-47 | "STA "   | $8D    | 2    | Store A absolute
$0448-4D | "STAZ"   | $85    | 1    | Store A zero page
$044E-53 | "STAX"   | $9D    | 2    | Store A absolute,X
$0454-59 | "STAY"   | $99    | 2    | Store A absolute,Y

$045A-5F | "STX "   | $8E    | 2    | Store X absolute
$0460-65 | "STXZ"   | $86    | 1    | Store X zero page

$0466-6B | "STY "   | $8C    | 2    | Store Y absolute
$046C-71 | "STYZ"   | $84    | 1    | Store Y zero page

$0472-77 | "ADC#"   | $69    | 1    | Add with carry immediate
$0478-7D | "SBC#"   | $E9    | 1    | Subtract with carry immediate

$047E-83 | "CMP#"   | $C9    | 1    | Compare A immediate
$0484-89 | "CMP "   | $CD    | 2    | Compare A absolute
$048A-8F | "CMPZ"   | $C5    | 1    | Compare A zero page

$0490-95 | "CPX#"   | $E0    | 1    | Compare X immediate
$0496-9B | "CPY#"   | $C0    | 1    | Compare Y immediate

$049C-A1 | "INC "   | $EE    | 2    | Increment absolute
$04A2-A7 | "INCZ"   | $E6    | 1    | Increment zero page
$04A8-AD | "DEC "   | $CE    | 2    | Decrement absolute
$04AE-B3 | "DECZ"   | $C6    | 1    | Decrement zero page

$04B4-B9 | "INX "   | $E8    | 0    | Increment X
$04BA-BF | "DEX "   | $CA    | 0    | Decrement X
$04C0-C5 | "INY "   | $C8    | 0    | Increment Y
$04C6-CB | "DEY "   | $88    | 0    | Decrement Y

$04CC-D1 | "TAX "   | $AA    | 0    | Transfer A to X
$04D2-D7 | "TAY "   | $A8    | 0    | Transfer A to Y
$04D8-DD | "TXA "   | $8A    | 0    | Transfer X to A
$04DE-E3 | "TYA "   | $98    | 0    | Transfer Y to A

$04E4-E9 | "JMP "   | $4C    | 2    | Jump absolute
$04EA-EF | "JSR "   | $20    | 2    | Jump to subroutine
$04F0-F5 | "RTS "   | $60    | 0    | Return from subroutine

$04F6-FB | "BEQ "   | $F0    | 3    | Branch if equal
$04FC-01 | "BNE "   | $D0    | 3    | Branch if not equal  
$0502-07 | "BCS "   | $B0    | 3    | Branch if carry set
$0508-0D | "BCC "   | $90    | 3    | Branch if carry clear

$050E-13 | "PHA "   | $48    | 0    | Push A
$0514-19 | "PLA "   | $68    | 0    | Pull A

$051A-1F | "CLC "   | $18    | 0    | Clear carry
$0520-25 | "SEC "   | $38    | 0    | Set carry

$0526-2B | "NOP "   | $EA    | 0    | No operation
$052C-31 | "BRK "   | $00    | 0    | Break
$0532-37 | "END "   | $FF    | 0    | End of source (special)
```

## Data Layout in Memory

Starting at $0400:
```
$0400: 4C 44 41 23    ; "LDA#" 
$0404: A9 01          ; $A9, type 1
$0406: 4C 44 41 20    ; "LDA " 
$040A: AD 02          ; $AD, type 2
$040C: 4C 44 41 5A    ; "LDAZ"
$0410: A5 01          ; $A5, type 1
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
The assembler stops searching when it reaches $0538 (beyond the last entry) or finds an entry starting with $00.

## Total Size
- 42 entries × 6 bytes = 252 bytes
- Fits comfortably in 256-byte page at $0400-$04FF
- Leaves room for expansion up to $0500