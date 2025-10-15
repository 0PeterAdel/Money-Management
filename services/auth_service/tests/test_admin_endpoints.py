"""
Comprehensive tests for all Admin endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.models.user import Base, User
from app.db.base import get_db
from app.core.security import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin_endpoints.db"
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
def admin_user(setup_database):
    db = TestingSessionLocal()
    admin = User(
        username="admin",
        name="Admin User",
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        role="ADMIN",
        is_active=True,
        is_banned=False
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return admin

@pytest.fixture
def regular_user(setup_database):
    db = TestingSessionLocal()
    user = User(
        username="user",
        name="Regular User",
        email="user@example.com",
        hashed_password=get_password_hash("UserPass123!"),
        role="USER",
        is_active=True,
        is_banned=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def admin_token(client, admin_user):
    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "admin",
        "password": "AdminPass123!"
    })
    return response.json()["access_token"]

@pytest.fixture
def user_token(client, regular_user):
    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "user",
        "password": "UserPass123!"
    })
    return response.json()["access_token"]


class TestListUsersEndpoint:
    """Test GET /api/v1/admin/users"""
    
    def test_list_users_success(self, client, admin_token, admin_user, regular_user):
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert len(data["users"]) >= 2
    
    def test_list_users_with_search(self, client, admin_token, admin_user, regular_user):
        response = client.get(
            "/api/v1/admin/users?search=Regular",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) >= 1
        assert any("Regular" in user["name"] for user in data["users"])
    
    def test_list_users_with_role_filter(self, client, admin_token, admin_user, regular_user):
        response = client.get(
            "/api/v1/admin/users?role=ADMIN",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert all(user["role"] == "ADMIN" for user in data["users"])
    
    def test_list_users_unauthorized(self, client, user_token):
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_list_users_no_token(self, client):
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401


class TestGetUserEndpoint:
    """Test GET /api/v1/admin/users/{user_id}"""
    
    def test_get_user_success(self, client, admin_token, regular_user):
        response = client.get(
            f"/api/v1/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "user"
        assert data["email"] == "user@example.com"
    
    def test_get_user_not_found(self, client, admin_token):
        response = client.get(
            "/api/v1/admin/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
    
    def test_get_user_unauthorized(self, client, user_token, regular_user):
        response = client.get(
            f"/api/v1/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403


class TestUpdateUserEndpoint:
    """Test PATCH /api/v1/admin/users/{user_id}"""
    
    def test_update_user_name(self, client, admin_token, regular_user):
        response = client.patch(
            f"/api/v1/admin/users/{regular_user.id}",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
    
    def test_update_user_role(self, client, admin_token, regular_user):
        response = client.patch(
            f"/api/v1/admin/users/{regular_user.id}",
            json={"role": "ADMIN"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "ADMIN"
    
    def test_update_user_telegram(self, client, admin_token, regular_user):
        response = client.patch(
            f"/api/v1/admin/users/{regular_user.id}",
            json={"telegram_id": "123456789"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["telegram_id"] == "123456789"
    
    def test_update_user_not_found(self, client, admin_token):
        response = client.patch(
            "/api/v1/admin/users/99999",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
    
    def test_update_user_unauthorized(self, client, user_token, regular_user):
        response = client.patch(
            f"/api/v1/admin/users/{regular_user.id}",
            json={"name": "Hacker Name"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403


class TestBanUserEndpoint:
    """Test POST /api/v1/admin/users/{user_id}/ban"""
    
    def test_ban_user_success(self, client, admin_token, regular_user):
        response = client.post(
            f"/api/v1/admin/users/{regular_user.id}/ban",
            json={"reason": "Violation of terms"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "banned" in response.json()["message"].lower()
        
        # Verify user is banned
        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == regular_user.id).first()
        assert user.is_banned == True
        assert user.ban_reason == "Violation of terms"
        db.close()
    
    def test_ban_already_banned_user(self, client, admin_token, regular_user):
        # Ban first time
        client.post(
            f"/api/v1/admin/users/{regular_user.id}/ban",
            json={"reason": "First ban"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Try to ban again
        response = client.post(
            f"/api/v1/admin/users/{regular_user.id}/ban",
            json={"reason": "Second ban"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "already banned" in response.json()["detail"].lower()
    
    def test_ban_self(self, client, admin_token, admin_user):
        response = client.post(
            f"/api/v1/admin/users/{admin_user.id}/ban",
            json={"reason": "Self ban"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "yourself" in response.json()["detail"].lower()
    
    def test_ban_user_unauthorized(self, client, user_token, regular_user):
        response = client.post(
            f"/api/v1/admin/users/{regular_user.id}/ban",
            json={"reason": "Unauthorized ban"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403


class TestUnbanUserEndpoint:
    """Test POST /api/v1/admin/users/{user_id}/unban"""
    
    def test_unban_user_success(self, client, admin_token, regular_user):
        # Ban user first
        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == regular_user.id).first()
        user.is_banned = True
        user.ban_reason = "Test ban"
        db.commit()
        db.close()
        
        # Unban
        response = client.post(
            f"/api/v1/admin/users/{regular_user.id}/unban",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "unbanned" in response.json()["message"].lower()
    
    def test_unban_not_banned_user(self, client, admin_token, regular_user):
        response = client.post(
            f"/api/v1/admin/users/{regular_user.id}/unban",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "not banned" in response.json()["detail"].lower()


class TestDeleteUserEndpoint:
    """Test DELETE /api/v1/admin/users/{user_id}"""
    
    def test_delete_user_success(self, client, admin_token, regular_user):
        response = client.delete(
            f"/api/v1/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()
        
        # Verify user is deleted
        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == regular_user.id).first()
        assert user is None
        db.close()
    
    def test_delete_self(self, client, admin_token, admin_user):
        response = client.delete(
            f"/api/v1/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "yourself" in response.json()["detail"].lower()
    
    def test_delete_user_not_found(self, client, admin_token):
        response = client.delete(
            "/api/v1/admin/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404


class TestNotifyUserEndpoint:
    """Test POST /api/v1/admin/users/{user_id}/notify"""
    
    def test_notify_user_success(self, client, admin_token, regular_user):
        response = client.post(
            f"/api/v1/admin/users/{regular_user.id}/notify",
            json={"message": "Test notification", "priority": "high"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "notification" in response.json()["message"].lower()


class TestOTPConfigEndpoints:
    """Test GET/PUT /api/v1/admin/config/otp"""
    
    def test_get_otp_config(self, client, admin_token):
        response = client.get(
            "/api/v1/admin/config/otp",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "otp_method" in data
        assert "otp_expiry_minutes" in data
    
    def test_update_otp_config(self, client, admin_token):
        response = client.put(
            "/api/v1/admin/config/otp",
            json={"otp_method": "email", "otp_expiry_minutes": 10},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
    
    def test_otp_config_unauthorized(self, client, user_token):
        response = client.get(
            "/api/v1/admin/config/otp",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403


class TestSystemStatsEndpoint:
    """Test GET /api/v1/admin/stats"""
    
    def test_get_stats_success(self, client, admin_token, admin_user, regular_user):
        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "inactive_users" in data
        assert "banned_users" in data
        assert "admin_users" in data
        assert data["total_users"] >= 2
    
    def test_get_stats_unauthorized(self, client, user_token):
        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
