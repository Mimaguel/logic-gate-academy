"""
game/gates.py
=================
This is the "rulebook" for logic gates. Nothing in here prints anything
or asks the user a question - it only knows how to compute answers.

Seven gates are supported: AND, OR, NOT, XOR, NAND, NOR, XNOR. Difficulty
tiers (see game/challenges.py) control which of these a player actually
sees - beginners start with the classic three, and the rest unlock as
difficulty increases.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional


class GateType(Enum):
    """Every logic gate the game knows how to evaluate."""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    XOR = "XOR"
    NAND = "NAND"
    NOR = "NOR"
    XNOR = "XNOR"

    @property
    def is_unary(self) -> bool:
        """NOT only needs one input; every other gate needs two."""
        return self is GateType.NOT

    def truth_table(self) -> str:
        """Return a small, human-readable truth table for this gate."""
        tables = {
            GateType.AND: (
                "A  B  |  A AND B\n"
                "0  0  |  0\n"
                "0  1  |  0\n"
                "1  0  |  0\n"
                "1  1  |  1"
            ),
            GateType.OR: (
                "A  B  |  A OR B\n"
                "0  0  |  0\n"
                "0  1  |  1\n"
                "1  0  |  1\n"
                "1  1  |  1"
            ),
            GateType.NOT: (
                "A  |  NOT A\n"
                "0  |  1\n"
                "1  |  0"
            ),
            GateType.XOR: (
                "A  B  |  A XOR B\n"
                "0  0  |  0\n"
                "0  1  |  1\n"
                "1  0  |  1\n"
                "1  1  |  0"
            ),
            GateType.NAND: (
                "A  B  |  A NAND B\n"
                "0  0  |  1\n"
                "0  1  |  1\n"
                "1  0  |  1\n"
                "1  1  |  0"
            ),
            GateType.NOR: (
                "A  B  |  A NOR B\n"
                "0  0  |  1\n"
                "0  1  |  0\n"
                "1  0  |  0\n"
                "1  1  |  0"
            ),
            GateType.XNOR: (
                "A  B  |  A XNOR B\n"
                "0  0  |  1\n"
                "0  1  |  0\n"
                "1  0  |  0\n"
                "1  1  |  1"
            ),
        }
        return tables[self]

    def describe(self) -> str:
        """One-line plain-English explanation, used in tooltips/menus."""
        descriptions = {
            GateType.AND: "True only if BOTH inputs are true.",
            GateType.OR: "True if AT LEAST ONE input is true.",
            GateType.NOT: "Flips the input: 0 becomes 1, 1 becomes 0.",
            GateType.XOR: "True if the inputs are DIFFERENT from each other.",
            GateType.NAND: "The opposite of AND - false only if both inputs are true.",
            GateType.NOR: "The opposite of OR - true only if both inputs are false.",
            GateType.XNOR: "True if the inputs are THE SAME as each other.",
        }
        return descriptions[self]


class LogicGate:
    """A tiny "calculator" that evaluates gates.

    Every method is a @staticmethod because LogicGate doesn't need to
    remember any state between calls - it's a pure function bundled
    into a class purely for organization.
    """

    @staticmethod
    def evaluate(gate: GateType, a: int, b: Optional[int] = None) -> int:
        """Evaluate `gate` on input(s) `a` (and `b`, for binary gates).

        `a` and `b` are expected to be 0 or 1. The result is always
        returned as a plain int (0 or 1), never as a Python bool, so it
        can be concatenated straight into a binary string.
        """
        av, bv = bool(a), bool(b)
        if gate is GateType.AND:
            return int(av and bv)
        if gate is GateType.OR:
            return int(av or bv)
        if gate is GateType.NOT:
            return int(not av)
        if gate is GateType.XOR:
            return int(av != bv)
        if gate is GateType.NAND:
            return int(not (av and bv))
        if gate is GateType.NOR:
            return int(not (av or bv))
        if gate is GateType.XNOR:
            return int(av == bv)
        raise ValueError(f"Unsupported gate: {gate!r}")
