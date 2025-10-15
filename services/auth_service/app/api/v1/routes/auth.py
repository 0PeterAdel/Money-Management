"""
Authentication routes - Complete auth system
Endpoints: /auth/signup, /auth/login, /auth/refresh, /auth/verify-otp,
          /auth/reset-password, /auth/change-password, /auth/delete-account
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import Optional
import httpx

from app.db.session import get_db
from app.db.models.user import User, OTPCode, UserSession, SystemConfig, UserRole
from app.schemas.user import (
    SignupRequest, LoginRequest, TokenResponse, VerifyOTPRequest,
    RequestPasswordResetRequest, ResetPasswordRequest, ChangePasswordRequest,
    DeleteAccountRequest, User as UserSchema, MessageResponse
)
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_token, generate_otp_code
)
from app.core.config import settings
from app.api.v1.dependencies import get_current_user

router = APIRouter()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def send_otp_notification(
    user: User,
    otp_code: str,
    purpose: str,
    db: Session
) -> bool:
    """
    Send OTP via configured method (Telegram or Email)
    """
    # Get OTP method from system config
    config = db.query(SystemConfig).filter(SystemConfig.key == "otp_method").first()
    otp_method = config.value if config else "disabled"
    
    if otp_method == "disabled":
        # OTP is disabled, auto-activate for dev
        return True
    
    # Prepare notification message
    if purpose == "signup":
        message = f"Welcome! Your verification code is: {otp_code}\nValid for {settings.OTP_EXPIRY_MINUTES} minutes."
        subject = "Account Verification Code"
    elif purpose == "reset_password":
        message = f"Password reset code: {otp_code}\nValid for {settings.OTP_EXPIRY_MINUTES} minutes."
        subject = "Password Reset Code"
    else:
        message = f"Your verification code is: {otp_code}"
        subject = "Verification Code"
    
    try:
        async with httpx.AsyncClient() as client:
            if otp_method == "telegram" and user.telegram_id:
                # Send via Telegram
                await client.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/send-telegram",
                    json={"chat_id": str(user.telegram_id), "message": message}
                )
            elif otp_method == "email":
                # Send via Email
                await client.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/send-email",
                    json={"to_email": user.email, "subject": subject, "body": message}
                )
            return True
    except Exception as e:
        print(f"Failed to send OTP notification: {e}")
        return False


def create_otp_code(user_id: int, purpose: str, db: Session) -> str:
    """
    Create and store OTP code
    """
    # Invalidate old OTP codes for this purpose
    db.query(OTPCode).filter(
        OTPCode.user_id == user_id,
        OTPCode.purpose == purpose,
        OTPCode.is_used == False
    ).update({"is_used": True})
    
    # Generate new OTP
    code = generate_otp_code(settings.OTP_LENGTH)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
    otp = OTPCode(
        user_id=user_id,
        code=code,
        purpose=purpose,
        expires_at=expires_at
    )
    db.add(otp)
    db.commit()
    
    return code


def verify_otp_code(user_id: int, code: str, purpose: str, db: Session) -> bool:
    """
    Verify OTP code
    """
    otp = db.query(OTPCode).filter(
        OTPCode.user_id == user_id,
        OTPCode.code == code,
        OTPCode.purpose == purpose,
        OTPCode.is_used == False,
        OTPCode.expires_at > datetime.utcnow()
    ).first()
    
    if not otp:
        return False
    
    # Mark as used
    otp.is_used = True
    db.commit()
    
    return True


def create_user_session(user: User, device_info: Optional[str], ip_address: Optional[str], db: Session) -> str:
    """
    Create user session and return refresh token
    """
    # Create refresh token
    refresh_token = create_refresh_token({"sub": str(user.id), "username": user.username})
    
    # Store session
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session = UserSession(
        user_id=user.id,
        refresh_token=refresh_token,
        device_info=device_info,
        ip_address=ip_address,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    
    return refresh_token


def invalidate_user_sessions(user_id: int, db: Session, except_token: Optional[str] = None):
    """
    Invalidate all user sessions except optionally one
    """
    query = db.query(UserSession).filter(UserSession.user_id == user_id)
    if except_token:
        query = query.filter(UserSession.refresh_token != except_token)
    query.delete()
    db.commit()


# ============================================================================
# AUTH ROUTES
# ============================================================================

@router.post("/signup", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    User signup/registration
    - Creates new user account
    - Sends OTP for verification if enabled
    - Returns success message
    """
    # Check if username exists
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if telegram_id exists (if provided)
    if request.telegram_id:
        if db.query(User).filter(User.telegram_id == request.telegram_id).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram account already linked"
            )
    
    # Create user
    hashed_password = get_password_hash(request.password)
    user = User(
        username=request.username,
        name=request.name,
        email=request.email,
        hashed_password=hashed_password,
        telegram_id=request.telegram_id,
        is_active=False,  # Will be activated after OTP verification
        role=UserRole.USER
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate and send OTP
    otp_code = create_otp_code(user.id, "signup", db)
    await send_otp_notification(user, otp_code, "signup", db)
    
    return MessageResponse(
        message="Registration successful! Please check your email/telegram for verification code.",
        detail=f"User ID: {user.id}"
    )


@router.post("/verify-otp", response_model=MessageResponse)
async def verify_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP code and activate account
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify OTP
    if not verify_otp_code(user.id, request.code, "signup", db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code"
        )
    
    # Activate user
    user.is_active = True
    db.commit()
    
    return MessageResponse(message="Account activated successfully! You can now login.")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    User login
    - Accepts username or email
    - Returns JWT tokens
    """
    # Find user by username or email
    user = db.query(User).filter(
        or_(
            User.username == request.username_or_email,
            User.email == request.username_or_email
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )
    
    # Check if user is banned
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been banned. Please contact support."
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated. Please verify your email/telegram first."
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role.value})
    
    # Create session with refresh token
    device_info = http_request.headers.get("user-agent")
    ip_address = http_request.client.host if http_request.client else None
    refresh_token = create_user_session(user, device_info, ip_address, db)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Check if session exists
    session = db.query(UserSession).filter(
        UserSession.refresh_token == refresh_token,
        UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    
    # Get user
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or user.is_banned or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not valid"
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role.value})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,  # Same refresh token
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/request-password-reset", response_model=MessageResponse)
async def request_password_reset(
    request: RequestPasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset - sends OTP
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists
        return MessageResponse(
            message="If the email exists, a reset code has been sent."
        )
    
    # Generate and send OTP
    otp_code = create_otp_code(user.id, "reset_password", db)
    await send_otp_notification(user, otp_code, "reset_password", db)
    
    return MessageResponse(
        message="Password reset code sent! Please check your email/telegram."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password with OTP
    """
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify OTP
    if not verify_otp_code(user.id, request.otp_code, "reset_password", db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code"
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    # Invalidate all sessions
    invalidate_user_sessions(user.id, db)
    
    return MessageResponse(message="Password reset successful! Please login with your new password.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password (authenticated user)
    """
    # Verify old password
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    # Invalidate other sessions (keep current one)
    # This would require passing current refresh token, simplified for now
    invalidate_user_sessions(current_user.id, db)
    
    return MessageResponse(message="Password changed successfully!")


@router.post("/delete-account", response_model=MessageResponse)
async def delete_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user account permanently
    """
    # Verify password
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Send confirmation notification (optional)
    try:
        await send_otp_notification(
            current_user,
            "Your account has been permanently deleted.",
            "account_deletion",
            db
        )
    except:
        pass  # Don't fail if notification fails
    
    # Delete user (cascade will delete sessions, OTPs, etc.)
    db.delete(current_user)
    db.commit()
    
    return MessageResponse(message="Account deleted successfully. We're sorry to see you go!")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Logout user - invalidate session
    """
    session = db.query(UserSession).filter(UserSession.refresh_token == refresh_token).first()
    if session:
        db.delete(session)
        db.commit()
    
    return MessageResponse(message="Logged out successfully!")
