"""
User profile routes.

GET /users/me - return the authenticated user's own profile
"""

from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the current authenticated user's profile",
)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
