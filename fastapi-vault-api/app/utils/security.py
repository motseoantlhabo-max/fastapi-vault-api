"""
Password security utilities.

JWT functionality is handled separately in app.auth.oauth2.
"""

from passlib.context import CryptContext


# bcrypt password hashing configuration.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    """

    return pwd_context.hash(plain_password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plaintext password against its bcrypt hash.
    """

    return pwd_context.verify(
        plain_password,
        hashed_password,
    )