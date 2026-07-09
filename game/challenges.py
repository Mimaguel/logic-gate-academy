"""
game/challenges.py
=================
Pure game-rule logic for every question type in the game: generating a
random question and checking whether an answer is correct.

This module deliberately contains NO input()/print() calls and NO
blocking loops - it never "runs" a question interactively itself.
Instead, it hands back small, immutable data objects (dataclasses)
describing a question, and the caller (a GUI widget, a test, whatever)
decides how to display it and how to collect an answer.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from random import choice, randint
from typing import List, Optional

from . import encoding
from .gates import GateType, LogicGate


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @property
    def label(self) -> str:
        return self.value.capitalize()


# ---------------------------------------------------------------------
# Logic gate questions
# ---------------------------------------------------------------------

# Game-balance constants - the single place these numbers are defined.
ROUNDS_PER_CHALLENGE = 7
STARTING_LIVES = 5
POINTS_PER_ROUND = {Difficulty.EASY: 10, Difficulty.MEDIUM: 15, Difficulty.HARD: 20}
BONUS_POINTS = 10
NUMBER_CHALLENGE_MAX_ATTEMPTS = 3

# Which gates are in play at each difficulty. Higher difficulties add
# progressively less-familiar gates on top of the previous tier, so the
# gate pool itself becomes part of the difficulty curve, not just the
# question formula.
GATES_BY_DIFFICULTY: dict[Difficulty, List[GateType]] = {
    Difficulty.EASY: [GateType.AND, GateType.OR, GateType.NOT],
    Difficulty.MEDIUM: [GateType.AND, GateType.OR, GateType.NOT, GateType.XOR, GateType.NAND],
    Difficulty.HARD: list(GateType),  # all seven
}


@dataclass
class GateRound:
    """Everything about a single logic-gate question."""

    a: int
    b: int
    c: int
    op1: GateType
    op2: Optional[GateType]
    expected: int

    def question_text(self, difficulty: Difficulty) -> str:
        if difficulty is Difficulty.EASY:
            return f"What is the result of A: {self.a} {self.op1.value} B: {self.b}?"
        if difficulty is Difficulty.MEDIUM:
            return (
                f"First compute (A: {self.a} {self.op1.value} B: {self.b}).\n"
                f"Then combine that result {self.op2.value} A ({self.a})."
            )
        return (
            f"First compute (A: {self.a} {self.op1.value} B: {self.b}).\n"
            f"Then combine that result {self.op2.value} C ({self.c})."
        )


def generate_round(difficulty: Difficulty) -> GateRound:
    """Build one random logic-gate question for the given difficulty.

    - easy:   A (op1) B                - gates: AND, OR, NOT
    - medium: (A op1 B) op2 A          - gates: + XOR, NAND
    - hard:   (A op1 B) op2 C          - gates: + NOR, XNOR (all seven)
    """
    pool = GATES_BY_DIFFICULTY[difficulty]
    a, b, c = randint(0, 1), randint(0, 1), randint(0, 1)
    op1 = choice(pool)

    if difficulty is Difficulty.EASY:
        expected = LogicGate.evaluate(op1, a, b)
        return GateRound(a, b, c, op1, None, expected)

    op2 = choice(pool)
    intermediate = LogicGate.evaluate(op1, a, b)
    second_operand = a if difficulty is Difficulty.MEDIUM else c
    expected = LogicGate.evaluate(op2, intermediate, second_operand)
    return GateRound(a, b, c, op1, op2, expected)


# ---------------------------------------------------------------------
# Number-system questions (binary <-> decimal <-> ASCII)
# ---------------------------------------------------------------------

@dataclass
class BinaryQuestion:
    """'What's this binary string in decimal?'"""

    binary_string: str
    decimal_value: int


def generate_binary_question() -> BinaryQuestion:
    binary_string = "".join(str(randint(0, 1)) for _ in range(7))
    return BinaryQuestion(binary_string, encoding.binary_to_decimal(binary_string))


@dataclass
class AsciiQuestion:
    """'What's this ASCII decimal code in 7-bit binary?'"""

    decimal_value: int
    binary_value: str

    @property
    def character(self) -> str:
        return chr(self.decimal_value)


def generate_ascii_question() -> AsciiQuestion:
    codes = encoding.all_quizzable_codes()
    decimal_value = codes[randint(0, len(codes) - 1)]
    return AsciiQuestion(decimal_value, encoding.decimal_to_binary(decimal_value))


def is_valid_binary_answer(raw: str) -> bool:
    """True if `raw` is exactly 7 characters of '0'/'1' - used to validate
    an AsciiQuestion answer before comparing it."""
    return len(raw) == 7 and all(ch in "01" for ch in raw)
