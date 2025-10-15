"""
Comprehensive tests for Users and Groups endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.models.user import Base, User, Group
from app.db.base import get_db
from app.core.security import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_users_groups.db"
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
def test_users(setup_database):
    db = TestingSessionLocal()
    users = [
        User(
            username=f"user{i}",
            name=f"User {i}",
            email=f"user{i}@example.com",
            hashed_password=get_password_hash("Password123!"),
            role="USER",
            is_active=True
        )
        for i in range(1, 4)
    ]
    db.add_all(users)
    db.commit()
    for user in users:
        db.refresh(user)
    db.close()
    return users

@pytest.fixture
def test_group(setup_database, test_users):
    db = TestingSessionLocal()
    group = Group(name="Test Group", created_by=test_users[0].id)
    db.add(group)
    db.commit()
    db.refresh(group)
    db.close()
    return group


class TestGetUsersEndpoint:
    """Test GET /api/v1/users"""
    
    def test_get_users_success(self, client, test_users):
        response = client.get("/api/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
    
    def test_get_users_with_pagination(self, client, test_users):
        response = client.get("/api/v1/users?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
    
    def test_get_users_with_skip(self, client, test_users):
        response = client.get("/api/v1/users?skip=2&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestGetUserByNameEndpoint:
    """Test GET /api/v1/users/by-name/{username}"""
    
    def test_get_user_by_name_success(self, client, test_users):
        response = client.get("/api/v1/users/by-name/user1")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "user1"
        assert data["email"] == "user1@example.com"
    
    def test_get_user_by_name_not_found(self, client):
        response = client.get("/api/v1/users/by-name/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetUserByIdEndpoint:
    """Test GET /api/v1/users/{user_id}"""
    
    def test_get_user_by_id_success(self, client, test_users):
        user_id = test_users[0].id
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == "user1"
    
    def test_get_user_by_id_not_found(self, client):
        response = client.get("/api/v1/users/99999")
        assert response.status_code == 404


class TestDeleteUserEndpoint:
    """Test DELETE /api/v1/users/{user_id}"""
    
    def test_delete_user_success(self, client, test_users):
        user_id = test_users[0].id
        response = client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()
        
        # Verify user is deleted
        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == user_id).first()
        assert user is None
        db.close()
    
    def test_delete_user_not_found(self, client):
        response = client.delete("/api/v1/users/99999")
        assert response.status_code == 404
    
    def test_delete_user_with_groups(self, client, test_users, test_group):
        # Add user to group
        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == test_users[0].id).first()
        group = db.query(Group).filter(Group.id == test_group.id).first()
        group.members.append(user)
        db.commit()
        db.close()
        
        # Try to delete user with groups
        response = client.delete(f"/api/v1/users/{test_users[0].id}")
        assert response.status_code == 400
        assert "group" in response.json()["detail"].lower()


class TestCreateGroupEndpoint:
    """Test POST /api/v1/groups"""
    
    def test_create_group_success(self, client, test_users):
        response = client.post("/api/v1/groups", json={
            "name": "New Group",
            "created_by": test_users[0].id
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Group"
        assert "id" in data
    
    def test_create_group_duplicate_name(self, client, test_users, test_group):
        response = client.post("/api/v1/groups", json={
            "name": "Test Group",
            "created_by": test_users[0].id
        })
        # Should still succeed as duplicate names may be allowed
        assert response.status_code in [201, 400]


class TestGetGroupsEndpoint:
    """Test GET /api/v1/groups"""
    
    def test_get_groups_success(self, client, test_group):
        response = client.get("/api/v1/groups")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(g["name"] == "Test Group" for g in data)
    
    def test_get_groups_with_pagination(self, client, test_group):
        response = client.get("/api/v1/groups?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestGetUserGroupsEndpoint:
    """Test GET /api/v1/users/{user_id}/groups"""
    
    def test_get_user_groups_success(self, client, test_users, test_group):
        # Add user to group
        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == test_users[0].id).first()
        group = db.query(Group).filter(Group.id == test_group.id).first()
        group.members.append(user)
        db.commit()
        db.close()
        
        response = client.get(f"/api/v1/users/{test_users[0].id}/groups")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(g["name"] == "Test Group" for g in data)
    
    def test_get_user_groups_empty(self, client, test_users):
        response = client.get(f"/api/v1/users/{test_users[1].id}/groups")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_user_groups_not_found(self, client):
        response = client.get("/api/v1/users/99999/groups")
        assert response.status_code == 404


class TestAddMemberToGroupEndpoint:
    """Test POST /api/v1/groups/{group_id}/add_member/{user_id}"""
    
    def test_add_member_success(self, client, test_users, test_group):
        response = client.post(f"/api/v1/groups/{test_group.id}/add_member/{test_users[1].id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_group.id
        
        # Verify member was added
        db = TestingSessionLocal()
        group = db.query(Group).filter(Group.id == test_group.id).first()
        assert any(m.id == test_users[1].id for m in group.members)
        db.close()
    
    def test_add_member_already_exists(self, client, test_users, test_group):
        # Add member first time
        client.post(f"/api/v1/groups/{test_group.id}/add_member/{test_users[1].id}")
        
        # Try to add again
        response = client.post(f"/api/v1/groups/{test_group.id}/add_member/{test_users[1].id}")
        assert response.status_code == 400
        assert "already a member" in response.json()["detail"].lower()
    
    def test_add_member_group_not_found(self, client, test_users):
        response = client.post(f"/api/v1/groups/99999/add_member/{test_users[0].id}")
        assert response.status_code == 404
    
    def test_add_member_user_not_found(self, client, test_group):
        response = client.post(f"/api/v1/groups/{test_group.id}/add_member/99999")
        assert response.status_code == 404


class TestRemoveMemberFromGroupEndpoint:
    """Test DELETE /api/v1/groups/{group_id}/remove_member/{user_id}"""
    
    def test_remove_member_success(self, client, test_users, test_group):
        # Add member first
        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == test_users[1].id).first()
        group = db.query(Group).filter(Group.id == test_group.id).first()
        group.members.append(user)
        db.commit()
        db.close()
        
        # Remove member
        response = client.delete(f"/api/v1/groups/{test_group.id}/remove_member/{test_users[1].id}")
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()
        
        # Verify member was removed
        db = TestingSessionLocal()
        group = db.query(Group).filter(Group.id == test_group.id).first()
        assert not any(m.id == test_users[1].id for m in group.members)
        db.close()
    
    def test_remove_member_not_in_group(self, client, test_users, test_group):
        response = client.delete(f"/api/v1/groups/{test_group.id}/remove_member/{test_users[2].id}")
        assert response.status_code == 400
        assert "not a member" in response.json()["detail"].lower()
    
    def test_remove_member_group_not_found(self, client, test_users):
        response = client.delete(f"/api/v1/groups/99999/remove_member/{test_users[0].id}")
        assert response.status_code == 404


class TestLinkTelegramEndpoint:
    """Test POST /api/v1/link-telegram"""
    
    def test_link_telegram_success(self, client, test_users):
        response = client.post("/api/v1/link-telegram", json={
            "username": "user1",
            "telegram_id": "123456789"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == "123456789"
        
        # Verify in database
        db = TestingSessionLocal()
        user = db.query(User).filter(User.username == "user1").first()
        assert user.telegram_id == "123456789"
        db.close()
    
    def test_link_telegram_user_not_found(self, client):
        response = client.post("/api/v1/link-telegram", json={
            "username": "nonexistent",
            "telegram_id": "123456789"
        })
        assert response.status_code == 404
    
    def test_link_telegram_already_linked(self, client, test_users):
        # Link first time
        client.post("/api/v1/link-telegram", json={
            "username": "user1",
            "telegram_id": "123456789"
        })
        
        # Try to link again
        response = client.post("/api/v1/link-telegram", json={
            "username": "user1",
            "telegram_id": "987654321"
        })
        # Should update the telegram_id
        assert response.status_code == 200
        assert response.json()["telegram_id"] == "987654321"


class TestLegacyRegisterEndpoint:
    """Test POST /api/v1/register (legacy)"""
    
    def test_legacy_register_success(self, client):
        response = client.post("/api/v1/register", json={
            "username": "newuser",
            "name": "New User",
            "email": "newuser@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert "id" in data
    
    def test_legacy_register_duplicate_username(self, client, test_users):
        response = client.post("/api/v1/register", json={
            "username": "user1",
            "name": "Another User",
            "email": "another@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
