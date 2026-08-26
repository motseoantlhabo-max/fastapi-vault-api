"""Pydantic v2 schemas for authentication."""

from pydantic import BaseModel


class Token(BaseModel):
    """Response returned by POST /auth/login."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload shape."""

    sub: str | None = None
    exp: int | None = None
