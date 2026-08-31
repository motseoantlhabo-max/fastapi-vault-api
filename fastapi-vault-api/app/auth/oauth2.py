"""
OAuth2 and JWT authentication utilities.

Responsible for:

1. Defining the OAuth2 bearer token scheme.
2. Creating JWT access tokens.
3. Decoding and validating JWT access tokens.
4. Loading the current authenticated user.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User


# This tells FastAPI where users obtain their access token.
#
# It is also used by Swagger UI when you click "Authorize".
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# Standard exception used whenever authentication fails.
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create and sign a JWT access token.

    The data dictionary normally contains:

        {"sub": user.id}

    The expiration time is added automatically.
    """

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update(
        {
            "exp": expire,
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate a JWT.

    Returns:
        Dictionary containing the JWT payload if valid.
        None if the token is invalid or expired.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        return payload

    except JWTError:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the bearer token and return the authenticated user.

    The JWT contains the user's ID in the "sub" claim.
    """

    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id: str | None = payload.get("sub")

    if user_id is None:
        raise credentials_exception

    user = db.get(User, user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user