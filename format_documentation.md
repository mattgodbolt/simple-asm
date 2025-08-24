# Assembly Format Documentation

## Historical Context: Paper to Punch Cards

This project mirrors the historical process of early computing where programmers would:

1. **Write on paper** - Human-readable source with comments, formatting, and documentation
2. **Transfer to punch cards** - Machine-readable format with strict constraints
3. **Feed to computer** - Rigid format required by primitive input systems

Our system recreates this workflow with two distinct formats.

## Paper Format (Friendly Assembly)

This is what you'd write by hand or type for human consumption:

```assembly
; Simple counter program
; Counts from 0 to 10 and stops

LDA# 00     ; Initialize accumulator to 0
STA  80     ; Store in zero page location $80

; Main loop starts here  
LOOP:
    INCZ 80     ; Increment the counter
    LDAZ 80     ; Load counter value
    CMP# 0A     ; Compare with 10
    BNE  FB     ; Branch back if not equal (back 5 instructions)

; Done counting
BRK         ; Stop program
END         ; End of source
```

### Paper Format Features:
- **Comments**: Lines starting with `;` are ignored
- **Inline comments**: Everything after `;` on a line is ignored  
- **Flexible whitespace**: Blank lines, indentation, spacing for readability
- **Labels**: `LOOP:` (conceptual - not implemented in minimal version)
- **Mixed case**: `lda#`, `LDA#`, `Lda#` all accepted
- **Flexible operands**: `$42`, `42`, `0x42` all mean hex 42

## Punch Card Format (Machine Input)

This is what gets fed to the 6502 assembler:

```
LDA#00
STAZ80
INCZ80
LDAZ80
CMP#0A
BNE FB
BRK 
END 
```

### Punch Card Format Requirements:
- **No comments**: All `;` content stripped
- **One instruction per line**: Each instruction on its own line
- **Exact opcodes**: Must be exactly 4 characters (space-padded)
- **Uppercase hex**: All operands in uppercase
- **No blank lines**: Only instruction lines
- **Minimal whitespace**: No spaces between opcode and operand

## Format Comparison

| Feature | Paper Format | Punch Card Format |
|---------|-------------|-------------------|
| Comments | ✓ Supported | ✗ Stripped |
| Blank lines | ✓ Ignored | ✗ Not allowed |
| Whitespace | ✓ Flexible | ✗ Minimal |
| Opcode length | ✓ 1-4 chars | ✗ Exactly 4 chars |
| Case sensitivity | ✓ Any case | ✗ Uppercase only |
| Line structure | ✓ Flexible | ✓ One instruction per line |
| Human readable | ✓ Very | ✓ Somewhat |

## The Conversion Process

Use `punch_card_formatter.py` to convert between formats:

```bash
# Convert friendly source to punch card format
python punch_card_formatter.py program.asm program.punch

# Create 80-column cards (historical punch card format)
python punch_card_formatter.py --80col program.asm program.cards

# Verify both produce same machine code
python punch_card_formatter.py --verify program.asm program.punch
```

## Why This Approach?

### Historical Accuracy
Real programmers in the 1960s-70s followed this exact workflow:
- Write readable source on coding sheets
- Keypunch operators converted to punch cards
- Cards fed to assemblers with rigid parsing

### Practical Benefits
- **Development**: Use friendly format with comments and formatting
- **Bootstrap**: Convert to minimal format for hand-assembly
- **Testing**: Verify both produce identical results
- **Education**: Shows constraints of early computing

### Modern Parallel
This mirrors modern development:
- **Source code**: Human-readable with comments
- **Minification**: Compressed for transmission/storage  
- **Compilation**: Machine-readable output

## Example Workflow

1. **Write program** in friendly format:
   ```assembly
   ; This is my program
   LDA# 42    ; Load the answer
   STA  2000  ; Store it somewhere
   BRK        ; All done
   END
   ```

2. **Convert to punch cards**:
   ```
   LDA#42
   STA 2000
   BRK 
   END 
   ```

3. **Hand-assemble** the punch card format using our 6502 assembler

4. **Run** the resulting machine code

## Size Constraints

Our minimal 6502 assembler has strict memory limits:
- **Source input**: $1000-$1FFF (4KB max)
- **Machine output**: $2000-$2FFF (4KB max)  
- **Assembler code**: ~600 bytes

The punch card format maximizes use of this limited space by eliminating all non-essential characters.

## Testing Both Formats

Both the Python assembler (friendly format) and our 6502 assembler (punch card format) should produce identical machine code:

```bash
# Assemble with Python (friendly format)  
python simple_asm.py program.asm

# Convert and assemble with 6502 format
python punch_card_formatter.py program.asm program.punch
python simple_asm.py program.punch

# Results should be byte-for-byte identical
```

This proves our bootstrap process is correct - the hand-assembled 6502 assembler will produce the same results as our reference implementation.