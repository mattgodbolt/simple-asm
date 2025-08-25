# Test Programs for Minimal Assembler

## Test 1: Hello World (Memory Pattern)
Simple program to verify basic instruction assembly:

```
LDA# 48     ; Load 'H' (ASCII 72 = $48)
STA  2100   ; Store to memory
LDA# 45     ; Load 'E' (ASCII 69 = $45)
STA  2101   ; Store to memory
LDA# 4C     ; Load 'L' (ASCII 76 = $4C)
STA  2102   ; Store to memory
STA  2103   ; Store again for double L
LDA# 4F     ; Load 'O' (ASCII 79 = $4F)
STA  2104   ; Store to memory
BRK         ; End program
END         ; End of source
```

Expected output at $2000:
```
A9 48 EA EA  ; LDA# 48
8D 00 21 EA  ; STA 2100
A9 45 EA EA  ; LDA# 45
8D 01 21 EA  ; STA 2101
A9 4C EA EA  ; LDA# 4C
8D 02 21 EA  ; STA 2102
8D 03 21 EA  ; STA 2103
A9 4F EA EA  ; LDA# 4F
8D 04 21 EA  ; STA 2104
00 EA EA EA  ; BRK
```

## Test 2: Simple Counter
Tests loops and branching:

```
LDA# 00     ; Initialize counter
STA  80     ; Store in zero page
LOOP:       ; (This would be address $200C in assembled code)
INC  80     ; Increment counter
LDA  80     ; Load counter
CMP# 0A     ; Compare with 10
BNE  FD     ; Branch back 3 instructions (to INC 80)
BRK         ; Done
END
```

Expected output:
```
A9 00 EA EA  ; LDA# 00
85 80 EA EA  ; STAZ 80
E6 80 EA EA  ; INCZ 80
A5 80 EA EA  ; LDAZ 80
C9 0A EA EA  ; CMP# 0A
D0 F4 EA EA  ; BNE FD (-3 * 4 = -12 = $F4)
00 EA EA EA  ; BRK
```

## Test 3: Memory Copy
Tests indexed addressing:

```
LDX# 00     ; Initialize index
LDA  3000   ; Load from source (absolute for simplicity)
STA  4000   ; Store to destination
INX         ; Next byte
CPX# 08     ; Copied 8 bytes?
BNE  FA     ; Branch back 6 instructions
BRK
END
```

## Test 4: Subroutine Call
Tests JSR/RTS:

```
JSR  0008   ; Call subroutine (8 instructions forward)
LDA# FF     ; Main program continues
STA  2100   ; Store result
BRK         ; End main
; Subroutine starts here ($2000 + 8*4 = $2020)
LDA# 42     ; Load answer
RTS         ; Return
END
```

## Test 5: The Assembler Itself
The ultimate test - can our assembler assemble itself?

Input: The assembler source code from assembler_source.asm
Expected: Should produce identical machine code to what we hand-assembled

## Python Reference Implementation

To verify our design works, we'll create a Python version that implements the exact same logic:

1. Read source from specified address (simulated)
2. Parse 4-character opcodes
3. Look up in identical opcode table
4. Generate 4-byte padded instructions
5. Output to specified address (simulated)

This Python version will let us:
- Test the assembler logic before hand-assembly
- Verify that our 6502 assembler produces correct output
- Debug any issues with the instruction format
- Prove the bootstrap concept works

The Python assembler will be bit-for-bit compatible with our 6502 version.
