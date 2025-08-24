# Bootstrapping a Computer - Script Outline (Revised)

*[Estimated 20-25 minutes total recording time]*

## Opening Hook (2-3 mins)
"Right, so in my previous videos I've talked about this robot executing simple instructions - numbers in boxes, machine code, all that good stuff. But there's something I've completely glossed over..."

*[Draw the familiar robot-and-boxes diagram]*

"How do the numbers get in the boxes in the first place?"

*[Pause for effect - this is where Sean might ask "Well, how DO they get there?"]*

"Well, that's the bootstrap problem. It's a proper chicken-and-egg situation. You need a program to load programs, but how do you load the program that loads programs?"

## The Punch Card Reader Solution (5-6 mins)
"So let's solve this step by step. We need some way to get data into the computer that doesn't involve us typing in thousands of numbers by hand."

*[Draw a simple punch card reader setup]*

"Enter the punch card reader! Now, here's the clever bit. We write one tiny program - just once - that knows how to read punch cards and stuff the data into memory."

*[Show the concept of a simple loader loop]*
"Read byte from card, store in memory, increment memory pointer, repeat until done. Maybe 20 lines of code, tops."

*[Sean might ask "But how do you get THAT program into the computer?"]*

"Ah, well... we cheat a bit. Either we have a tiny ROM with this program burned in, or we use front panel switches like on the old Altair 8800 to toggle it in by hand. Point is, we do this horrible job exactly once."

*[Draw the ROM or front panel concept]*

"Once that's done, we can load much longer programs from punch cards. Brilliant!"

## But It's Still Painful (4-5 mins)
"Right, so now we can input longer programs. But look what we're actually putting on these cards..."

*[Show a simple program as raw hex]*
```
A9 2A    ; What's this supposed to be?
69 0D    ; No idea without looking it up
8D 00 02 ; Absolute gibberish to humans
```

"This is our simple 'add two numbers' program. A9 2A means 'load 42 into the A register', 69 0D means 'add 13 to it'... but you'd never know that from looking at it!"

*[Natural place for Sean to ask "This is still pretty tedious, isn't it?"]*

"Exactly! We've solved the input problem, but we're still having to look up every single instruction in a manual and convert it to hex by hand. Make one mistake and your program crashes in mysterious ways."

*[Show the pain of debugging hex code]*

"There's got to be a better way..."

## Enter the Minimal Assembler (6-7 mins)
"So let's write an assembler! Something that lets us write 'LDA' instead of having to remember that's opcode A9."

"But here's the thing - we need to write this assembler using our punch card system, which means we're writing it in raw hex. So it needs to be as simple as humanly possible."

*[Show the 4-character mnemonic idea]*
```
LDA# 042  ; Load immediate 42 (padded to 3 bytes total)
ADC# 013  ; Add immediate 13
STA  200  ; Store to absolute address 200  
JMP  -03  ; Jump back 3 instructions
```

"See what we've done? Every instruction is exactly 4 characters followed by exactly 3 bytes. No variable-length instructions, no complex addressing modes to parse."

*[Show how the table lookup would work]*
"The assembler just needs a table: LDA# maps to A9, ADC# maps to 69, STA maps to 8D..."

"And because everything's the same length, we can do relative jumps by instruction count. Jump back 3 instructions? That's just subtract 9 bytes from the current address."

*[Sean might ask "How complex is this assembler to write?"]*

"Still quite fiddly! You need to scan through text, do string comparisons, convert decimal numbers to hex... but it's manageable. Maybe a few hundred bytes of machine code."

## Writing the Assembler By Hand (3-4 mins)
*[Show a snippet of what the assembler looks like in hex]*

"So we bite the bullet and write this thing by hand. Painful, but doable. And once it's working..."

*[Show the same program in the 4-character assembly format]*
```
LDA# 042
ADC# 013  
STA  200
```

"Suddenly we can write programs that humans can actually read! And debug! And maintain!"

## The Second Bootstrap (3-4 mins)
"But we're not done. Now we can write a better assembler using our simple one."

*[Show progression]*
"We write a fancier assembler - one that handles proper 6502 addressing modes, labels, variable-length instructions, all the good stuff. But we write it in our simple 4-character assembly language."

"So we feed our new assembler's source code through our old assembler, and out pops a better assembler!"

*[Natural place for "And then what?"]*

"Well, then we write a compiler. In proper assembly language this time. And once we've got a compiler working, we can rewrite it in its own language..."

## The Endless Ladder (2-3 mins)
*[Draw the ladder concept - each tool building the next]*

"This is how we got from front panel switches to modern IDEs. Each generation of tools builds the next generation."

*[Show the progression: ROM/switches → punch card loader → simple assembler → better assembler → compiler → high-level languages]*

"The beautiful thing is, this actually happened! The first FORTRAN compiler was written by hand in assembly language. The first C compiler was written in assembly. Then they rewrote it in C."

## Wrap-up (1-2 mins)
"So that's bootstrapping - it's turtles all the way up! Each level of abstraction is built using the tools from the level below."

"And the next time someone asks you how programs get into computers, you can tell them: very carefully, one bootstrap at a time."

*[Final pause for any closing questions from Sean]*

---

## Notes for Matt:
- Start with solving the input problem directly - more logical flow
- Keep the hex examples short but concrete
- The 4-character thing is still the memorable hook
- Show just enough assembler complexity to be believable
- Natural progression from "this is hard" to "this is less hard" to "this builds the next thing"
- Could still split if timing gets tight: "Getting Programs Into Computers" and "Your First Assembler"