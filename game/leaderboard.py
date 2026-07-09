"""
game/leaderboard.py
=================
Tracks scores across a play session. Internally stored as CSV (via
EncryptedCSVStore), encrypted as a whole with Fernet before touching
disk - so `data/leaderboard.enc` is both a simple, well-understood format
under the hood and unreadable as plain text if opened directly.

Every method here returns data rather than printing it - display is
entirely the GUI's responsibility.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .storage import EncryptedCSVStore

_FIELDNAMES = ["username", "score", "difficulty"]


@dataclass
class ScoreEntry:
    username: str
    score: int
    difficulty: str


class Leaderboard:
    """Keeps scores sorted best-first and (optionally) persists them,
    encrypted, to disk as CSV."""

    def __init__(self, save_path: Optional[Path] = None, key_path: Optional[Path] = None) -> None:
        self._store: Optional[EncryptedCSVStore] = None
        self._entries: List[ScoreEntry] = []

        if save_path and key_path:
            self._store = EncryptedCSVStore(save_path, key_path, _FIELDNAMES)
            self._entries = [
                ScoreEntry(row["username"], int(row["score"]), row["difficulty"])
                for row in self._store.read_rows()
                if row.get("username") and row.get("score", "").isdigit()
            ]
            self._entries.sort(key=lambda e: e.score, reverse=True)

    def add(self, username: str, score: int, difficulty: str) -> None:
        self._entries.append(ScoreEntry(username, score, difficulty))
        self._entries.sort(key=lambda e: e.score, reverse=True)
        self._persist()

    def top(self, count: int = 10) -> List[ScoreEntry]:
        return self._entries[:count]

    def all(self) -> List[ScoreEntry]:
        """Every saved entry, sorted best-first - used by the Admin
        Dashboard, which (unlike the normal leaderboard view) shouldn't be
        limited to the top 10."""
        return list(self._entries)

    def clear(self) -> None:
        """Wipe every entry and persist the now-empty leaderboard.
        Used by the Admin Dashboard's "Reset Leaderboard" action."""
        self._entries = []
        self._persist()

    # -- persistence -----------------------------------------------------

    def _persist(self) -> None:
        if not self._store:
            return
        rows = [
            {"username": e.username, "score": str(e.score), "difficulty": e.difficulty}
            for e in self._entries
        ]
        self._store.write_rows(rows)
