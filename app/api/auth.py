from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_db
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserOut,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_password_reset_token,
    verify_password_reset_token_db,
)
from app.core.config import settings
from app.services.email_service import send_password_reset_email

import secrets
from app.services.notification_service import send_password_reset_email


RESET_TOKEN_EXPIRE_MINUTES = 30
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token."""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/password-reset/request")
@limiter.limit("3/hour")
async def request_password_reset(
    request: Request,
    data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset.
    Rate limited to 3 requests per hour per IP address.
    """
    user = db.query(User).filter(User.email == data.email).first()
    
    if user:
        # Generate secure random token
        token = generate_password_reset_token()
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )
        
        # Store token in database
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
        )
        db.add(reset_token)
        db.commit()
        
        # Send email
        try:
            await send_password_reset_email(user.email, user.name, token)
        except Exception as e:
            print(f"Failed to send reset email to {user.email}: {e}")

    # Always return the same message for security
    return {
        "message": "If that email address is in our system, you will receive a password reset link shortly."
    }


@router.post("/password-reset/confirm")
def confirm_password_reset(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """
    Confirm password reset with one-time token.
    Token is immediately marked as used after successful reset.
    """
    # Verify token
    token_data = verify_password_reset_token_db(db, data.token)
    if not token_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid, expired, or already used reset token"
        )

    # Get user
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user password
    user.password_hash = hash_password(data.new_password)
    db.commit()

    # Mark token as used (one-time use enforcement)
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.id == token_data["token_id"]
    ).first()
    if reset_token:
        reset_token.is_used = True
        reset_token.used_at = datetime.utcnow()
        db.commit()

    return {
        "message": "Password updated successfully. You can now log in with your new password."
    }