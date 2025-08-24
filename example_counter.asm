; Classic Counter Example
; Counts from 0 to 10 and stops
; Shows typical early computer program structure

; Initialize counter to zero
LDA# 00     ; A = 0
STAZ 80     ; counter = 0 (store in zero page)

; Main counting loop
; LOOP: (branch target for BNE instruction below)
    ; Increment and check
    INCZ 80     ; counter++
    LDAZ 80     ; A = counter
    CMP# 0A     ; compare with 10
    BNE  FB     ; if A != 10, go back 5 instructions to INCZ
    
; Counter reached 10 - we're done
BRK         ; Stop execution
END         ; End of source code