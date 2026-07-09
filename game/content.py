"""
game/content.py
=================
Static teaching content: the Tutorial's pages and the plain-English
explanations shown in Learning Mode. Kept as plain data (Markdown
strings) so any front-end can render it - the GUI's QTextBrowser
supports Markdown natively via `.setMarkdown(...)`.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from .gates import GateType


@dataclass
class TutorialPage:
    heading: str
    body: str  # Markdown text


TUTORIAL_PAGES: List[TutorialPage] = [
    TutorialPage(
        "Welcome",
        """
Welcome to **Logic Gate Academy**!

This is an interactive game that teaches the basics of **logic gates**,
**binary numbers**, and **ASCII encoding**.

You'll be shown random logic gate expressions and have to work out the
answer using binary values (`0` = False, `1` = True). Higher difficulties
introduce more gates beyond the classic AND / OR / NOT.

Every correct answer adds one bit to a secret binary code. Finish all
7 rounds and you'll get to decode the hidden character it spells out.
        """,
    ),
    TutorialPage(
        "Binary Numbers",
        """
### What is binary?

Binary represents data using only two digits: `0` and `1`. Computers
use binary because electrical signals are either **on** (`1`) or
**off** (`0`).

Each digit is a power of 2, counting from the right:

| Position (from right) | 1st | 2nd | 3rd | 4th | ... |
|---|---|---|---|---|---|
| Value | 2^0 = 1 | 2^1 = 2 | 2^2 = 4 | 2^3 = 8 | ... |

**Example:** the letter `a` is decimal `97`, which in 7-bit binary is
`1100001` -> 64 + 32 + 1 = 97 (we only add up the positions that are `1`).
        """,
    ),
    TutorialPage(
        "ASCII Encoding",
        """
### What is ASCII?

ASCII (American Standard Code for Information Interchange) maps every
letter, digit, and symbol to a unique decimal number.

| Category | Range |
|---|---|
| Uppercase letters `A`-`Z` | 65 - 90 |
| Lowercase letters `a`-`z` | 97 - 122 |
| Digits `0`-`9` | 48 - 57 |
| Common symbols | 33 - 47 |

Each of those decimal codes can be written as binary, e.g.
`A` = 65 = `1000001`, `a` = 97 = `1100001`.
        """,
    ),
    TutorialPage(
        "Logic Gates",
        """
### The gates in this game

**AND** - true only if *both* inputs are true.

**OR** - true if *at least one* input is true.

**NOT** - flips a single input (0 to 1, or 1 to 0).

Those three appear at every difficulty. As you move up, more gates join
the mix:

**XOR** and **NAND** unlock at **Medium**.

**NOR** and **XNOR** unlock at **Hard**, alongside all five of the above -
seven gates in total. Check the Learning Mode's "Explain: Logic Gates"
screen any time for a full truth-table reference.
        """,
    ),
    TutorialPage(
        "How a Round Works",
        """
### Putting it together

1. The game shows you a random logic gate expression.
2. You compute the result yourself (0 or 1) and enter it.
3. Correct answers are collected into a growing binary code.
4. After 7 correct rounds, that code becomes a decimal ASCII value.
5. You get one last challenge: guess the character it represents!

That's the whole game. Good luck, and have fun!
        """,
    ),
]


def gate_reference_markdown() -> str:
    """A Markdown block covering all seven gates - description + truth
    table for each - used by Learning Mode's 'Explain: Logic Gates'."""
    parts = [
        "# Logic Gates\n",
        "AND / OR / NOT appear at every difficulty. XOR and NAND join at "
        "**Medium**. NOR and XNOR join at **Hard**, for all seven.\n",
    ]
    for gate in GateType:
        parts.append(f"### {gate.value}\n{gate.describe()}\n")
        parts.append("```\n" + gate.truth_table() + "\n```\n")
    return "\n".join(parts)


BINARY_EXPLANATION_MARKDOWN = """
# Counting in Binary

Each position in a binary number represents a power of 2.

From right to left: 1, 2, 4, 8, 16, 32, 64, ...

To convert binary to decimal, add up the powers of 2 where the digit is `1`.

**Example:** `10110` = 16 + 4 + 2 = **22**
"""

ASCII_EXPLANATION_MARKDOWN = """
# ASCII Basics

ASCII assigns a decimal number to every character.

- Uppercase letters (A-Z): 65-90
- Lowercase letters (a-z): 97-122
- Digits (0-9): 48-57
- Common symbols: 33-47

We use 7-bit binary numbers to represent these codes in this game.
"""
