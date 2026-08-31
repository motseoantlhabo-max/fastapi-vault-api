"""
Shared FastAPI dependencies.

Authentication itself lives in app.auth.oauth2.
This module re-exports get_current_user so the rest of the
application can use a simple dependency import.
"""

from app.database import get_db
from app.auth.oauth2 import get_current_user


__all__ = [
    "get_db",
    "get_current_user",
]