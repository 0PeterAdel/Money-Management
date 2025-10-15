# Auth Service

Authentication and User Management microservice for the Money Management system.

## Features

- User registration
- User authentication
- Telegram account linking
- Group management
- User management

## API Endpoints

### Authentication
- `POST /api/v1/register` - Register a new user
- `POST /api/v1/link-telegram` - Link Telegram account

### Users
- `GET /api/v1/users` - Get all users
- `GET /api/v1/users/{user_id}` - Get user by ID
- `GET /api/v1/users/by-name/{username}` - Get user by username
- `DELETE /api/v1/users/{user_id}` - Delete user

### Groups
- `POST /api/v1/groups` - Create group
- `GET /api/v1/groups` - Get all groups
- `GET /api/v1/users/{user_id}/groups` - Get user's groups
- `POST /api/v1/groups/{group_id}/add_member/{user_id}` - Add member to group
- `DELETE /api/v1/groups/{group_id}/remove_member/{user_id}` - Remove member from group

## Running Locally

```bash
cd services/auth_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## Environment Variables

- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Secret key for JWT tokens
