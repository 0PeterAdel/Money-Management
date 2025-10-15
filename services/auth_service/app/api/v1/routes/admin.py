"""
Admin routes - User management and system configuration
Endpoints: /admin/users, /admin/users/{id}, /admin/config
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List

from app.db.session import get_db
from app.db.models.user import User, SystemConfig, UserSession
from app.schemas.user import (
    User as UserSchema, UserUpdate, UserListFilter, UserListResponse,
    SendNotificationRequest, SystemConfigUpdate, SystemConfigResponse,
    MessageResponse
)
from app.api.v1.dependencies import get_current_admin_user
from app.core.security import get_password_hash
import httpx
from app.core.config import settings

router = APIRouter()


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@router.get("/users", response_model=UserListResponse)
async def list_users(
    search: str = None,
    role: str = None,
    is_active: bool = None,
    is_banned: bool = None,
    skip: int = 0,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users with filters and pagination
    """
    query = db.query(User)
    
    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.username.ilike(search_pattern),
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_banned is not None:
        query = query.filter(User.is_banned == is_banned)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return UserListResponse(
        users=[UserSchema.model_validate(u) for u in users],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/users/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user details by ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserSchema.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user details (admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_update.name is not None:
        user.name = user_update.name
    
    if user_update.email is not None:
        # Check if email already exists
        existing = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = user_update.email
    
    if user_update.telegram_id is not None:
        # Check if telegram_id already exists
        existing = db.query(User).filter(
            User.telegram_id == user_update.telegram_id,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram account already linked to another user"
            )
        user.telegram_id = user_update.telegram_id
    
    if user_update.role is not None:
        user.role = user_update.role
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    if user_update.is_banned is not None:
        user.is_banned = user_update.is_banned
        # If banning user, terminate all sessions
        if user_update.is_banned:
            db.query(UserSession).filter(UserSession.user_id == user_id).delete()
    
    db.commit()
    db.refresh(user)
    
    return UserSchema.model_validate(user)


@router.post("/users/{user_id}/ban", response_model=MessageResponse)
async def ban_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Ban user and terminate all sessions
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-ban
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ban yourself"
        )
    
    user.is_banned = True
    db.commit()
    
    # Terminate all user sessions
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()
    db.commit()
    
    return MessageResponse(message=f"User {user.username} has been banned successfully")


@router.post("/users/{user_id}/unban", response_model=MessageResponse)
async def unban_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Unban user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_banned = False
    db.commit()
    
    return MessageResponse(message=f"User {user.username} has been unbanned successfully")


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete user permanently (admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    username = user.username
    db.delete(user)
    db.commit()
    
    return MessageResponse(message=f"User {username} has been deleted successfully")


@router.post("/users/{user_id}/notify", response_model=MessageResponse)
async def send_user_notification(
    user_id: int,
    request: SendNotificationRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Send notification to specific user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            if request.method == "telegram":
                if not user.telegram_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User has no Telegram account linked"
                    )
                await client.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/send-telegram",
                    json={"chat_id": str(user.telegram_id), "message": request.message}
                )
            elif request.method == "email":
                await client.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/send-email",
                    json={
                        "to_email": user.email,
                        "subject": request.subject or "Notification from Admin",
                        "body": request.message
                    }
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )
    
    return MessageResponse(message="Notification sent successfully")


# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================

@router.get("/config/otp", response_model=SystemConfigResponse)
async def get_otp_config(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get OTP configuration
    """
    otp_method_config = db.query(SystemConfig).filter(SystemConfig.key == "otp_method").first()
    otp_expiry_config = db.query(SystemConfig).filter(SystemConfig.key == "otp_expiry_minutes").first()
    
    return SystemConfigResponse(
        otp_method=otp_method_config.value if otp_method_config else "disabled",
        otp_expiry_minutes=int(otp_expiry_config.value) if otp_expiry_config else 5
    )


@router.put("/config/otp", response_model=MessageResponse)
async def update_otp_config(
    config: SystemConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update OTP configuration (admin only)
    """
    # Update OTP method
    otp_method_config = db.query(SystemConfig).filter(SystemConfig.key == "otp_method").first()
    if otp_method_config:
        otp_method_config.value = config.otp_method.value
    else:
        db.add(SystemConfig(
            key="otp_method",
            value=config.otp_method.value,
            description="OTP delivery method: disabled, telegram, or email"
        ))
    
    # Update OTP expiry
    otp_expiry_config = db.query(SystemConfig).filter(SystemConfig.key == "otp_expiry_minutes").first()
    if otp_expiry_config:
        otp_expiry_config.value = str(config.otp_expiry_minutes)
    else:
        db.add(SystemConfig(
            key="otp_expiry_minutes",
            value=str(config.otp_expiry_minutes),
            description="OTP code expiration time in minutes"
        ))
    
    db.commit()
    
    return MessageResponse(message="OTP configuration updated successfully")


@router.get("/stats", response_model=dict)
async def get_system_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get system statistics
    """
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    banned_users = db.query(func.count(User.id)).filter(User.is_banned == True).scalar()
    admin_users = db.query(func.count(User.id)).filter(User.role == "admin").scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "banned_users": banned_users,
        "admin_users": admin_users,
        "inactive_users": total_users - active_users
    }
