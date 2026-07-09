"""
game/security.py
=================
Password hashing for the accounts database. Uses PBKDF2-HMAC-SHA256 (from
Python's standard library `hashlib` - no extra dependency needed) with a
random per-user salt, so:

  1. Two users with the same password get different stored hashes.
  2. The stored file never contains a plain-text password, only a salt
     and a hash that can verify a password without revealing it.
  3. Comparison uses `secrets.compare_digest` to avoid leaking timing
     information about how much of the hash matched.

This is a reasonable, dependency-free standard for a learning project.
It is intentionally NOT the same as a production auth system (which
would typically use a slower, memory-hard KDF like bcrypt/argon2), but
it is a genuine, correct implementation of the same core idea.
"""

from __future__ import annotations
import hashlib
import secrets
from typing import Optional

_ITERATIONS = 100_000


def hash_password(password: str, salt_hex: Optional[str] = None) -> tuple[str, str]:
    """Return (salt_hex, hash_hex) for `password`.

    If `salt_hex` is given, reuses it (used when verifying a login
    attempt against a stored hash). Otherwise generates a fresh random
    salt (used when creating a new account).
    """
    salt_hex = salt_hex or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), _ITERATIONS
    )
    return salt_hex, digest.hex()


def verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    """True if `password`, hashed with `salt_hex`, matches `expected_hash_hex`."""
    _, actual_hash_hex = hash_password(password, salt_hex)
    return secrets.compare_digest(actual_hash_hex, expected_hash_hex)
