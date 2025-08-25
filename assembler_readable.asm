; Minimal 6502 Assembler Source Code - Readable Version
; Written in our restricted 4-byte instruction format
; Handles newlines and whitespace properly

; Entry point at $0200 - Initialize source pointer to $1000
LDA# 00
STAZ 00
LDA# 10
STAZ 01

; Initialize output pointer to $2000
LDA# 00
STAZ 02
LDA# 20
STAZ 03

; Main assembly loop
MAIN_LOOP:
    ; Skip any leading whitespace
    JSR  SKIP_SPACES

    ; Read opcode (up to 4 chars or until whitespace)
    LDY# 00
    LDX# 00

READ_OPCODE_LOOP:
    LDAY 00     ; Read character from source
    CMP# 20     ; Space?
    BEQ  OPCODE_DONE
    CMP# 0A     ; Newline?
    BEQ  OPCODE_DONE
    CMP# 0D     ; Carriage return?
    BEQ  OPCODE_DONE
    CMP# 09     ; Tab?
    BEQ  OPCODE_DONE
    CMP# 00     ; End of source?
    BEQ  ASSEMBLY_DONE

    ; Store character in opcode buffer
    STAX 05
    INX
    JSR  ADVANCE_SOURCE
    CPX# 04     ; Read 4 chars max
    BNE  READ_OPCODE_LOOP

OPCODE_DONE:
    ; Pad opcode buffer to 4 chars with spaces
PAD_LOOP:
    CPX# 04
    BEQ  OPCODE_READY
    LDA# 20     ; Space character
    STAX 05
    INX
    JMP  PAD_LOOP

OPCODE_READY:
    ; Skip whitespace after opcode
    JSR  SKIP_SPACES

    ; Look up opcode in table
    JSR  LOOKUP_OPCODE

    ; Read operand based on type
    LDA  0C     ; Get operand type
    BEQ  NO_OPERAND
    CMP# 01
    BEQ  READ_BYTE_OPERAND
    CMP# 02
    BEQ  READ_WORD_OPERAND
    ; Must be type 3 - branch
    JSR  READ_HEX_BYTE
    ; Multiply by 4
    LDA  09
    ASL
    ASL
    STAZ 09
    JMP  WRITE_INSTRUCTION

READ_BYTE_OPERAND:
    JSR  READ_HEX_BYTE
    LDA# 00
    STAZ 0A
    JMP  WRITE_INSTRUCTION

READ_WORD_OPERAND:
    JSR  READ_HEX_WORD
    ; Store as little-endian
    STAZ 0A     ; High byte
    JSR  READ_HEX_WORD
    STAZ 09     ; Low byte
    JMP  WRITE_INSTRUCTION

NO_OPERAND:
    LDA# 00
    STAZ 09
    STAZ 0A

WRITE_INSTRUCTION:
    ; Skip any trailing whitespace after operand
    JSR  SKIP_SPACES

    ; Check for END marker
    LDA  0B
    CMP# FF
    BEQ  ASSEMBLY_DONE

    ; Write 4-byte instruction
    LDY# 00
    LDA  0B     ; Opcode
    STAY 02
    INY

    ; Write operand bytes based on type
    LDA  0C
    BEQ  WRITE_NOPS_ALL
    CMP# 01
    BEQ  WRITE_BYTE_AND_NOPS
    ; Type 2 or 3 - write 2 bytes + 1 NOP
    LDA  09
    STAY 02
    INY
    LDA  0A
    STAY 02
    INY
    JMP  WRITE_FINAL_NOP

WRITE_BYTE_AND_NOPS:
    LDA  09
    STAY 02
    INY
    LDA# EA
    STAY 02
    INY
    JMP  WRITE_FINAL_NOP

WRITE_NOPS_ALL:
    LDA# EA
    STAY 02
    INY
    LDA# EA
    STAY 02
    INY

WRITE_FINAL_NOP:
    LDA# EA
    STAY 02

    ; Advance output pointer by 4
    CLC
    LDA  02
    ADC# 04
    STAZ 02
    BCC  CONTINUE_MAIN
    INC  03

CONTINUE_MAIN:
    JMP  MAIN_LOOP

ASSEMBLY_DONE:
    JMP  2000   ; Jump to assembled program

; Subroutines
SKIP_SPACES:
    LDAY 00
    CMP# 20     ; Space
    BEQ  SKIP_ONE
    CMP# 0A     ; Newline
    BEQ  SKIP_ONE
    CMP# 0D     ; CR
    BEQ  SKIP_ONE
    CMP# 09     ; Tab
    BEQ  SKIP_ONE
    RTS
SKIP_ONE:
    JSR  ADVANCE_SOURCE
    JMP  SKIP_SPACES

ADVANCE_SOURCE:
    CLC
    LDA  00
    ADC# 01
    STAZ 00
    BCC  ADV_DONE
    INC  01
ADV_DONE:
    RTS

READ_HEX_BYTE:
    JSR  SKIP_SPACES
    ; Read first hex digit
    LDAY 00
    JSR  HEX_TO_NIBBLE
    ASL
    ASL
    ASL
    ASL
    STAZ 0D
    JSR  ADVANCE_SOURCE
    ; Read second hex digit
    LDAY 00
    JSR  HEX_TO_NIBBLE
    ORA  0D
    STAZ 09
    JSR  ADVANCE_SOURCE
    RTS

READ_HEX_WORD:
    JSR  READ_HEX_BYTE
    LDA  09
    STAZ 0D     ; Save first byte
    JSR  READ_HEX_BYTE
    LDA  09     ; Second byte in A
    LDX  0D     ; First byte in X
    RTS

HEX_TO_NIBBLE:
    CMP# 41     ; 'A'
    BCS  HEX_LETTER
    SEC
    SBC# 30     ; '0'
    RTS
HEX_LETTER:
    SEC
    SBC# 37     ; 'A' - 10
    RTS

LOOKUP_OPCODE:
    ; Table lookup logic - simplified for readability
    ; Compare opcode buffer with table entries
    ; Return opcode byte in $0B and type in $0C
    ; (Implementation would be similar to original but cleaner)
    RTS

END
