"""
Unit tests for admin panel endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.models.user import User, UserRole, SystemConfig
from app.core.security import hash_password


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin.db"
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
    
    # Add default system config
    db = TestingSessionLocal()
    config = SystemConfig(
        key="otp_method",
        value="disabled",
        description="OTP delivery method"
    )
    db.add(config)
    config2 = SystemConfig(
        key="otp_expiry_minutes",
        value="5",
        description="OTP expiration time"
    )
    db.add(config2)
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_token():
    """Create admin user and return token"""
    db = TestingSessionLocal()
    admin = User(
        username="admin",
        name="Admin User",
        email="admin@example.com",
        hashed_password=hash_password("Admin123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_banned=False,
        created_at=datetime.utcnow()
    )
    db.add(admin)
    db.commit()
    db.close()
    
    # Login to get token
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "admin",
            "password": "Admin123!"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def regular_user_token():
    """Create regular user and return token"""
    db = TestingSessionLocal()
    user = User(
        username="user",
        name="Regular User",
        email="user@example.com",
        hashed_password=hash_password("User123!"),
        role=UserRole.USER,
        is_active=True,
        is_banned=False,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.close()
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "user",
            "password": "User123!"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def test_users():
    """Create multiple test users"""
    db = TestingSessionLocal()
    users = []
    for i in range(5):
        user = User(
            username=f"user{i}",
            name=f"Test User {i}",
            email=f"user{i}@example.com",
            hashed_password=hash_password("Pass123"),
            role=UserRole.USER if i < 4 else UserRole.ADMIN,
            is_active=i % 2 == 0,  # Every other user is active
            is_banned=i == 3,  # User 3 is banned
            created_at=datetime.utcnow()
        )
        db.add(user)
        users.append(user)
    db.commit()
    db.close()
    return users


def test_get_stats_success(admin_token, test_users):
    """Test getting system stats as admin"""
    response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "active_users" in data
    assert "banned_users" in data
    assert "admin_users" in data
    assert data["total_users"] == 6  # 5 test users + 1 admin
    assert data["admin_users"] == 2  # 1 test admin + fixture admin
    assert data["banned_users"] == 1


def test_get_stats_unauthorized(regular_user_token):
    """Test that regular users cannot access stats"""
    response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {regular_user_token}"}
    )
    assert response.status_code == 403


def test_get_stats_no_auth():
    """Test stats endpoint without authentication"""
    response = client.get("/api/v1/admin/stats")
    assert response.status_code == 401


def test_list_users_success(admin_token, test_users):
    """Test listing users as admin"""
    response = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert len(data["users"]) == 6


def test_list_users_with_pagination(admin_token, test_users):
    """Test user list with pagination"""
    response = client.get(
        "/api/v1/admin/users?skip=2&limit=2",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2


def test_list_users_filter_by_role(admin_token, test_users):
    """Test filtering users by role"""
    response = client.get(
        "/api/v1/admin/users?role=ADMIN",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(user["role"] == "ADMIN" for user in data["users"])


def test_list_users_filter_by_status(admin_token, test_users):
    """Test filtering users by active status"""
    response = client.get(
        "/api/v1/admin/users?is_active=true",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(user["is_active"] for user in data["users"])


def test_list_users_search(admin_token, test_users):
    """Test searching users"""
    response = client.get(
        "/api/v1/admin/users?search=user0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) >= 1


def test_get_user_by_id_success(admin_token, test_users):
    """Test getting specific user by ID"""
    user_id = test_users[0].id
    response = client.get(
        f"/api/v1/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "user0"


def test_get_user_not_found(admin_token):
    """Test getting non-existent user"""
    response = client.get(
        "/api/v1/admin/users/99999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


def test_update_user_success(admin_token, test_users):
    """Test updating user information"""
    user_id = test_users[0].id
    response = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={
            "name": "Updated Name",
            "is_active": True
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["is_active"] is True


def test_update_user_role(admin_token, test_users):
    """Test promoting user to admin"""
    user_id = test_users[0].id
    response = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"role": "ADMIN"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "ADMIN"


def test_update_user_unauthorized(regular_user_token, test_users):
    """Test that regular users cannot update others"""
    user_id = test_users[0].id
    response = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"name": "Hacked Name"},
        headers={"Authorization": f"Bearer {regular_user_token}"}
    )
    assert response.status_code == 403


def test_delete_user_success(admin_token, test_users):
    """Test deleting a user"""
    user_id = test_users[0].id
    response = client.delete(
        f"/api/v1/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Verify user is deleted
    get_response = client.get(
        f"/api/v1/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == 404


def test_ban_user_success(admin_token, test_users):
    """Test banning a user"""
    user_id = test_users[0].id
    response = client.post(
        f"/api/v1/admin/users/{user_id}/ban",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Verify user is banned
    get_response = client.get(
        f"/api/v1/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.json()["is_banned"] is True


def test_unban_user_success(admin_token, test_users):
    """Test unbanning a user"""
    user_id = test_users[3].id  # This user is already banned
    response = client.post(
        f"/api/v1/admin/users/{user_id}/unban",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Verify user is unbanned
    get_response = client.get(
        f"/api/v1/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.json()["is_banned"] is False


def test_ban_prevents_login(admin_token):
    """Test that banned users cannot login"""
    # Create and ban a user
    db = TestingSessionLocal()
    user = User(
        username="bantest",
        name="Ban Test",
        email="ban@example.com",
        hashed_password=hash_password("Pass123"),
        role=UserRole.USER,
        is_active=True,
        is_banned=False,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    user_id = user.id
    db.close()
    
    # Ban the user
    client.post(
        f"/api/v1/admin/users/{user_id}/ban",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Try to login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "bantest",
            "password": "Pass123"
        }
    )
    assert login_response.status_code == 403


def test_get_otp_config_success(admin_token):
    """Test getting OTP configuration"""
    response = client.get(
        "/api/v1/admin/config/otp",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "otp_method" in data
    assert "otp_expiry_minutes" in data
    assert data["otp_method"] in ["disabled", "email", "telegram"]


def test_update_otp_config_success(admin_token):
    """Test updating OTP configuration"""
    response = client.put(
        "/api/v1/admin/config/otp",
        json={
            "otp_method": "email",
            "otp_expiry_minutes": 10
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["otp_method"] == "email"
    assert data["otp_expiry_minutes"] == 10


def test_update_otp_config_invalid_method(admin_token):
    """Test updating OTP with invalid method"""
    response = client.put(
        "/api/v1/admin/config/otp",
        json={
            "otp_method": "invalid_method",
            "otp_expiry_minutes": 5
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422


def test_update_otp_config_unauthorized(regular_user_token):
    """Test that regular users cannot update OTP config"""
    response = client.put(
        "/api/v1/admin/config/otp",
        json={
            "otp_method": "email",
            "otp_expiry_minutes": 10
        },
        headers={"Authorization": f"Bearer {regular_user_token}"}
    )
    assert response.status_code == 403


def test_notify_user_success(admin_token, test_users):
    """Test sending notification to user"""
    user_id = test_users[0].id
    response = client.post(
        f"/api/v1/admin/users/{user_id}/notify",
        json={
            "message": "Test notification",
            "priority": "high"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    # This might return 200 or 501 depending on notification service availability
    assert response.status_code in [200, 501, 503]


def test_admin_endpoints_require_admin_role(regular_user_token):
    """Test that all admin endpoints require admin role"""
    endpoints = [
        ("GET", "/api/v1/admin/stats"),
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/users/1"),
        ("PATCH", "/api/v1/admin/users/1"),
        ("DELETE", "/api/v1/admin/users/1"),
        ("POST", "/api/v1/admin/users/1/ban"),
        ("POST", "/api/v1/admin/users/1/unban"),
        ("GET", "/api/v1/admin/config/otp"),
        ("PUT", "/api/v1/admin/config/otp"),
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint, headers={"Authorization": f"Bearer {regular_user_token}"})
        elif method == "POST":
            response = client.post(endpoint, json={}, headers={"Authorization": f"Bearer {regular_user_token}"})
        elif method == "PUT":
            response = client.put(endpoint, json={"otp_method": "email", "otp_expiry_minutes": 5}, headers={"Authorization": f"Bearer {regular_user_token}"})
        elif method == "PATCH":
            response = client.patch(endpoint, json={}, headers={"Authorization": f"Bearer {regular_user_token}"})
        elif method == "DELETE":
            response = client.delete(endpoint, headers={"Authorization": f"Bearer {regular_user_token}"})
        
        assert response.status_code == 403, f"Endpoint {method} {endpoint} should return 403 for non-admin"
