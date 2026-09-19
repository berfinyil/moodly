"""Authentication endpoints: register and login."""

from fastapi import APIRouter, status

from app.core.dependencies import DbSession
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register", response_model=UserRead, status_code=status.HTTP_201_CREATED
)
def register(data: UserCreate, db: DbSession) -> UserRead:
    """Create a new user account."""
    return auth_service.register_user(db, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: DbSession) -> TokenResponse:
    """Exchange email + password for a JWT access token."""
    token = auth_service.login_user(db, data.email, data.password)
    return TokenResponse(access_token=token)
