# Hand Assembly Guide

## Converting the Assembler Source to Machine Code

This guide shows how to hand-assemble our minimal 6502 assembler from `assembler_source.asm` into machine code that can be toggled into a computer via front panel switches.

## Step 1: Understanding the Format

Each line in our assembler source follows this pattern:
```
OPCD OPER    ; Address: Machine Code - Comment
```

For example:
```
LDA# 00      ; $0200: A9 00 EA EA
```

This means:
- `LDA#` (load immediate) with operand `00`
- Should be placed at address `$0200`
- Generates machine code: `A9 00 EA EA`

## Step 2: Machine Code Translation

Here's the complete hand-assembly of our assembler:

### Initialization Section ($0200-$021F)
```
Address  | Source      | Machine Code | Explanation
---------|-------------|--------------|---------------------------
$0200    | LDA# 00     | A9 00 EA EA  | A=0
$0204    | STAZ 00     | 85 00 EA EA  | Store A to zero page $00
$0208    | LDA# 10     | A9 10 EA EA  | A=$10
$020C    | STAZ 01     | 85 01 EA EA  | Store A to zero page $01 (src=$1000)
$0210    | LDA# 00     | A9 00 EA EA  | A=0
$0214    | STAZ 02     | 85 02 EA EA  | Store A to zero page $02
$0218    | LDA# 20     | A9 20 EA EA  | A=$20
$021C    | STAZ 03     | 85 03 EA EA  | Store A to zero page $03 (out=$2000)
```

### Main Loop Section ($0220-$024F)
```
$0220    | LDY# 00     | A0 00 EA EA  | Y=0 (index for reading)
$0224    | LDAY 00     | B1 00 EA EA  | A = (source+Y)
$0228    | STAY 05     | 91 05 EA EA  | (buffer+Y) = A
$022C    | INY         | C8 EA EA EA  | Y++
$0230    | CPY# 04     | C0 04 EA EA  | Compare Y with 4
$0234    | BNE  FD     | D0 F4 EA EA  | Branch back if Y≠4
$0238    | CLC         | 18 EA EA EA  | Clear carry
$023C    | LDA  00     | A5 00 EA EA  | A = source pointer low
$0240    | ADC# 04     | 69 04 EA EA  | A += 4
$0244    | STAZ 00     | 85 00 EA EA  | Store back
$0248    | BCC  02     | 90 08 EA EA  | Skip if no carry
$024C    | INC  01     | E6 01 EA EA  | Increment high byte
```

### Space Skipping Section ($0250-$0277)
```
$0250    | LDAY 00     | B1 00 EA EA  | A = current char
$0254    | CMP# 20     | C9 20 EA EA  | Compare with space
$0258    | BNE  05     | D0 14 EA EA  | If not space, continue
$025C    | CLC         | 18 EA EA EA  | Clear carry
$0260    | LDA  00     | A5 00 EA EA  | A = source pointer low
$0264    | ADC# 01     | 69 01 EA EA  | A += 1
$0268    | STAZ 00     | 85 00 EA EA  | Store back
$026C    | BCC  FA     | 90 E8 EA EA  | Loop back to space check
$0270    | INC  01     | E6 01 EA EA  | Increment high byte
$0274    | JMP  F8     | 4C 50 02 EA  | Jump back to space check
```

## Step 3: Opcode Table Data

The opcode table should be placed starting at $0450 (after the main code):

```
Address  | Data                    | Meaning
---------|-------------------------|------------------
$0450    | 4C 44 41 23 A9 01      | "LDA#" -> $A9, type 1
$0456    | 4C 44 41 20 AD 02      | "LDA " -> $AD, type 2  
$045C    | 4C 44 41 5A A5 01      | "LDAZ" -> $A5, type 1
...      | (continue for all opcodes)
```

See `opcode_table.md` for the complete table layout.

## Step 4: Hand-Assembly Process

### Using Front Panel Switches (Altair 8800 style):
1. Set address switches to $0200
2. Set data switches to $A9 (first byte)
3. Press DEPOSIT
4. Set data switches to $00 (second byte)  
5. Press DEPOSIT NEXT
6. Continue for all bytes...

### Using Monitor Program:
If you have a simple monitor, you can enter:
```
0200: A9 00 EA EA 85 00 EA EA A9 10 EA EA 85 01 EA EA
0210: A9 00 EA EA 85 02 EA EA A9 20 EA EA 85 03 EA EA
...
```

## Step 5: Bootstrap Sequence

1. **Load the assembler**: Toggle in the machine code at $0200
2. **Load source code**: Place assembly source at $1000 (via cards/tape)
3. **Run assembler**: Jump to $0200
4. **Collect output**: Machine code appears at $2000
5. **Save and run**: Save the output, then load and run it

## Step 6: Verification

Use the Python reference implementation to verify:
```bash
uv run python simple_asm.py test_program.asm
```

Compare the output with what your hand-assembled version produces.

## Complete Memory Map for Bootstrap

```
$0000-001F: Assembler variables (zero page)
$0100-01FF: Stack
$0200-044F: Hand-assembled assembler code
$0450-04FF: Opcode table
$1000-1FFF: Source code input
$2000-2FFF: Assembled output
```

## Critical Addresses for Debugging

- **Entry point**: $0200 (start here)
- **Main loop**: $0220 (opcode reading)
- **Lookup**: $0278 (table search)
- **Output**: $03C8 (instruction writing)
- **Variables**: $00-$1F (zero page)

## Testing Your Hand-Assembly

1. Start with the simple test program in `simple_test.asm`
2. Verify it produces the expected output
3. Then try assembling the assembler source itself
4. If it produces identical machine code, bootstrap is complete!

## What Happens After Bootstrap

Once you have a working assembler:
1. Write a better assembler with labels and expressions
2. Use the simple assembler to assemble the better one
3. Write a compiler using the better assembler
4. Each tool builds the next, climbing the abstraction ladder

This is exactly how early computers were bootstrapped in the 1960s and 70s!