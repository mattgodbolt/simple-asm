; Test file for data definitions
; This tests strings, hex data, and regular opcodes

; Simple program that loads a value
LDA# 42     ; Load 42
STA  2000   ; Store at $2000

; String data
"HELLO"

; Hex data
#DEADBEEF

; More code  
LDA# 00     ; Load 0
"WORLD"     ; Another string
#0102       ; More hex data
BRK         ; Stop
END         ; End marker