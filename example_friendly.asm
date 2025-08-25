; Example Program: Simple Calculator
; Adds two numbers and stores the result
; This demonstrates the "paper format" with human-readable comments

; Program constants
LDA# 2A     ; Load first number (42 decimal)
STA  80     ; Store in zero page for fast access

; Load second number
LDA# 1C     ; Load second number (28 decimal)
STA  81     ; Store in next zero page location

; Perform addition
CLC         ; Clear carry flag (good practice)
LDAZ 80     ; Load first number
ADC# 1C     ; Add second number (42 + 28 = 70 = $46)
STA  2000   ; Store result at $2000

; Display result in a loop (blinking light pattern)
; DISPLAY_LOOP: (main display loop starts here)
    LDA  2000   ; Load result
    STA  2100   ; Store to output port (hypothetical)

    ; Short delay loop
    LDX# FF     ; Load delay counter
; DELAY: (inner delay loop)
        DEX         ; Decrement X
        BNE  FE     ; Branch back if not zero (back 1 instruction to DEX)

    ; Clear display
    LDA# 00     ; Load zero
    STA  2100   ; Clear output port

    ; Another delay
    LDX# FF     ; Reload counter
; DELAY2: (second delay loop)
        DEX         ; Decrement
        BNE  FE     ; Branch back if not zero (to DEX above)

    ; Repeat forever - calculate offset to DISPLAY_LOOP
    ; From here back to "LDA 2000" is about 11 instructions * 4 bytes = 44 = $2C
    ; So we need BNE D4 (which is -44 in two's complement)
    JMP  2008   ; Jump back to start (absolute address)

; This would be the end in a real program
; BRK
; END
