"""
game/encoding.py
=================
Helper functions for the "number systems" side of the game: turning
binary strings into decimal numbers, and decimal ASCII codes into
printable characters (and back again).

Nothing here touches the screen or the keyboard - just like gates.py,
this module is pure logic that other modules can trust and re-use.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple


def binary_to_decimal(binary_string: str) -> int:
    """Convert a string like '1100001' into its decimal value (97)."""
    return int(binary_string, 2)


def decimal_to_binary(value: int, bits: int = 7) -> str:
    """Convert a decimal value into a zero-padded binary string."""
    return bin(value)[2:].zfill(bits)


@dataclass(frozen=True)
class AsciiRange:
    """A named block of the ASCII table, e.g. 'Uppercase letters'."""

    label: str
    start: int
    end: int

    def contains(self, value: int) -> bool:
        return self.start <= value <= self.end

    def characters(self) -> List[Tuple[int, str]]:
        """List of (decimal_code, character) pairs in this range."""
        return [(code, chr(code)) for code in range(self.start, self.end + 1)]


# The ranges the game is willing to quiz players on. 7 bits covers
# 0-127, which is exactly the classic ASCII table.
ASCII_RANGES: List[AsciiRange] = [
    AsciiRange("Uppercase letters (A-Z)", 65, 90),
    AsciiRange("Lowercase letters (a-z)", 97, 122),
    AsciiRange("Digits (0-9)", 48, 57),
    AsciiRange("Symbols (!\"#$%&'()*+,-./)", 33, 47),
]


def find_ascii_range(decimal_value: int) -> AsciiRange | None:
    """Return the AsciiRange that a decimal value belongs to, if any."""
    for ascii_range in ASCII_RANGES:
        if ascii_range.contains(decimal_value):
            return ascii_range
    return None


def all_quizzable_codes() -> List[int]:
    """Every decimal code the game is allowed to ask players to guess."""
    return [code for r in ASCII_RANGES for code in range(r.start, r.end + 1)]
