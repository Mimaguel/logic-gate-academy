"""
game/accounts.py
=================
Manages who is playing: a signed-up Player, or a temporary Guest.

Registered accounts are now PERSISTED between runs, stored via an
EncryptedCSVStore (see game/storage.py) - so creating an account once
means you can log back in tomorrow. Passwords are never stored in plain
text: only a random salt and a PBKDF2 hash (see game/security.py) ever
touch disk.

Guests remain intentionally ephemeral (never written to disk) - a guest
is meant to be a quick "just let me play" option, not an identity worth
remembering.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import security
from .storage import EncryptedCSVStore

_FIELDNAMES = ["username", "salt", "password_hash"]


@dataclass
class Player:
    username: str
    password: Optional[str] = field(default=None, repr=False)
    is_guest: bool = False


class AccountManager:
    def __init__(self, save_path: Optional[Path] = None, key_path: Optional[Path] = None) -> None:
        self._guest_count = 0
        self._store: Optional[EncryptedCSVStore] = None
        # username -> {"salt": ..., "password_hash": ...}
        self._accounts: dict[str, dict[str, str]] = {}

        if save_path and key_path:
            self._store = EncryptedCSVStore(save_path, key_path, _FIELDNAMES)
            for row in self._store.read_rows():
                self._accounts[row["username"]] = {
                    "salt": row["salt"],
                    "password_hash": row["password_hash"],
                }

    def create_account(self, username: str, password: str, confirm_password: str) -> tuple[Optional[Player], Optional[str]]:
        """Returns (player, None) on success, or (None, error_message)."""
        username = username.strip()
        if not username:
            return None, "Username cannot be empty."
        if username in self._accounts:
            return None, "That username is already taken."
        if not password:
            return None, "Password cannot be empty."
        if password != confirm_password:
            return None, "Passwords did not match."

        salt, password_hash = security.hash_password(password)
        self._accounts[username] = {"salt": salt, "password_hash": password_hash}
        self._persist()
        return Player(username=username), None

    def login(self, username: str, password: str) -> tuple[Optional[Player], Optional[str]]:
        """Returns (player, None) on success, or (None, error_message)."""
        username = username.strip()
        record = self._accounts.get(username)
        if not record:
            return None, "No account with that username."
        if not security.verify_password(password, record["salt"], record["password_hash"]):
            return None, "Incorrect password."
        return Player(username=username), None

    def play_as_guest(self) -> Player:
        self._guest_count += 1
        return Player(username=f"Player{self._guest_count}", is_guest=True)

    def list_usernames(self) -> list[str]:
        """Registered (non-guest) usernames only, alphabetically sorted.
        Never exposes passwords or hashes - used by the Admin Dashboard."""
        return sorted(self._accounts.keys())

    def account_count(self) -> int:
        return len(self._accounts)

    # -- persistence -----------------------------------------------------

    def _persist(self) -> None:
        if not self._store:
            return
        rows = [
            {"username": name, "salt": rec["salt"], "password_hash": rec["password_hash"]}
            for name, rec in self._accounts.items()
        ]
        self._store.write_rows(rows)
