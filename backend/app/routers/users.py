"""User endpoints."""

from fastapi import APIRouter

from app.core.dependencies import CurrentUser
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> UserRead:
    """Return the profile of the logged-in user."""
    return current_user
