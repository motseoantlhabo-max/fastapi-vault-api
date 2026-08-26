"""
Authentication routes.

POST /auth/register  - create a new user account
POST /auth/login      - exchange credentials for a JWT access token
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Creates a new user account. Emails and usernames must be unique. "
        "Passwords are hashed with bcrypt before being stored — the plaintext "
        "password is never persisted."
    ),
)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.execute(
        select(User).where((User.email == user_in.email) | (User.username == user_in.username))
    ).scalar_one_or_none()

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email or username already exists",
        )

    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Log in and receive a JWT access token",
    description=(
        "Standard OAuth2 password flow. Accepts form-encoded `username` and "
        "`password` fields (the `username` field accepts either the account's "
        "email or username) and returns a bearer access token."
    ),
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = db.execute(
        select(User).where(
            (User.email == form_data.username) | (User.username == form_data.username)
        )
    ).scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token)
