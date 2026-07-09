"""
game/storage.py
=================
A small, generic "encrypted CSV database" used by both the accounts
store and the leaderboard. Internally, data is kept as CSV (simple,
human-designable, easy to inspect/debug if you ever decrypt it) and then
encrypted as a whole with Fernet before touching disk - so you get the
simplicity of CSV as a format and the privacy of encryption at rest,
together.

Neither AccountManager nor Leaderboard talk to files directly - they
both go through an EncryptedCSVStore instance, so the "how do we persist
this" logic only exists in one place.
"""

from __future__ import annotations
import csv
import io
from pathlib import Path
from typing import Dict, List, Optional

from . import crypto_utils


class EncryptedCSVStore:
    def __init__(self, path: Path, key_path: Path, fieldnames: List[str]):
        self.path = path
        self.key_path = key_path
        self.fieldnames = fieldnames
        self.key: bytes = crypto_utils.load_or_create_key(key_path)

    def read_rows(self) -> List[Dict[str, str]]:
        """Return every row as a dict, or an empty list if the file is
        missing, corrupted, or the key doesn't match - this store is
        used for game data, not anything worth crashing over."""
        if not self.path.exists():
            return []
        try:
            raw = self.path.read_bytes()
            decrypted = crypto_utils.decrypt(raw, self.key)
            text = decrypted.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            return [dict(row) for row in reader]
        except (crypto_utils.InvalidToken, UnicodeDecodeError, csv.Error, ValueError):
            return []

    def write_rows(self, rows: List[Dict[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        encrypted = crypto_utils.encrypt(buffer.getvalue().encode("utf-8"), self.key)
        self.path.write_bytes(encrypted)
