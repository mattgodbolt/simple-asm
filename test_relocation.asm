; Test file for relocation directives
; Assembles at 2000 but effective address starts at 0200

!1E00        ; Set offset: 2000 - 0200 = 1E00
@0200        ; Start at effective address 0200

; Code section at 0200
LDA# 42      ; Load 42
STA  2000    ; Store at 2000 (absolute address)
JMP  0250    ; Jump within our code

@0250        ; Continue at 0250
LDX# FF      ; Load counter
"MSG1"       ; String data inline

@0280        ; Jump forward, leaving gap
BRK          ; Stop
END          ; End marker

@0400        ; Table section at 0400
"HELLO"      ; String
#DEADBEEF    ; Hex data