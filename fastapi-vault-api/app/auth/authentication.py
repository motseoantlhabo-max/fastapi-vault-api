"""
Authentication endpoints.

Handles user login and issuing JWT access tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token
from app.utils.security import verify_password
from app.auth.oauth2 import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=Token,
    summary="Log in and receive a JWT access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:

    # The OAuth2 form calls this field "username".
    # We allow the user to log in using either username or email.
    user = db.execute(
        select(User).where(
            (User.username == form_data.username)
            | (User.email == form_data.username)
        )
    ).scalar_one_or_none()

    # Do not reveal whether the username/email exists.
    if user is None or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Do not allow inactive users to log in.
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Create JWT using the user's UUID as the subject.
    access_token = create_access_token(
        data={"sub": user.id}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
    )