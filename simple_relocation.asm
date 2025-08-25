!1E00        ; Set offset: 2000 - 0200 = 1E00
@0200        ; Start at effective address 0200
LDA# 42      ; Load 42
BRK          ; Stop
@0210        ; Skip forward
LDX# FF      ; Another instruction
END          ; End marker
