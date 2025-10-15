"""
User Pydantic schemas - Enhanced for full auth system
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enum"""
    USER = "user"
    ADMIN = "admin"


class OTPMethod(str, Enum):
    """OTP delivery method"""
    DISABLED = "disabled"
    TELEGRAM = "telegram"
    EMAIL = "email"


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class SignupRequest(BaseModel):
    """Signup/Registration request"""
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    telegram_id: Optional[int] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class LoginRequest(BaseModel):
    """Login request - supports username or email"""
    username_or_email: str = Field(..., min_length=3)
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class VerifyOTPRequest(BaseModel):
    """OTP verification request"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class RequestPasswordResetRequest(BaseModel):
    """Request password reset - sends OTP"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password with OTP"""
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=100)


class ChangePasswordRequest(BaseModel):
    """Change password (authenticated user)"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class DeleteAccountRequest(BaseModel):
    """Delete account confirmation"""
    password: str


class LinkTelegramRequest(BaseModel):
    """Link Telegram account"""
    telegram_id: int


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    """Base user schema"""
    username: str
    name: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user (internal)"""
    password: str
    telegram_id: Optional[int] = None
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    """Schema for updating user (admin)"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    telegram_id: Optional[int] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None


class User(UserBase):
    """User response schema"""
    id: int
    telegram_id: Optional[int] = None
    role: UserRole
    is_active: bool
    is_banned: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserWithGroups(User):
    """User with groups"""
    groups: List['Group'] = []
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# GROUP SCHEMAS
# ============================================================================

class GroupBase(BaseModel):
    """Base group schema"""
    name: str
    description: Optional[str] = None


class GroupCreate(GroupBase):
    """Schema for creating a group"""
    pass


class GroupUpdate(BaseModel):
    """Schema for updating a group"""
    name: Optional[str] = None
    description: Optional[str] = None


class Group(GroupBase):
    """Group response schema"""
    id: int
    created_at: datetime
    members: List[User] = []
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ADMIN SCHEMAS
# ============================================================================

class UserListFilter(BaseModel):
    """Filters for user list"""
    search: Optional[str] = None  # Search in name, username, email
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None
    skip: int = 0
    limit: int = 50


class UserListResponse(BaseModel):
    """Paginated user list response"""
    users: List[User]
    total: int
    skip: int
    limit: int


class SendNotificationRequest(BaseModel):
    """Send notification to user"""
    user_id: int
    method: OTPMethod  # telegram or email
    subject: Optional[str] = None  # For email
    message: str


class SystemConfigUpdate(BaseModel):
    """Update system config"""
    otp_method: OTPMethod
    otp_expiry_minutes: int = Field(default=5, ge=1, le=60)


class SystemConfigResponse(BaseModel):
    """System config response"""
    otp_method: OTPMethod
    otp_expiry_minutes: int


# ============================================================================
# GENERIC SCHEMAS
# ============================================================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None


# Resolve forward references
UserWithGroups.model_rebuild()
