"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import AuthUserResponse, LoginRequest, LoginResponse
from app.services.auth_service import (
    create_access_token,
    get_current_active_user,
    get_db_session,
    verify_password,
    verify_password_via_db,
)

auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@auth_router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_session)):
    """Authenticate user with email/password and return JWT."""
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong email and/or password",
        )

    if not verify_password(payload.password, user.password_hash) and not verify_password_via_db(
        db, payload.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong email and/or password",
        )

    token = create_access_token(user.user_id, user.email)
    return LoginResponse(
        access_token=token,
        user=AuthUserResponse(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
        ),
    )


@auth_router.get("/me", response_model=AuthUserResponse)
def me(current_user: User = Depends(get_current_active_user)):
    """Return current authenticated user profile."""
    return AuthUserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        display_name=current_user.display_name,
        is_active=current_user.is_active,
    )
