"""
Unit tests for authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.core.security import hash_password


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """Create a test user"""
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        name="Test User",
        email="test@example.com",
        hashed_password=hash_password("TestPass123"),
        role=UserRole.USER,
        is_active=True,
        is_banned=False,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def admin_user():
    """Create an admin user"""
    db = TestingSessionLocal()
    user = User(
        username="admin",
        name="Admin User",
        email="admin@example.com",
        hashed_password=hash_password("Admin123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_banned=False,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_signup_success():
    """Test successful user registration"""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "username": "newuser",
            "name": "New User",
            "email": "new@example.com",
            "password": "NewPass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "created" in data["message"].lower() or "verification" in data["message"].lower()


def test_signup_duplicate_username():
    """Test signup with duplicate username"""
    # Create first user
    client.post(
        "/api/v1/auth/signup",
        json={
            "username": "duplicate",
            "name": "First User",
            "email": "first@example.com",
            "password": "Pass123"
        }
    )
    
    # Try to create user with same username
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "username": "duplicate",
            "name": "Second User",
            "email": "second@example.com",
            "password": "Pass123"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_signup_duplicate_email():
    """Test signup with duplicate email"""
    # Create first user
    client.post(
        "/api/v1/auth/signup",
        json={
            "username": "user1",
            "name": "First User",
            "email": "same@example.com",
            "password": "Pass123"
        }
    )
    
    # Try to create user with same email
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "username": "user2",
            "name": "Second User",
            "email": "same@example.com",
            "password": "Pass123"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_login_success(test_user):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "TestPass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_with_email(test_user):
    """Test login using email instead of username"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "test@example.com",
            "password": "TestPass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_wrong_password(test_user):
    """Test login with incorrect password"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "WrongPassword"
        }
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user():
    """Test login with non-existent user"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "nonexistent",
            "password": "AnyPassword"
        }
    )
    assert response.status_code == 401


def test_login_banned_user():
    """Test login with banned user"""
    # Create banned user
    db = TestingSessionLocal()
    user = User(
        username="banned",
        name="Banned User",
        email="banned@example.com",
        hashed_password=hash_password("Pass123"),
        role=UserRole.USER,
        is_active=True,
        is_banned=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.close()
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "banned",
            "password": "Pass123"
        }
    )
    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_login_inactive_user():
    """Test login with inactive user"""
    # Create inactive user
    db = TestingSessionLocal()
    user = User(
        username="inactive",
        name="Inactive User",
        email="inactive@example.com",
        hashed_password=hash_password("Pass123"),
        role=UserRole.USER,
        is_active=False,
        is_banned=False,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.close()
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "inactive",
            "password": "Pass123"
        }
    )
    assert response.status_code == 403
    assert "not activated" in response.json()["detail"].lower()


def test_change_password_success(test_user):
    """Test successful password change"""
    # Login first
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "TestPass123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Change password
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "TestPass123",
            "new_password": "NewPass456"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Try logging in with new password
    new_login = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "NewPass456"
        }
    )
    assert new_login.status_code == 200


def test_change_password_wrong_current(test_user):
    """Test password change with wrong current password"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "TestPass123"
        }
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "WrongPassword",
            "new_password": "NewPass456"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400 or response.status_code == 401


def test_change_password_unauthorized():
    """Test password change without authentication"""
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "OldPass",
            "new_password": "NewPass"
        }
    )
    assert response.status_code == 401


def test_delete_account_success(test_user):
    """Test successful account deletion"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "TestPass123"
        }
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/api/v1/auth/delete-account",
        json={"password": "TestPass123"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Try logging in again - should fail
    login_again = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "TestPass123"
        }
    )
    assert login_again.status_code == 401


def test_delete_account_wrong_password(test_user):
    """Test account deletion with wrong password"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "TestPass123"
        }
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/api/v1/auth/delete-account",
        json={"password": "WrongPassword"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400 or response.status_code == 401


def test_refresh_token(test_user):
    """Test token refresh"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "TestPass123"
        }
    )
    refresh_token = login_response.json()["refresh_token"]
    
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout(test_user):
    """Test logout"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "TestPass123"
        }
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
