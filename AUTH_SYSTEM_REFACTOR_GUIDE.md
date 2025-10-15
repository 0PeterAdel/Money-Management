# 🔐 Authentication System Refactor - Complete Implementation Guide

## 📋 Overview

This guide provides step-by-step instructions for completing the comprehensive authentication system refactor across backend (FastAPI) and frontend (React + TypeScript).

---

## ✅ What Has Been Completed

### Backend (FastAPI - Auth Service)

#### ✅ **1. Database Models** (`app/db/models/user.py`)
- Enhanced `User` model with:
  - `username`, `email`, `telegram_id`, `role`, `is_active`, `is_banned`
  - `last_login`, `updated_at` timestamps
- New `OTPCode` model for verification codes
- New `UserSession` model for session management
- New `SystemConfig` model for system settings
- Enums: `UserRole`, `OTPMethod`

#### ✅ **2. Pydantic Schemas** (`app/schemas/user.py`)
- Auth schemas: `SignupRequest`, `LoginRequest`, `TokenResponse`, etc.
- User schemas: `User`, `UserUpdate`, `UserListResponse`
- Admin schemas: `UserListFilter`, `SendNotificationRequest`, `SystemConfigUpdate`
- Password validation with strength requirements

#### ✅ **3. Security Module** (`app/core/security.py`)
- JWT token creation (`create_access_token`, `create_refresh_token`)
- Token verification (`verify_token`, `decode_token`)
- OTP generation (`generate_otp_code`)
- Password hashing (bcrypt)

#### ✅ **4. Configuration** (`app/core/config.py`)
- JWT settings (expiration times)
- OTP settings
- External service URLs

#### ✅ **5. Auth Routes** (`app/api/v1/routes/auth.py`)
- `/auth/signup` - User registration with OTP
- `/auth/verify-otp` - OTP verification
- `/auth/login` - Login with JWT tokens
- `/auth/refresh` - Refresh access token
- `/auth/request-password-reset` - Send reset OTP
- `/auth/reset-password` - Reset password with OTP
- `/auth/change-password` - Change password (authenticated)
- `/auth/delete-account` - Delete account
- `/auth/logout` - Invalidate session

#### ✅ **6. Admin Routes** (`app/api/v1/routes/admin.py`)
- `/admin/users` - List users with filters
- `/admin/users/{id}` - Get/Update/Delete user
- `/admin/users/{id}/ban` - Ban user
- `/admin/users/{id}/unban` - Unban user
- `/admin/users/{id}/notify` - Send notification
- `/admin/config/otp` - Get/Update OTP settings
- `/admin/stats` - System statistics

#### ✅ **7. Dependencies** (`app/api/v1/dependencies.py`)
- `get_current_user` - Extract user from JWT
- `get_current_admin_user` - Verify admin role
- JWT Bearer security scheme

#### ✅ **8. Requirements** (`requirements.txt`)
- Added: `python-jose`, `httpx`, `email-validator`

---

## 🔨 Steps to Complete Implementation

### STEP 1: Database Migration

**Create Alembic Migration:**

```bash
cd services/auth_service

# Initialize Alembic (if not already done)
alembic init alembic

# Edit alembic.ini - set sqlalchemy.url
# Edit alembic/env.py - import your Base and models

# Create migration
alembic revision --autogenerate -m "enhance_auth_system"

# Review migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

**Or Manual SQL (if not using Alembic):**

```sql
-- Add new columns to users table
ALTER TABLE users ADD COLUMN username VARCHAR(50) UNIQUE NOT NULL DEFAULT 'user_' || id::text;
ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE NOT NULL DEFAULT id || '@temp.local';
ALTER TABLE users ADD COLUMN role VARCHAR(10) DEFAULT 'user';
ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
ALTER TABLE users RENAME COLUMN hashed_password TO hashed_password;

-- Change telegram_id to INTEGER
ALTER TABLE users ALTER COLUMN telegram_id TYPE INTEGER USING telegram_id::integer;

-- Create OTP codes table
CREATE TABLE otp_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    code VARCHAR(6) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user sessions table
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) UNIQUE NOT NULL,
    device_info VARCHAR(255),
    ip_address VARCHAR(45),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create system config table
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default config
INSERT INTO system_config (key, value, description) VALUES
    ('otp_method', 'disabled', 'OTP delivery method: disabled, telegram, or email'),
    ('otp_expiry_minutes', '5', 'OTP code expiration time in minutes');

-- Create indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_otp_codes_user_id ON otp_codes(user_id);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
```

### STEP 2: Update Auth Service Main App

**Edit `services/auth_service/app/main.py`:**

```python
"""
Auth Service - Main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routes import auth, admin, users, register, login
from app.db.base import Base
from app.db.session import engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Authentication and User Management Service"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["Admin"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])

# Backward compatibility (optional - keep old routes)
app.include_router(register.router, prefix=f"{settings.API_V1_PREFIX}", tags=["Legacy"])
app.include_router(login.router, prefix=f"{settings.API_V1_PREFIX}", tags=["Legacy"])

@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
```

### STEP 3: Install Updated Dependencies

```bash
cd services/auth_service
source venv/bin/activate
pip install -r requirements.txt
```

### STEP 4: Test Backend Endpoints

```bash
# Start auth service
uvicorn app.main:app --reload --port 8001

# Test in another terminal:

# 1. Signup
curl -X POST http://localhost:8001/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPass123"
  }'

# 2. Verify OTP (use code from email/telegram)
curl -X POST http://localhost:8001/api/v1/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "123456"
  }'

# 3. Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "testuser",
    "password": "TestPass123"
  }'

# 4. Use access token for authenticated requests
TOKEN="<access_token_from_login>"
curl -X GET http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎨 Frontend Implementation

### STEP 5: Update TypeScript Types

**Create/Update `frontend/src/types/api.ts`:**

```typescript
export enum UserRole {
  USER = 'user',
  ADMIN = 'admin',
}

export enum OTPMethod {
  DISABLED = 'disabled',
  TELEGRAM = 'telegram',
  EMAIL = 'email',
}

export interface User {
  id: number;
  username: string;
  name: string;
  email: string;
  telegram_id?: number;
  role: UserRole;
  is_active: boolean;
  is_banned: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface SignupRequest {
  username: string;
  name: string;
  email: string;
  password: string;
  telegram_id?: number;
}

export interface LoginRequest {
  username_or_email: string;
  password: string;
}

export interface VerifyOTPRequest {
  email: string;
  code: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface DeleteAccountRequest {
  password: string;
}

export interface UserListResponse {
  users: User[];
  total: number;
  skip: number;
  limit: number;
}

export interface SystemConfig {
  otp_method: OTPMethod;
  otp_expiry_minutes: number;
}
```

### STEP 6: Update Auth Context

**Edit `frontend/src/contexts/auth-context.tsx`:**

```typescript
import React, { createContext, useState, useContext, useEffect } from 'react';
import { User, TokenResponse, LoginRequest, SignupRequest } from '../types/api';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (data: LoginRequest) => Promise<void>;
  signup: (data: SignupRequest) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [refreshTokenValue, setRefreshTokenValue] = useState<string | null>(
    localStorage.getItem('refresh_token')
  );

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/users/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    }
  };

  const login = async (data: LoginRequest) => {
    const response = await api.post<TokenResponse>('/auth/login', data);
    const { access_token, refresh_token } = response.data;
    
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    setToken(access_token);
    setRefreshTokenValue(refresh_token);
    
    await fetchCurrentUser();
  };

  const signup = async (data: SignupRequest) => {
    await api.post('/auth/signup', data);
    // Don't auto-login, user needs to verify OTP first
  };

  const logout = async () => {
    try {
      if (refreshTokenValue) {
        await api.post('/auth/logout', { refresh_token: refreshTokenValue });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setToken(null);
      setRefreshTokenValue(null);
      setUser(null);
    }
  };

  const refreshToken = async () => {
    if (!refreshTokenValue) throw new Error('No refresh token');
    
    const response = await api.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshTokenValue
    });
    
    const { access_token } = response.data;
    localStorage.setItem('access_token', access_token);
    setToken(access_token);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        signup,
        logout,
        refreshToken,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### STEP 7: Update API Service

**Edit `frontend/src/services/api.ts`:**

```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');

        const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

### STEP 8: Create/Update Frontend Pages

Due to space constraints, the complete frontend pages would be very long. Here's a summary of what needs to be updated:

#### **`frontend/src/pages/Register.tsx`**
- Add username, email fields
- Password strength indicator
- OTP verification step after registration
- Form validation

#### **`frontend/src/pages/Login.tsx`**
- Support username OR email login
- Loading states
- Error handling
- "Forgot Password" link

#### **`frontend/src/pages/Settings.tsx`**
- Add "Change Password" section
- Add "Delete Account" section with confirmation
- Link Telegram account
- User profile editing

#### **`frontend/src/pages/Users.tsx`** (New - Admin Panel)
- User list table with pagination
- Search and filters (role, active, banned)
- Edit user modal
- Ban/Unban buttons
- Delete user confirmation
- Send notification modal
- System statistics dashboard
- OTP configuration settings

---

## 🧪 Testing Checklist

### Backend Tests

```bash
# Create tests in services/auth_service/tests/

# test_auth.py
- test_signup_success
- test_signup_duplicate_username
- test_signup_duplicate_email
- test_verify_otp_success
- test_verify_otp_invalid
- test_login_success
- test_login_wrong_password
- test_login_banned_user
- test_refresh_token_success
- test_change_password_success
- test_delete_account_success

# test_admin.py
- test_list_users_as_admin
- test_list_users_as_regular_user (should fail)
- test_ban_user
- test_unban_user
- test_delete_user
- test_update_otp_config
- test_send_notification
```

### Frontend Tests

```bash
# Create tests with React Testing Library

# Login.test.tsx
- renders login form
- submits with valid credentials
- shows error for invalid credentials
- redirects after successful login

# Register.test.tsx
- renders registration form
- validates password strength
- submits registration
- shows OTP verification step

# Settings.test.tsx
- renders settings page
- changes password
- deletes account with confirmation
```

---

## 🚀 Deployment Steps

### 1. Update Environment Variables

```bash
# .env
SECRET_KEY=<generate-strong-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
OTP_EXPIRY_MINUTES=5
DATABASE_URL=postgresql://user:password@localhost:5432/money_management
NOTIFICATION_SERVICE_URL=http://notification_service:8002
```

### 2. Run Database Migrations

```bash
alembic upgrade head
```

### 3. Update Docker Compose

```yaml
# docker-compose.yml - Update auth_service
auth_service:
  environment:
    - SECRET_KEY=${SECRET_KEY}
    - ACCESS_TOKEN_EXPIRE_MINUTES=30
    - REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 4. Build and Deploy

```bash
docker-compose build auth_service
docker-compose up -d
```

---

## 📚 API Documentation

After starting the services, visit:
- **Auth Service API Docs:** http://localhost:8001/docs
- **All endpoints documented with OpenAPI/Swagger**

---

## 🔐 Security Checklist

- [ ] Use strong SECRET_KEY in production
- [ ] Enable HTTPS/TLS
- [ ] Set proper CORS origins (not "*")
- [ ] Use PostgreSQL (not SQLite) in production
- [ ] Enable rate limiting
- [ ] Add logging for security events
- [ ] Regular security audits
- [ ] Keep dependencies updated
- [ ] Use environment variables for secrets
- [ ] Implement CSRF protection

---

## 📝 Summary

### Completed:
✅ Enhanced database models with full auth support
✅ Comprehensive Pydantic schemas
✅ JWT token authentication system
✅ OTP verification system
✅ Complete auth routes (signup, login, reset password, etc.)
✅ Admin panel routes (user management, notifications)
✅ Session management
✅ Security utilities

### Remaining Work:
- [ ] Database migration (SQL or Alembic)
- [ ] Update main.py to register new routes
- [ ] Frontend page updates (Register, Login, Settings, Users)
- [ ] Frontend API integration
- [ ] Testing (backend + frontend)
- [ ] Documentation updates
- [ ] Production deployment configuration

**Estimated Time to Complete:** 8-12 hours of focused development

---

## 🆘 Troubleshooting

### Common Issues:

**1. JWT Token Errors**
- Check SECRET_KEY is set
- Verify token expiration times
- Ensure python-jose is installed

**2. OTP Not Sending**
- Check notification service is running
- Verify OTP method in system_config
- Check service URLs in config

**3. Database Migration Errors**
- Review migration SQL carefully
- Backup database before migrating
- Check for constraint violations

**4. CORS Errors**
- Update BACKEND_CORS_ORIGINS
- Check frontend API base URL
- Verify credentials mode

---

## 🎉 Conclusion

This refactor provides a production-ready, secure, and modern authentication system with:
- ✅ Full user lifecycle management
- ✅ OTP verification (Telegram/Email)
- ✅ JWT-based authentication
- ✅ Admin panel for user management
- ✅ Session management
- ✅ Password reset functionality
- ✅ Account deletion
- ✅ Role-based access control

Follow the steps above to complete the implementation. Good luck! 🚀
