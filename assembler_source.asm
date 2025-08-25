; Minimal 6502 Assembler Source Code
; Written in our restricted 4-byte instruction format
; Assembles programs from $1000 to $2000

@0200        ; Entry point at $0200
; Initialize source pointer to $1000
LDA# 00
STAZ 00     ; Store to zero page $00
LDA# 20
STAZ 01     ; Store to zero page $01

; Initialize output pointer to $8000
LDA# 00
STAZ 02     ; Store to zero page $02
LDA# 80
STAZ 03     ; Store to zero page $03

@0220       ; Align main loop to clean address with room for growth
; Main assembly loop
; Read 4-character opcode into buffer at $05-$08
MAIN_LOOP:
LDAY 00     ; Peek at first character
CMP# 40     ; Is it '@' ($40)?
BEQ  05     ; Yes, handle @ directive
CMP# 23     ; Is it '#' ($23)?
BEQ  04     ; Yes, handle hex data
CMP# 22     ; Is it '"' ($22)?
BEQ  03     ; Yes, handle string data
JMP  0280   ; $023C: 4C 80 02 EA  - No, handle as opcode (CHAR_HANDLER)

; Handle @ directive - jump to handler
JMP  1200   ; $0240: 4C 00 12 EA  - @ directive handler (HANDLE_AT)

; Handle # hex data - jump to handler
JMP  1280   ; $0244: 4C 80 12 EA  - # hex data handler (HANDLE_HASH)

; Handle " string data - jump to handler
JMP  1300   ; $0248: 4C 00 13 EA  - " string data handler (HANDLE_STRING)

@0280       ; Align SKIP_SPACES routine
; Skip spaces and newlines then read 4-character opcode
CHAR_HANDLER:
LDAY 00     ; Read current char
CMP# 20     ; Is it space?
BEQ  06     ; Yes, advance pointer
CMP# 0A     ; Is it newline?
BNE  07     ; No, start reading opcode
; Advance source pointer by 1
CLC
LDAZ 00
ADC# 01
STAZ 00
BCC  F6     ; Loop back to SKIP_SPACES
INCZ 01
JMP  0280   ; $0270: 4C 80 02 EA  - Jump back to CHAR_HANDLER

; Read 4 characters into buffer
READ_OPCODE:
LDY# 00     ; Initialize index
READ_CHAR:
LDAY 00     ; Read from (source),Y
STAY 0005   ; $027C: 99 05 00 EA  - Store to buffer at $0005,Y
INY         ; Next character
CPY# 04     ; Read 4 chars?
BNE  FB     ; Loop back to read next char

; Advance source pointer by 4
CLC
LDAZ 00
ADC# 04
STAZ 00
BCC  01     ; Skip if no carry
INCZ 01     ; Increment high byte
JMP  0300   ; $027C: 4C 00 03 EA  - Jump to table lookup (LOOKUP_TABLE)

@0300       ; Align table lookup section with room for expansion
; Look up opcode in table at $0500
LOOKUP_TABLE:
LDA# 00     ; Table pointer low
STAZ 0E
LDA# 10     ; Table pointer high
STAZ 0F

; Compare current table entry with opcode buffer
TABLE_LOOP:
LDY# 00     ; Reset comparison index
COMPARE_CHARS:
LDAY 0E     ; Get table character
CMPY 0005   ; $0290: D9 05 00 EA  - Compare with buffer char at $0005,Y
BNE  0A     ; No match, try next entry
INY         ; Next character
CPY# 04     ; All 4 chars checked?
BNE  FA     ; Loop back to COMPARE_CHARS

; Found match! Extract opcode and type
LDY# 04     ; Point to opcode byte
LDAY 0E     ; Get opcode value
STAZ 0B     ; Store opcode
INY         ; Point to type byte
LDAY 0E     ; Get operand type
STAZ 0C     ; Store type
JMP  0400   ; $02BC: 4C 00 04 EA  - Jump to READ_OPERAND

; No match - advance to next table entry
NEXT_ENTRY:
CLC
LDAZ 0E     ; Table pointer low
ADC# 06     ; Each entry is 6 bytes
STAZ 0E
BCC  01     ; Skip if no carry
INCZ 0F     ; Increment high byte

; Check for end of table
LDAZ 0F
CMP# 11     ; Past OPCODE_TABLE end?
BCC  E9     ; No, continue TABLE_LOOP
BRK         ; Error - opcode not found

@0400       ; Align operand reading section
; Read operand based on type in $0C
READ_OPERAND:
LDAZ 0C     ; Get operand type
BNE  04     ; Not 0, check other types
JMP  0E00   ; Type 0: jump to WRITE_INST
CMP# 01     ; Type 1: single byte
BNE  04     ; Not 1, check type 2
JMP  0500   ; Type 1: jump to READ_BYTE
CMP# 02     ; Type 2: two bytes
BNE  04     ; Not 2, must be type 3
JMP  0540   ; Type 2: jump to READ_WORD
; Must be type 3: branch
JSR  0500   ; $0318: 20 00 05 EA  - Call READ_BYTE
; Multiply by 4 for branch offset and add 2
LDAZ 09     ; Get byte value
ASL         ; Shift left (×2)
ASL         ; Shift left (×4)
CLC         ; Clear carry
ADC# 02     ; Add 2 to compensate for PC offset
STAZ 09     ; Store result
JMP  0E00   ; Jump to WRITE_INST

@0500       ; Align READ_BYTE routine
; Read single byte operand
READ_BYTE:
JSR  0580   ; $0340: 20 80 05 EA  - Call hex conversion (HEX_TO_BYTE)
STAZ 09     ; Store low byte
LDA# 00
STAZ 0A     ; Clear high byte
JMP  0E00   ; Jump to WRITE_INST

@0540       ; Align READ_WORD routine
; Read two-byte operand (little-endian)
READ_WORD:
JSR  0580   ; $0360: 20 80 05 EA  - Call hex conversion
STAZ 0A     ; Store as high byte
JSR  0580   ; $0364: 20 80 05 EA  - Call hex conversion again
STAZ 09     ; Store as low byte
JMP  0E00   ; Jump to WRITE_INST

@0580       ; Align HEX_TO_BYTE routine
; Convert 2 hex digits to byte in A
; Advances source pointer by 2
HEX_TO_BYTE:
LDAY 00     ; Get first hex digit
JSR  05C0   ; $0384: 20 C0 05 EA  - Convert to nibble (HEX_TO_NIBBLE)
ASL         ; Shift to high nibble
ASL
ASL
ASL
STAZ 0D     ; Save high nibble
; Advance source pointer
JSR  0600   ; $0390: 20 00 06 EA  - Call ADVANCE_SOURCE
LDAY 00     ; Get second hex digit
JSR  05C0   ; $0394: 20 C0 05 EA  - Convert to nibble
ORAZ 0D     ; Combine with high nibble
STAZ 04     ; Store complete byte
JSR  0600   ; $0398: 20 00 06 EA  - Advance source again
LDAZ 04     ; Return byte in A
RTS

@05C0       ; Align HEX_NIBBLE routine
; Convert single hex ASCII char to nibble (0-F)
; Input: A = ASCII char, Output: A = nibble
HEX_TO_NIBBLE:
CMP# 41     ; Is it >= 'A'?
BCS  02     ; Yes, handle A-F
SBC# 2F     ; Convert '0'-'9' (subtract '0'-1)
RTS
SBC# 36     ; Convert 'A'-'F' (subtract 'A'-10-1)
RTS

@0600       ; Align ADVANCE_SOURCE routine
; Advance source pointer by 1
ADVANCE_SOURCE:
CLC
LDAZ 00
ADC# 01
STAZ 00
BCC  01     ; Skip if no carry
INCZ 01     ; Increment high byte
RTS

@0E00       ; Align WRITE_INST routine
; Write instruction to output
WRITE_INST:
LDY# 00     ; Initialize output index
LDAZ 0B     ; Get opcode
STIY 02     ; Write to (output),Y
INY         ; Next position

; Write operand bytes or NOPs based on type
LDAZ 0C     ; Get operand type
BEQ  02     ; Type 0: write 3 NOPs
JMP  0F40   ; Jump to type 0 handler (WRITE_NOPS)
CMP# 01     ; Type 1: write byte + 2 NOPs
BEQ  06     ; Yes, goto WRITE_BYTE
; Type 2 or 3: write 2 bytes + 1 NOP
LDAZ 09     ; Get low byte
STIY 02     ; Write it
INY         ; Next position
LDAZ 0A     ; Get high byte
STIY 02     ; Write it
INY         ; Next position
JMP  0F00   ; Jump to write final NOP (PAD_INST)

; WRITE_BYTE:
LDAZ 09     ; Get operand byte
STIY 02     ; Write it
INY         ; Next position
LDA# EA     ; NOP opcode
STIY 02     ; Write NOP
INY         ; Next position
JMP  0F00   ; Jump to write final NOP (PAD_INST)

@0F00       ; Align final NOP writing section
PAD_INST:
LDA# EA     ; NOP opcode
STIY 02     ; Write final NOP
; Advance output pointer by 4
CLC
LDAZ 02     ; Output pointer low
ADC# 04     ; Add 4
STAZ 02
BCC  01     ; Skip if no carry
INCZ 03     ; Increment high byte
JMP  0F80   ; Jump to end check (CHECK_END)

@0F40       ; Type 0 handler: write 3 NOPs
WRITE_NOPS:
LDA# EA     ; NOP opcode
STIY 02     ; Write first NOP
INY         ; Next position
LDA# EA     ; NOP opcode
STIY 02     ; Write second NOP
INY         ; Next position
LDA# EA     ; NOP opcode
STIY 02     ; Write third NOP
INY         ; Next position
; Advance output pointer by 4
CLC
LDAZ 02     ; Output pointer low
ADC# 04     ; Add 4
STAZ 02
BCC  01     ; Skip if no carry
INCZ 03     ; Increment high byte
JMP  0F80   ; Jump to end check (CHECK_END)

@0F80       ; Align end check section
; Check for END marker (special opcode $FF)
CHECK_END:
LDAZ 0B     ; Get opcode
CMP# FF     ; Is it END marker?
BEQ  02     ; Yes, jump to assembled code
JMP  0220   ; $0448: 4C 20 02 EA - No, continue assembly (MAIN_LOOP)

; Done! Jump to assembled program
JMP  8000   ; $044C: 4C 00 80 EA - Jump to assembled code at $8000

; Minimal opcode table - just what counter.punch needs
@1000
; Each entry: 4-byte mnemonic + 1-byte opcode + 1-byte type

; LDA# = $A9, type 1 (immediate byte)
"LDA#"
#A9
#01

; STAZ = $85, type 1 (zero page byte)
"STAZ"
#85
#01

; INCZ = $E6, type 1 (zero page byte)
"INCZ"
#E6
#01

; LDAZ = $A5, type 1 (zero page byte)
"LDAZ"
#A5
#01

; CMP# = $C9, type 1 (immediate byte)
"CMP#"
#C9
#01

; STAY = $99, type 2 (absolute,Y)
"STAY"
#99
#02

; STIY = $91, type 1 (indirect indexed,Y)
"STIY"
#91
#01

; CMPY = $D9, type 2 (absolute,Y)
"CMPY"
#D9
#02

; BNE  = $D0, type 3 (branch offset)
"BNE "
#D0
#03

; BRK  = $00, type 0 (no operand)
"BRK "
#00
#00

; END  = $FF, type 0 (special marker)
"END "
#FF
#00

; ADC# = $69, type 1 (immediate byte)
"ADC#"
#69
#01

; ASL  = $0A, type 0 (accumulator)
"ASL "
#0A
#00

; BCC  = $90, type 3 (branch offset)
"BCC "
#90
#03

; BCS  = $B0, type 3 (branch offset)
"BCS "
#B0
#03

; BEQ  = $F0, type 3 (branch offset)
"BEQ "
#F0
#03

; CLC  = $18, type 0 (no operand)
"CLC "
#18
#00

; CPY# = $C0, type 1 (immediate byte)
"CPY#"
#C0
#01

; INY  = $C8, type 0 (no operand)
"INY "
#C8
#00

; JMP  = $4C, type 2 (absolute address)
"JMP "
#4C
#02

; JSR  = $20, type 2 (absolute address)
"JSR "
#20
#02

; LDAY = $B1, type 1 (indirect indexed,Y)
"LDAY"
#B1
#01

; LDY# = $A0, type 1 (immediate byte)
"LDY#"
#A0
#01

; ORAZ = $05, type 1 (zero page byte)
"ORAZ"
#05
#01

; RTS  = $60, type 0 (no operand)
"RTS "
#60
#00

; SBC# = $E9, type 1 (immediate byte)
"SBC#"
#E9
#01

@1100       ; Gap filling routine - simplified approach
; Just copy target address to output pointer (skip actual filling for now)
SET_OUTPUT_PTR:
LDAZ 0A     ; Target low
STAZ 02     ; Set output pointer low
LDAZ 0B     ; Target high
STAZ 03     ; Set output pointer high
RTS         ; Return

@1200       ; @ directive handler
; Handle @xxxx - set effective address and fill gap
HANDLE_AT:
; Advance source pointer by 1 (skip '@')
CLC
LDAZ 00
ADC# 01
STAZ 00
BCC  01
INCZ 01

; Read 4 hex digits for address
JSR  0580   ; $05B8: 20 80 05 EA  - Read first byte (high)
STAZ 06     ; Store high byte
JSR  0580   ; $05C0: 20 80 05 EA  - Read second byte (low)
STAZ 07     ; Store low byte

; Calculate target address: $8000 + directive value
; Directive value is in $06 (high) and $07 (low)
; Target = $8000 + ($06 << 8) + $07
CLC
LDAZ 07     ; Get low byte of directive
ADC# 00     ; Add base address low ($8000 & $FF = $00)
STAZ 0A     ; Store target low byte
LDAZ 06     ; Get high byte of directive
ADC# 80     ; Add base address high ($8000 >> 8 = $80)
STAZ 0B     ; Store target high byte

; Fill gap with zeros from current output to target
; Current output is at ($02/$03), target at ($0A/$0B)
JSR  1100   ; Call gap filling routine (SET_OUTPUT_PTR)
JMP  0220   ; Back to main loop (MAIN_LOOP)

@1280       ; # hex data handler
; Handle #xx - read hex byte and write to output
HANDLE_HASH:
; Advance source pointer by 1 (skip '#')
CLC
LDAZ 00
ADC# 01
STAZ 00
BCC  01
INCZ 01

; Read hex byte and write to output
JSR  0580   ; $05F8: 20 80 05 EA  - Read hex byte
LDY# 00
STIY 02     ; Write to (output),Y

; Advance output pointer by 1
CLC
LDAZ 02
ADC# 01
STAZ 02
BCC  01
INCZ 03
JMP  0220   ; $061C: 4C 20 02 EA  - Back to main loop

@1300       ; " string data handler
; Handle "text" - read string until closing quote and write to output
HANDLE_STRING:
; Advance source pointer by 1 (skip opening '"')
CLC
LDAZ 00
ADC# 01
STAZ 00
BCC  01
INCZ 01
JMP  1320   ; Jump to STRING_LOOP

@1320       ; Align STRING_LOOP routine
; Read characters until closing quote
STRING_LOOP:
LDAY 00     ; Read character
CMP# 22     ; Is it '"'?
BEQ  0A     ; Yes, done with string

; Write character to output
LDY# 00
STIY 02     ; Write to (output),Y

; Advance both pointers
JSR  0600   ; $064C: 20 00 06 EA  - Advance source pointer
CLC         ; Advance output pointer
LDAZ 02
ADC# 01
STAZ 02
BCC  FA     ; Loop back to STRING_LOOP
INCZ 03
JMP  1320   ; $0668: 4C 20 13 EA  - Jump back to STRING_LOOP

; Done with string - advance past closing quote
JSR  0600   ; $066C: 20 00 06 EA  - Advance source pointer
JMP  0220   ; $0670: 4C 20 02 EA  - Back to main loop

; End of assembler program
END
