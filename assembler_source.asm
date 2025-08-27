; Minimal 6502 Assembler Source Code
; Written using native 6502 instruction formats
; Reads source from $2000, assembles to $8000
;
; CODING STANDARDS FOLLOWED:
; - Memory alignment: All jump targets and data aligned with @xxxx directives
; - Control flow: Always use labels for all branch/jump targets (BEQ :SKIP, etc.)
; - Documentation: Comments describe intent and memory layout, not machine code bytes
; - Address loading: High/low byte loads clearly documented with table references

!0000        ; Code assembled to $8000 but runs as if at $0000
@0200        ; Entry point at $0200
; Initialize source pointer to $2000
LDA# 00     ; Low byte of source at $2000
STAZ 00     ; Store to zero page $00
LDA# 20     ; High byte of source at $2000
STAZ 01     ; Store to zero page $01

; Initialize output pointer to $8000
LDA# 00     ; Low byte of output at $8000
STAZ 02     ; Store to zero page $02
LDA# 80     ; High byte of output at $8000
STAZ 03     ; Store to zero page $03

; Initialize effective PC to $8000 (same as output initially)
LDA# 00     ; Low byte of effective PC at $8000
STAZ 10     ; Store to zero page $10 (effective PC low)
LDA# 80     ; High byte of effective PC at $8000
STAZ 11     ; Store to zero page $11 (effective PC high)

JMP  :MAIN_LOOP   ; Jump to main loop

; Main assembly loop
; Read 4-character opcode into buffer at $05-$08
MAIN_LOOP:
LDY# 00     ; Reset Y to 0
LDAY 00     ; Peek at first character
CMP# 21     ; Is it '!' ($21)?
BNE  :SKIP_EXCLAMATION     ; Not !, skip to next check
; Fall through to HANDLE_EXCLAMATION

; Handler moved here from $1380 to be within branch range
HANDLE_EXCLAMATION:
; Advance source pointer by 1 (skip '!')
JSR  :ADVANCE_SOURCE

; Read 4 hex digits for new effective address
JSR  :HEX_TO_BYTE   ; Read first byte (high)
STAZ 06     ; Store high byte
JSR  :HEX_TO_BYTE   ; Read second byte (low)
STAZ 07     ; Store low byte

; Set effective address directly (! sets where code thinks it's running)
; Effective address is in $06 (high) and $07 (low)
; This is used for relocation - code may be stored at $8000 but run at $0000
; Unlike @, this doesn't change the output pointer, only the effective PC
LDAZ 07     ; Get low byte of directive
STAZ 10     ; Store as effective PC low (using $10-11 for effective PC)
LDAZ 06     ; Get high byte of directive
STAZ 11     ; Store as effective PC high

; Skip newline after directive
JSR  :ADVANCE_SOURCE
JMP  :MAIN_LOOP   ; Back to main loop

SKIP_EXCLAMATION:
CMP# 40     ; Is it '@' ($40)?
BNE  :SKIP_AT     ; Not @, skip to next check
; Fall through to HANDLE_AT

; Handler moved here from $1200 to be within branch range
HANDLE_AT:
; Advance source pointer by 1 (skip '@')
JSR  :ADVANCE_SOURCE

; Read 4 hex digits for target effective address
JSR  :HEX_TO_BYTE   ; Read first byte (high)
STAZ 06     ; Store high byte
JSR  :HEX_TO_BYTE   ; Read second byte (low)
STAZ 07     ; Store low byte

; Calculate target output address
; If !0000 was used, we're assembling at $8000 but code thinks it's at $0000
; So @0200 means advance to output $8200 (which is $8000 + $0200)
CLC
LDAZ 07     ; Get low byte of target effective
ADC# 00     ; Add output base low ($8000 & $FF = $00)
STAZ 02     ; Update output pointer low directly
LDAZ 06     ; Get high byte of target effective
ADC# 80     ; Add output base high ($8000 >> 8 = $80)
STAZ 03     ; Update output pointer high directly

; Update effective PC to target
LDAZ 07
STAZ 10     ; Update effective PC low
LDAZ 06
STAZ 11     ; Update effective PC high

; Skip newline after directive
JSR  :ADVANCE_SOURCE
JMP  :MAIN_LOOP   ; Back to main loop

SKIP_AT:
CMP# 23     ; Is it '#' ($23)?
BNE  :SKIP_HASH     ; Not #, skip to next check
; Fall through to HANDLE_HASH

; Handler moved here from $1280 to be within branch range
HANDLE_HASH:
; Advance source pointer by 1 (skip '#')
JSR  :ADVANCE_SOURCE

; Read hex byte and write to output
JSR  :HEX_TO_BYTE   ; Read hex byte
LDY# 00
STIY 02     ; Write to (output),Y

; Advance output pointer by 1
JSR  :ADVANCE_OUTPUT
JMP  :MAIN_LOOP   ; Back to main loop

SKIP_HASH:
CMP# 22     ; Is it '"' ($22)?
BNE  :SKIP_STRING     ; Not ", skip to next check
; Fall through to HANDLE_STRING

; Handler moved here from $1300 to be within branch range
HANDLE_STRING:
; Advance source pointer by 1 (skip opening '"')
JSR  :ADVANCE_SOURCE
JMP  :STRING_LOOP   ; Jump to STRING_LOOP

SKIP_STRING:
JMP  :CHAR_HANDLER   ; None of the above, handle as opcode

; Skip spaces and newlines then read 4-character opcode
CHAR_HANDLER:
LDAY 00     ; Read current char (Y already 0 from main loop)
CMP# 20     ; Is it space?
BEQ  :SKIP_ADVANCE   ; Yes, advance pointer
CMP# 0A     ; Is it newline?
BNE  :READ_OPCODE   ; No, start reading opcode
SKIP_ADVANCE:
JSR  :ADVANCE_SOURCE   ; Advance source pointer by 1
JMP  :MAIN_LOOP   ; Jump back to check for special chars

; Read 4 characters into buffer
READ_OPCODE:
LDY# 00     ; Initialize index
READ_CHAR:
LDAY 00     ; Read from (source),Y
STAY 0005   ; Store to buffer at $0005,Y
INY         ; Next character
CPY# 04     ; Read 4 chars?
BNE  :READ_CHAR   ; Loop back to read next char

; Advance source pointer by 4 - using optimized subroutine
JSR  :ADVANCE_SOURCE_BY_4
JMP  :LOOKUP_TABLE   ; Jump to table lookup

; Look up opcode in table at $1000
LOOKUP_TABLE:
LDA# 00     ; Low byte of opcode table at $1000
STAZ 0E
LDA# 10     ; High byte of opcode table at $1000
STAZ 0F

; Compare current table entry with opcode buffer
TABLE_LOOP:
LDY# 00     ; Reset comparison index
COMPARE_CHARS:
LDAY 0E     ; Get table character
CMPY 0005   ; Compare with buffer char at $0005,Y
BNE  :NEXT_ENTRY   ; No match, try next entry
INY         ; Next character
CPY# 04     ; All 4 chars checked?
BNE  :COMPARE_CHARS   ; Loop back to COMPARE_CHARS

; Found match! Extract opcode and type
LDY# 04     ; Point to opcode byte
LDAY 0E     ; Get opcode value
STAZ 0B     ; Store opcode
; Check for END marker before writing
CMP# FF     ; Is it END marker?
BEQ  :END_FOUND   ; Yes, jump to assembled code
INY         ; Point to type byte
LDAY 0E     ; Get operand type
STAZ 0C     ; Store type
; Skip space between opcode and operand
LDY# 00     ; Reset Y to 0
LDAY 00     ; Get character at source pointer
CMP# 20     ; Is it a space?
BNE  :SKIP_SPACE_ADVANCE     ; No, skip advance
JSR  :ADVANCE_SOURCE   ; Yes, advance source pointer
SKIP_SPACE_ADVANCE:
JMP  :READ_OPERAND   ; Jump to READ_OPERAND

; No match - advance to next table entry
NEXT_ENTRY:
CLC
LDAZ 0E     ; Table pointer low
ADC# 06     ; Each entry is 6 bytes
STAZ 0E
BCC  :SKIP_TABLE_INC     ; Skip if no carry
INCZ 0F     ; Increment high byte
SKIP_TABLE_INC:

; Check for end of table
LDAZ 0F
CMP# 11     ; Past OPCODE_TABLE end?
BCC  :TABLE_LOOP   ; No, continue TABLE_LOOP
BRK         ; Error - opcode not found

END_FOUND:
JMP  8000   ; Jump to assembled code at $8000

; Read operand based on type in $0C
READ_OPERAND:
LDAZ 0C     ; Get operand type
BNE  :CHECK_TYPE_1   ; Not 0, check other types
JMP  :WRITE_INST   ; Type 0: jump to WRITE_INST
CHECK_TYPE_1:
CMP# 01     ; Type 1: single byte
BNE  :CHECK_TYPE_2   ; Not 1, check type 2
JSR  :READ_BYTE   ; Type 1: call READ_BYTE
JMP  :WRITE_INST   ; Jump to WRITE_INST
CHECK_TYPE_2:
CMP# 02     ; Type 2: two bytes
BNE  :TYPE_3_BRANCH   ; Not 2, must be type 3
JMP  :READ_WORD   ; Type 2: jump to READ_WORD
TYPE_3_BRANCH:
; Must be type 3: branch
JSR  :READ_BYTE   ; Call READ_BYTE
JMP  :WRITE_INST   ; Jump to WRITE_INST

; Read single byte operand
READ_BYTE:
JSR  :HEX_TO_BYTE   ; Call hex conversion
STAZ 09     ; Store low byte
LDA# 00
STAZ 0A     ; Clear high byte
RTS         ; Return to caller

; Read two-byte operand (little-endian)
READ_WORD:
JSR  :HEX_TO_BYTE   ; Call hex conversion
STAZ 0A     ; Store as high byte
JSR  :HEX_TO_BYTE   ; Call hex conversion again
STAZ 09     ; Store as low byte
JMP  :WRITE_INST   ; Jump to WRITE_INST

; Convert 2 hex digits to byte in A
; Advances source pointer by 2
HEX_TO_BYTE:
LDY# 00     ; Reset Y to 0
LDAY 00     ; Get first hex digit
JSR  :HEX_TO_NIBBLE   ; Convert to nibble
ASL         ; Shift to high nibble (×16)
ASL
ASL
ASL
STAZ 0D     ; Save high nibble
JSR  :ADVANCE_SOURCE   ; Advance to second digit
LDAY 00     ; Get second hex digit (Y still 0)
JSR  :HEX_TO_NIBBLE   ; Convert to nibble
ORAZ 0D     ; Combine with high nibble
STAZ 04     ; Store complete byte
JSR  :ADVANCE_SOURCE   ; Advance past second digit
LDAZ 04     ; Load result into A before return
RTS

; Convert single hex ASCII char to nibble (0-F)
; Input: A = ASCII char, Output: A = nibble
HEX_TO_NIBBLE:
CMP# 41     ; Is it >= 'A'?
BCS  :HEX_LETTER ; Yes, handle A-F
SBC# 2F     ; Convert '0'-'9' (subtract '0'-1)
RTS
HEX_LETTER:
CLC         ; Clear carry for proper subtraction
SBC# 36     ; Convert 'A'-'F' (subtract 'A'-10-1)
RTS

; Advance source pointer by 1
ADVANCE_SOURCE:
CLC
LDAZ 00
ADC# 01
STAZ 00
BCC  :SKIP_SOURCE_INC     ; Skip if no carry
INCZ 01     ; Increment high byte
SKIP_SOURCE_INC:
RTS


; Advance output pointer by 1
ADVANCE_OUTPUT:
CLC
LDAZ 02
ADC# 01
STAZ 02
BCC  :SKIP_OUTPUT_INC     ; Skip if no carry
INCZ 03     ; Increment high byte
SKIP_OUTPUT_INC:
RTS

; Advance source pointer by 4 - optimized version of 4x JSR :ADVANCE_SOURCE
ADVANCE_SOURCE_BY_4:
CLC
LDAZ 00     ; Get source pointer low byte
ADC# 04     ; Add 4
STAZ 00     ; Store back
BCC  :SKIP_SOURCE_BY_4_INC  ; Skip if no carry
INCZ 01     ; Increment high byte
SKIP_SOURCE_BY_4_INC:
RTS

; Write instruction to output
WRITE_INST:
LDY# 00     ; Initialize output index
LDAZ 0B     ; Get opcode
STIY 02     ; Write to (output),Y
INY         ; Next position

; Write operand bytes based on type
LDAZ 0C     ; Get operand type
BEQ  :FINISH_INST   ; Type 0: no operands, finish
CMP# 01     ; Type 1: write single byte
BEQ  :WRITE_BYTE   ; Yes, goto WRITE_BYTE
CMP# 03     ; Type 3: branch with offset
BEQ  :WRITE_BYTE   ; Same as type 1 - single byte
; Type 2: write 2 bytes
LDAZ 09     ; Get low byte
STIY 02     ; Write it
INY         ; Next position
LDAZ 0A     ; Get high byte
STIY 02     ; Write it
JMP  :FINISH_INST   ; Finish instruction

WRITE_BYTE:
LDAZ 09     ; Get operand byte
STIY 02     ; Write it
; Fall through to FINISH_INST

FINISH_INST:
; Advance output pointer by actual instruction length based on operand type
; Type 0 (BRK): 1 byte
; Type 1/3 (LDA# 42, BNE 03): 2 bytes
; Type 2 (JMP 1234): 3 bytes
LDAZ 0C     ; Get operand type
BEQ  :ADVANCE_1     ; Type 0: advance by 1
CMP# 02     ; Type 2?
BEQ  :ADVANCE_3     ; Type 2: advance by 3
; Type 1/3: advance by 2
JSR  :ADVANCE_OUTPUT
ADVANCE_1:
JSR  :ADVANCE_OUTPUT
JMP  :MAIN_LOOP   ; Jump to main loop

ADVANCE_3:
JSR  :ADVANCE_OUTPUT
JSR  :ADVANCE_OUTPUT
JSR  :ADVANCE_OUTPUT
JMP  :MAIN_LOOP   ; Jump to main loop

; Done! Jump to assembled program would be here, but now handled earlier

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

@1100       ; STRING_LOOP moved here from $1320
; Read characters until closing quote
STRING_LOOP:
LDY# 00     ; Reset Y to 0
LDAY 00     ; Read character
CMP# 22     ; Is it '"'?
BEQ  :STRING_DONE   ; Yes, done with string

; Write character to output
STIY 02     ; Write to (output),Y

; Advance both pointers
JSR  :ADVANCE_SOURCE   ; Advance source pointer
JSR  :ADVANCE_OUTPUT
JMP  :STRING_LOOP   ; Jump back to STRING_LOOP

STRING_DONE:
; Done with string - advance past closing quote
JSR  :ADVANCE_SOURCE   ; Advance source pointer
JMP  :MAIN_LOOP   ; Back to main loop

; Handlers have been moved inline with main loop for branch optimization
; This space now available for future use

; End of assembler program
END
