# Number System Conversion - Grades (Assignment 237486312)

Rubric (0-100): Dec->Bin 40 | Bonus 1 functions +10 | Bonus 2 Bin->Dec +10 | Bonus 3 Hex->Bin/Dec +10 | Bonus 4 Bin/Dec->Hex +10 | Elegance up to +10 | User-friendliness up to +10 | minus deductions for bugs/crashes.

| File | Bonuses | Score | Reason |
|---|---|---|---|
| AMcGuire_EMarina_EMaingrette.txt | 1,2,3,4 | 92 | All 6 conversions, letter menu, full input validation, accepts lowercase hex, repeat option. Heavy code duplication (~200 lines), recursion instead of loops, binary "0" gives empty hex. |
| CChen.txt | 1,2,3,4 | 87 | All bonuses, error handling, handles 0, some function reuse. Long if/elif chains, dec_to_hex duplicates bin_to_hex, lowercase hex rejected, empty input crashes, no repeat. |
| GValjato.txt | 1,2,3,4 | 86 | Most elegant: ~20 lines using bin()/int()/hex(). No menu (forces all 4 conversions in a row), no validation (crashes on bad input), lowercase hex output. Uses built-ins, so no algorithm shown. |
| GLiu.txt | 1,2,3,4 | 83 | All 6 conversions, good reuse (hex_bin/bin_hex compose others), numbered menu. Binary stored as an int (drops leading zeros), hard-coded if ladders, dead code, lowercase hex crashes, 256 crashes despite prompt "1-256". |
| AQirko.txt | 1,2,3,4 | 80 | Each input shows both other bases - nice output. 30+ line elif chain for hex, lowercase hex gives silently WRONG answer (c8 -> 8), 1-char hex crashes, no validation. |
| RWagner.txt | 1,2 | 64 | Functions + Bin<->Dec with a repeat loop. `while choice != "Bin" or "Dec"` is always true (no way to exit), debug print left in, binary must be exactly 8 digits or it crashes. |
| JLo.txt | 1 | 60 | Clean, short remainder loop in a function, handles 0. Only Dec->Bin, no validation. |
| MNembhard.txt | 1 | 59 | Compact function, fixed 8-bit output. Only Dec->Bin. Near-identical to AQirko's dec_to_bin - check for sharing. |
| SColin-Keita.txt | 1 | 54 | Works, uses a function, 8-bit output. Very verbose (8 hard-coded ifs + 8 variables). |
| ABhatti_SBifulco.txt | - | 50 | Concise loop, pads to 8 bits, 0 works. No function, cryptic names (x, y, z). |
| CRuiz_OYounggren.txt | - | 48 | Concise remainder loop with labeled output. No function; input 0 prints blank. Conner's file says partner submits the rest. |
| VWeber.txt | - | 45 | Correct 8-bit output, but 8 copy-paste if blocks, no function. |
| JGellineau.txt | - | 42 | Works but builds binary as an int (drops leading zeros), hard-coded ifs, no function. |
| CMiazga.txt | - | 28 | WRONG output for any number >= 128 (for/else bug always resets first bit: 200 -> 01001000). Verbose. |
| MArtemyev.txt | - | 10 | Does not run: IndentationError (unfinished if). Loop logic started but never printed. |
| MSultan_RChaglla.txt | - | 0 | Only the title print statement; no conversion. |
