; Minimal 6502 Assembler Source Code
; Written in our restricted 4-byte instruction format
; Assembles programs from $1000 to $2000

; Entry point at $0200 - no relocation needed for the assembler itself
; Initialize source pointer to $1000
LDA# 00     ; $0200: A9 00 EA EA
STAZ 00     ; $0204: 85 00 EA EA  - Store to zero page $00
LDA# 10     ; $0208: A9 10 EA EA
STAZ 01     ; $020C: 85 01 EA EA  - Store to zero page $01

; Initialize output pointer to $2000
LDA# 00     ; $0210: A9 00 EA EA
STAZ 02     ; $0214: 85 02 EA EA  - Store to zero page $02
LDA# 20     ; $0218: A9 20 EA EA  
STAZ 03     ; $021C: 85 03 EA EA  - Store to zero page $03

; Main assembly loop
; Read 4-character opcode into buffer at $05-$08
; MAIN_LOOP:
LDY# 00     ; $0220: A0 00 EA EA  - Initialize index
; READ_OPCODE:
LDAY 00     ; $0224: B1 00 EA EA  - Read from (source),Y
STAY 05     ; $0228: 91 05 EA EA  - Store to opcode buffer,Y
INY         ; $022C: C8 EA EA EA  - Next character
CPY# 04     ; $0230: C0 04 EA EA  - Read 4 chars?
BNE  FD     ; $0234: D0 F4 EA EA  - Loop back 3 instructions

; Advance source pointer by 4
CLC         ; $0238: 18 EA EA EA
LDA  00     ; $023C: A5 00 EA EA
ADC# 04     ; $0240: 69 04 EA EA  
STAZ 00     ; $0244: 85 00 EA EA
BCC  02     ; $0248: 90 08 EA EA  - Skip if no carry
INC  01     ; $024C: E6 01 EA EA  - Increment high byte

; Skip spaces in source
; SKIP_SPACES:
LDAY 00     ; $0250: B1 00 EA EA  - Read current char
CMP# 20     ; $0254: C9 20 EA EA  - Is it space?
BNE  05     ; $0258: D0 14 EA EA  - No, continue to lookup
; Advance source pointer by 1
CLC         ; $025C: 18 EA EA EA
LDA  00     ; $0260: A5 00 EA EA
ADC# 01     ; $0264: 69 01 EA EA
STAZ 00     ; $0268: 85 00 EA EA
BCC  FA     ; $026C: 90 E8 EA EA  - Loop back to SKIP_SPACES
INC  01     ; $0270: E6 01 EA EA
JMP  F8     ; $0274: 4C 50 02 EA  - Jump back to SKIP_SPACES

; Look up opcode in table at $0500
; LOOKUP_OPCODE:
LDA# 00     ; $0278: A9 00 EA EA  - Table pointer low
STAZ 0E     ; $027C: 85 0E EA EA
LDA# 05     ; $0280: A9 05 EA EA  - Table pointer high  
STAZ 0F     ; $0284: 85 0F EA EA

; Compare current table entry with opcode buffer
; TABLE_LOOP:
LDY# 00     ; $0288: A0 00 EA EA  - Reset comparison index
; COMPARE_CHARS:
LDAY 0E     ; $028C: B1 0E EA EA  - Get table character
CMPY 05     ; $0290: D1 05 EA EA  - Compare with buffer char
BNE  0A     ; $0294: D0 28 EA EA  - No match, try next entry
INY         ; $0298: C8 EA EA EA  - Next character
CPY# 04     ; $029C: C0 04 EA EA  - All 4 chars checked?
BNE  FC     ; $02A0: D0 F0 EA EA  - Loop back to COMPARE_CHARS

; Found match! Extract opcode and type
LDY# 04     ; $02A4: A0 04 EA EA  - Point to opcode byte
LDAY 0E     ; $02A8: B1 0E EA EA  - Get opcode value
STAZ 0B     ; $02AC: 85 0B EA EA  - Store opcode
INY         ; $02B0: C8 EA EA EA  - Point to type byte
LDAY 0E     ; $02B4: B1 0E EA EA  - Get operand type
STAZ 0C     ; $02B8: 85 0C EA EA  - Store type
JMP  1A     ; $02BC: 4C 00 03 EA  - Jump to READ_OPERAND

; No match - advance to next table entry
; NEXT_ENTRY:
CLC         ; $02C0: 18 EA EA EA
LDA  0E     ; $02C4: A5 0E EA EA  - Table pointer low
ADC# 06     ; $02C8: 69 06 EA EA  - Each entry is 6 bytes
STAZ 0E     ; $02CC: 85 0E EA EA
BCC  02     ; $02D0: 90 08 EA EA  - Skip if no carry
INC  0F     ; $02D4: E6 0F EA EA  - Increment high byte

; Check for end of table
LDA  0F     ; $02D8: A5 0F EA EA
CMP# 06     ; $02DC: C9 06 EA EA  - Past $0600?
BCC  E9     ; $02E0: 90 A4 EA EA  - No, continue TABLE_LOOP
BRK         ; $02E4: 00 EA EA EA  - Error - opcode not found

; Read operand based on type in $0C
; READ_OPERAND:
LDA  0C     ; $0300: A5 0C EA EA  - Get operand type
BEQ  1E     ; $0304: F0 78 EA EA  - Type 0: no operand, goto WRITE_INST
CMP# 01     ; $0308: C9 01 EA EA  - Type 1: single byte
BEQ  04     ; $030C: F0 10 EA EA  - Yes, goto READ_BYTE
CMP# 02     ; $0310: C9 02 EA EA  - Type 2: two bytes  
BEQ  08     ; $0314: F0 20 EA EA  - Yes, goto READ_WORD
; Must be type 3: branch
JSR  3A     ; $0318: 20 5C 03 EA  - Call READ_BYTE
; Multiply by 4 for branch offset
LDA  09     ; $031C: A5 09 EA EA  - Get byte value
ASL         ; $0320: 0A EA EA EA  - Shift left (×2)
ASL         ; $0324: 0A EA EA EA  - Shift left (×4) 
STAZ 09     ; $0328: 85 09 EA EA  - Store result
JMP  14     ; $032C: 4C 7C 03 EA  - Jump to WRITE_INST

; Read single byte operand
; READ_BYTE:
JSR  2E     ; $0330: 20 5C 03 EA  - Call hex conversion
STAZ 09     ; $0334: 85 09 EA EA  - Store low byte
LDA# 00     ; $0338: A9 00 EA EA
STAZ 0A     ; $033C: 85 0A EA EA  - Clear high byte
JMP  10     ; $0340: 4C 7C 03 EA  - Jump to WRITE_INST

; Read two-byte operand (little-endian)
; READ_WORD:
JSR  26     ; $0344: 20 5C 03 EA  - Call hex conversion
STAZ 0A     ; $0348: 85 0A EA EA  - Store as high byte
JSR  22     ; $034C: 20 5C 03 EA  - Call hex conversion again  
STAZ 09     ; $0350: 85 09 EA EA  - Store as low byte
JMP  0B     ; $0354: 4C 7C 03 EA  - Jump to WRITE_INST

; Convert 2 hex digits to byte in A
; Advances source pointer by 2
; HEX_TO_BYTE:
LDAY 00     ; $0358: B1 00 EA EA  - Get first hex digit
JSR  12     ; $035C: 20 98 03 EA  - Convert to nibble
ASL         ; $0360: 0A EA EA EA  - Shift to high nibble
ASL         ; $0364: 0A EA EA EA
ASL         ; $0368: 0A EA EA EA
ASL         ; $036C: 0A EA EA EA
STAZ 0D     ; $0370: 85 0D EA EA  - Save high nibble
; Advance source pointer
JSR  15     ; $0374: 20 B8 03 EA  - Call ADVANCE_SOURCE
LDAY 00     ; $0378: B1 00 EA EA  - Get second hex digit
JSR  08     ; $037C: 20 98 03 EA  - Convert to nibble
ORA  0D     ; $0380: 05 0D EA EA  - Combine with high nibble
STAZ 04     ; $0384: 85 04 EA EA  - Store complete byte
JSR  0D     ; $0388: 20 B8 03 EA  - Advance source again
LDA  04     ; $038C: A5 04 EA EA  - Return byte in A
RTS         ; $0390: 60 EA EA EA

; Convert single hex ASCII char to nibble (0-F)
; Input: A = ASCII char, Output: A = nibble
; HEX_CHAR_TO_NIBBLE:
CMP# 41     ; $0394: C9 41 EA EA  - Is it >= 'A'?
BCS  04     ; $0398: B0 10 EA EA  - Yes, handle A-F
SBC# 2F     ; $039C: E9 2F EA EA  - Convert '0'-'9' (subtract '0'-1)
RTS         ; $03A0: 60 EA EA EA
SBC# 36     ; $03A4: E9 36 EA EA  - Convert 'A'-'F' (subtract 'A'-10-1)  
RTS         ; $03A8: 60 EA EA EA

; Advance source pointer by 1
; ADVANCE_SOURCE:
CLC         ; $03AC: 18 EA EA EA
LDA  00     ; $03B0: A5 00 EA EA
ADC# 01     ; $03B4: 69 01 EA EA
STAZ 00     ; $03B8: 85 00 EA EA
BCC  02     ; $03BC: 90 08 EA EA  - Skip if no carry
INC  01     ; $03C0: E6 01 EA EA  - Increment high byte
RTS         ; $03C4: 60 EA EA EA

; Write instruction to output
; WRITE_INST:
LDY# 00     ; $03C8: A0 00 EA EA  - Initialize output index
LDA  0B     ; $03CC: A5 0B EA EA  - Get opcode
STAY 02     ; $03D0: 91 02 EA EA  - Write to (output),Y
INY         ; $03D4: C8 EA EA EA  - Next position

; Write operand bytes or NOPs based on type
LDA  0C     ; $03D8: A5 0C EA EA  - Get operand type
BEQ  0A     ; $03DC: F0 28 EA EA  - Type 0: write 3 NOPs
CMP# 01     ; $03E0: C9 01 EA EA  - Type 1: write byte + 2 NOPs
BEQ  06     ; $03E4: F0 18 EA EA  - Yes, goto WRITE_BYTE
; Type 2 or 3: write 2 bytes + 1 NOP
LDA  09     ; $03E8: A5 09 EA EA  - Get low byte  
STAY 02     ; $03EC: 91 02 EA EA  - Write it
INY         ; $03F0: C8 EA EA EA  - Next position
LDA  0A     ; $03F4: A5 0A EA EA  - Get high byte
STAY 02     ; $03F8: 91 02 EA EA  - Write it  
INY         ; $03FC: C8 EA EA EA  - Next position
JMP  0A     ; $0400: 4C 1C 04 EA  - Jump to write final NOP

; WRITE_BYTE:
LDA  09     ; $0404: A5 09 EA EA  - Get operand byte
STAY 02     ; $0408: 91 02 EA EA  - Write it
INY         ; $040C: C8 EA EA EA  - Next position
LDA# EA     ; $0410: A9 EA EA EA  - NOP opcode
STAY 02     ; $0414: 91 02 EA EA  - Write NOP
INY         ; $0418: C8 EA EA EA  - Next position

; WRITE_NOPS:
LDA# EA     ; $041C: A9 EA EA EA  - NOP opcode  
STAY 02     ; $0420: 91 02 EA EA  - Write final NOP
; Advance output pointer by 4
CLC         ; $0424: 18 EA EA EA
LDA  02     ; $0428: A5 02 EA EA  - Output pointer low
ADC# 04     ; $042C: 69 04 EA EA  - Add 4
STAZ 02     ; $0430: 85 02 EA EA
BCC  02     ; $0434: 90 08 EA EA  - Skip if no carry
INC  03     ; $0438: E6 03 EA EA  - Increment high byte

; Check for END marker (special opcode $FF)
LDA  0B     ; $043C: A5 0B EA EA  - Get opcode
CMP# FF     ; $0440: C9 FF EA EA  - Is it END marker?
BEQ  02     ; $0444: F0 08 EA EA  - Yes, jump to assembled code
JMP  0220   ; $0448: 4C 20 02 EA - No, continue assembly

; Done! Jump to assembled program
JMP  2000   ; $044C: 4C 00 20 EA

; Minimal opcode table - just what counter.punch needs
@0500
; LDA# = $A9, type 1 (immediate byte)
#4C444123A901
; STAZ = $85, type 1 (zero page byte) 
#5354415A8501
; INCZ = $E6, type 1 (zero page byte)
#494E435AE601
; LDAZ = $A5, type 1 (zero page byte)
#4C44415AA501
; CMP# = $C9, type 1 (immediate byte)
#434D5023C901
; BNE  = $D0, type 3 (branch offset)
#424E4520D003
; BRK  = $00, type 0 (no operand)
#42524B200000
; END  = $FF, type 0 (special marker)
#454E4420FF00