"""
game/crypto_utils.py
=================
Small helper for encrypting and decrypting the leaderboard save file.

Uses Fernet symmetric encryption (from the `cryptography` library), which
combines AES-128 encryption with a message authentication code - so the
saved file is both unreadable without the key AND tamper-evident (loading
a file that's been edited or corrupted raises `InvalidToken` instead of
silently returning wrong data).

LEARNING-PROJECT CAVEAT: the encryption key is generated once and stored
in a plain file (`data/leaderboard.key`) right next to the encrypted
leaderboard. This stops someone from casually opening `leaderboard.enc` in
a text editor and reading scores, but it does NOT stop someone who has
filesystem access to the whole `data/` folder, since the key sits right
there too. Real secret management would keep the key somewhere separate
from the data it protects (an environment variable, a secrets manager, a
password-derived key, etc.). This is intentionally simple, to demonstrate
the *concept* of encrypting data at rest without adding a login flow just
to view your own leaderboard.
"""

from __future__ import annotations
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

__all__ = ["Fernet", "InvalidToken", "load_or_create_key", "encrypt", "decrypt"]


def load_or_create_key(key_path: Path) -> bytes:
    """Return the Fernet key stored at `key_path`.

    The first time this is called for a given path, a new random key is
    generated and saved; every call after that reuses the same key so
    previously-encrypted data can still be decrypted.
    """
    if key_path.exists():
        return key_path.read_bytes()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    key_path.write_bytes(key)
    return key


def encrypt(data: bytes, key: bytes) -> bytes:
    """Encrypt raw bytes (e.g. UTF-8 encoded JSON) with `key`."""
    return Fernet(key).encrypt(data)


def decrypt(token: bytes, key: bytes) -> bytes:
    """Decrypt bytes previously produced by `encrypt` with the same key.

    Raises `cryptography.fernet.InvalidToken` if `key` is wrong, or if
    `token` has been corrupted or tampered with.
    """
    return Fernet(key).decrypt(token)
