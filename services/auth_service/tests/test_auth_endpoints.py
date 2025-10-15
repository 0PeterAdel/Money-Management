"""
Comprehensive tests for all Authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.models.user import Base, User
from app.db.base import get_db
from app.core.security import get_password_hash
from app.core.config import settings

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth_endpoints.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user(setup_database):
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        name="Test User",
        email="test@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        role="USER",
        is_active=True,
        is_banned=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


class TestSignupEndpoint:
    """Test /api/v1/auth/signup"""
    
    def test_signup_success(self, client):
        response = client.post("/api/v1/auth/signup", json={
            "username": "newuser",
            "name": "New User",
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
        assert "message" in response.json()
    
    def test_signup_duplicate_username(self, client, test_user):
        response = client.post("/api/v1/auth/signup", json={
            "username": "testuser",
            "name": "Another User",
            "email": "another@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_signup_duplicate_email(self, client, test_user):
        response = client.post("/api/v1/auth/signup", json={
            "username": "newuser",
            "name": "New User",
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 400
    
    def test_signup_invalid_email(self, client):
        response = client.post("/api/v1/auth/signup", json={
            "username": "newuser",
            "name": "New User",
            "email": "invalid-email",
            "password": "SecurePass123!"
        })
        assert response.status_code == 422


class TestLoginEndpoint:
    """Test /api/v1/auth/login"""
    
    def test_login_with_username(self, client, test_user):
        response = client.post("/api/v1/auth/login", json={
            "username_or_email": "testuser",
            "password": "TestPassword123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_with_email(self, client, test_user):
        response = client.post("/api/v1/auth/login", json={
            "username_or_email": "test@example.com",
            "password": "TestPassword123!"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_wrong_password(self, client, test_user):
        response = client.post("/api/v1/auth/login", json={
            "username_or_email": "testuser",
            "password": "WrongPassword123!"
        })
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        response = client.post("/api/v1/auth/login", json={
            "username_or_email": "nonexistent",
            "password": "Password123!"
        })
        assert response.status_code == 401  # Returns 401 for invalid credentials
    
    def test_login_inactive_user(self, client):
        db = TestingSessionLocal()
        user = User(
            username="inactiveuser",
            name="Inactive User",
            email="inactive@example.com",
            hashed_password=get_password_hash("Password123!"),
            role="USER",
            is_active=False
        )
        db.add(user)
        db.commit()
        db.close()
        
        response = client.post("/api/v1/auth/login", json={
            "username_or_email": "inactiveuser",
            "password": "Password123!"
        })
        assert response.status_code == 403
        assert "not activated" in response.json()["detail"].lower()
    
    def test_login_banned_user(self, client):
        db = TestingSessionLocal()
        user = User(
            username="banneduser",
            name="Banned User",
            email="banned@example.com",
            hashed_password=get_password_hash("Password123!"),
            role="USER",
            is_active=True,
            is_banned=True
        )
        db.add(user)
        db.commit()
        db.close()
        
        response = client.post("/api/v1/auth/login", json={
            "username_or_email": "banneduser",
            "password": "Password123!"
        })
        assert response.status_code == 403
        assert "banned" in response.json()["detail"].lower()


class TestRefreshTokenEndpoint:
    """Test /api/v1/auth/refresh"""
    
    def test_refresh_token_success(self, client, test_user):
        # First login to get refresh token
        login_response = client.post("/api/v1/auth/login", json={
            "username_or_email": "testuser",
            "password": "TestPassword123!"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Now refresh
        response = client.post("/api/v1/auth/refresh", params={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_token_invalid(self, client):
        response = client.post("/api/v1/auth/refresh", params={"refresh_token": "invalid_token"})
        assert response.status_code == 401


class TestPasswordResetEndpoints:
    """Test /api/v1/auth/request-password-reset and /api/v1/auth/reset-password"""
    
    def test_request_password_reset(self, client, test_user):
        response = client.post("/api/v1/auth/request-password-reset", json={
            "email": "test@example.com"
        })
        assert response.status_code == 200
        assert "reset" in response.json()["message"].lower()
    
    def test_request_password_reset_nonexistent_email(self, client):
        response = client.post("/api/v1/auth/request-password-reset", json={
            "email": "nonexistent@example.com"
        })
        # API returns 200 even for non-existent emails for security reasons
        assert response.status_code == 200
    
    def test_reset_password_success(self, client, test_user):
        from app.db.models.user import OTPCode
        # First request reset
        client.post("/api/v1/auth/request-password-reset", json={
            "email": "test@example.com"
        })
        
        # Get OTP from database
        db = TestingSessionLocal()
        otp_record = db.query(OTPCode).filter(OTPCode.user_id == test_user.id).order_by(OTPCode.created_at.desc()).first()
        otp_code = otp_record.code if otp_record else "000000"
        db.close()
        
        # Reset password
        response = client.post("/api/v1/auth/reset-password", json={
            "email": "test@example.com",
            "otp_code": otp_code,
            "new_password": "NewPassword123!"
        })
        assert response.status_code == 200
        assert "successful" in response.json()["message"].lower()
    
    def test_reset_password_invalid_otp(self, client, test_user):
        response = client.post("/api/v1/auth/reset-password", json={
            "email": "test@example.com",
            "otp_code": "000000",
            "new_password": "NewPassword123!"
        })
        assert response.status_code == 400


class TestChangePasswordEndpoint:
    """Test /api/v1/auth/change-password"""
    
    def test_change_password_success(self, client, test_user):
        # Login first
        login_response = client.post("/api/v1/auth/login", json={
            "username_or_email": "testuser",
            "password": "TestPassword123!"
        })
        token = login_response.json()["access_token"]
        
        # Change password
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "TestPassword123!",
                "new_password": "NewPassword123!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "successful" in response.json()["message"].lower()
    
    def test_change_password_wrong_current(self, client, test_user):
        login_response = client.post("/api/v1/auth/login", json={
            "username_or_email": "testuser",
            "password": "TestPassword123!"
        })
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "WrongPassword!",
                "new_password": "NewPassword123!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
    
    def test_change_password_unauthorized(self, client):
        response = client.post("/api/v1/auth/change-password", json={
            "old_password": "OldPass123!",
            "new_password": "NewPass123!"
        })
        # Returns 403 when no valid token provided
        assert response.status_code in [401, 403]


class TestDeleteAccountEndpoint:
    """Test /api/v1/auth/delete-account"""
    
    def test_delete_account_success(self, client, test_user):
        login_response = client.post("/api/v1/auth/login", json={
            "username_or_email": "testuser",
            "password": "TestPassword123!"
        })
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/v1/auth/delete-account",
            json={"password": "TestPassword123!"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()
    
    def test_delete_account_wrong_password(self, client, test_user):
        login_response = client.post("/api/v1/auth/login", json={
            "username_or_email": "testuser",
            "password": "TestPassword123!"
        })
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/v1/auth/delete-account",
            json={"password": "WrongPassword!"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400


class TestLogoutEndpoint:
    """Test /api/v1/auth/logout"""
    
    def test_logout_success(self, client, test_user):
        login_response = client.post("/api/v1/auth/login", json={
            "username_or_email": "testuser",
            "password": "TestPassword123!"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        response = client.post("/api/v1/auth/logout", params={"refresh_token": refresh_token})
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
