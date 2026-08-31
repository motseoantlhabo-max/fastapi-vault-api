"""
Authentication routes.

POST /auth/register - create a new user account
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.utils.security import hash_password


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Creates a new user account. Email and username must be unique. "
        "The password is hashed using bcrypt before being stored."
    ),
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> User:

    # Check whether the email or username is already registered.
    existing = db.execute(
        select(User).where(
            (User.email == user_in.email)
            | (User.username == user_in.username)
        )
    ).scalar_one_or_none()

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email or username already exists",
        )

    # Create user with a hashed password.
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user