from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
from fastapi import Response, Request
from app.models.user_session import UserSession
from app.core.config import settings
from app.core.security import generate_refresh_token, hash_token, get_current_user
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

# import secrets
# from app.services.notification_service import send_password_reset_email


RESET_TOKEN_EXPIRE_MINUTES = 30
router = APIRouter()
REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="none" if settings.ENVIRONMENT == "production" else "lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",
    )


def _issue_session(db: Session, user: User, request: Request, family_id: str) -> str:
    raw_token = generate_refresh_token()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        family_id=family_id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    db.commit()
    return raw_token
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
def login(credentials: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({"sub": str(user.id)})
    family_id = str(uuid.uuid4())
    refresh_token = _issue_session(db, user, request, family_id)
    _set_refresh_cookie(response, refresh_token)

    return {"access_token": access_token, "token_type": "bearer"}
@router.post("/refresh", response_model=Token)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    token_hash = hash_token(raw_token)
    session = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()

    if not session:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if session.revoked_at is not None:
        # This exact token was already rotated away once before — a second use
        # means someone else has a copy of it. Kill the whole session family.
        db.query(UserSession).filter(
            UserSession.family_id == session.family_id,
            UserSession.revoked_at.is_(None),
        ).update({"revoked_at": datetime.utcnow()})
        db.commit()
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/auth")
        raise HTTPException(status_code=401, detail="Refresh token reuse detected, please log in again")

    if session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    session.revoked_at = datetime.utcnow()
    db.commit()

    new_refresh_token = _issue_session(db, user, request, session.family_id)
    _set_refresh_cookie(response, new_refresh_token)

    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        token_hash = hash_token(raw_token)
        session = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()
        if session and session.revoked_at is None:
            session.revoked_at = datetime.utcnow()
            db.commit()
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/auth")
    return {"message": "Logged out"}


@router.post("/logout-all")
def logout_all(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at.is_(None),
    ).update({"revoked_at": datetime.utcnow()})
    db.commit()
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/auth")
    return {"message": "Logged out of all devices"}


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