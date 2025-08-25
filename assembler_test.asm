; Test: Can our assembler assemble a simple program?
; This should produce the same output as the Python version

LDA# 42
STA  2100
LDA# 0D
ADC# 1D
STA  2101
INX
DEX
TAX
TXA
JMP  2020
BEQ  FE
BNE  02
BRK
END
