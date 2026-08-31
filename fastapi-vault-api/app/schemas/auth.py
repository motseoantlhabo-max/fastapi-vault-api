"""
Pydantic schemas for authentication.
"""

from pydantic import BaseModel


class Token(BaseModel):
    """
    JWT access token returned after successful login.
    """

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Structure of the JWT payload.
    """

    sub: str | None = None
    exp: int | None = None