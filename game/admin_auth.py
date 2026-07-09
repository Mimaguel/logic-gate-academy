"""
game/admin_auth.py
=================
The admin password check, kept separate from any UI so it can be reused
and unit-tested without a GUI event loop.

LEARNING-PROJECT CAVEAT: the default password below is hardcoded. It's
overridden by an `ADMIN_PASSWORD` environment variable if one is set, so
the hardcoded default never has to be what's actually protecting real
data - but for a real deployment you'd want a proper secrets store, not
a plain string comparison either.
"""

from __future__ import annotations
import os

DEFAULT_ADMIN_PASSWORD = "admin123"


def get_admin_password() -> str:
    return os.environ.get("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)


def check_admin_password(attempt: str) -> bool:
    return attempt == get_admin_password()
