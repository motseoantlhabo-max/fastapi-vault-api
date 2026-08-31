"""
Pydantic v2 schemas for User request/response payloads.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """
    Data required to create a new user.
    """

    email: EmailStr

    username: str = Field(
        min_length=3,
        max_length=50,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserRead(BaseModel):
    """
    Safe user representation returned to clients.

    hashed_password is intentionally excluded.
    """

    id: str
    email: EmailStr
    username: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )