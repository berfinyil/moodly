"""Business logic for registration and login."""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate

logger = logging.getLogger("moodly.auth")


def register_user(db: Session, data: UserCreate) -> User:
    """Create a new user; fails if email or username is already taken."""
    if user_repository.get_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Diese E-Mail-Adresse ist bereits registriert.",
        )
    if user_repository.get_by_username(db, data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dieser Benutzername ist bereits vergeben.",
        )
    return user_repository.create(
        db,
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
    )


def login_user(db: Session, email: str, password: str) -> str:
    """Verify credentials and return a JWT access token."""
    user = user_repository.get_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        # Same message for both cases so attackers can't probe which emails exist.
        logger.info("Login failed for a user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-Mail oder Passwort ist falsch.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dieses Konto ist deaktiviert.",
        )
    return create_access_token(user.id)
