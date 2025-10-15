# Migration Guide: Monolithic to Microservices

This guide helps you migrate from the old monolithic structure to the new microservices architecture.

## Changes Overview

### Old Structure (Monolithic)
```
Money-Management/
├── main.py              # Single FastAPI app
├── models.py            # All database models
├── security.py          # Security utilities
├── database.py          # Database config
├── config.py            # Configuration
├── notifications.py     # Notifications
└── bot/
    ├── bot_main.py
    └── locales.py
```

### New Structure (Microservices)
```
Money-Management/
├── services/
│   ├── auth_service/         # User & Group management
│   ├── notification_service/ # Notifications
│   └── bot_service/          # Telegram bot
├── gateway/                  # API Gateway
├── shared/                   # Shared utilities
└── frontend/                 # Web interface
```

## Migration Steps

### 1. Backup Your Data

```bash
# Backup your existing database
cp assistant.db assistant.db.backup

# Backup environment variables
cp .env .env.backup
```

### 2. Update Environment Variables

The new structure uses `.env` file at the root. Update it with:

```bash
# Copy the template
cp .env.docker .env

# Edit with your values
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite:///./assistant.db
SECRET_KEY=your-secret-key
```

### 3. Database Migration

The database schema remains the same, but you may need to update the path:

```bash
# Move database to project root if needed
mv bot/assistant.db ./assistant.db
```

### 4. Start Services

#### Option A: Using Docker (Recommended)
```bash
docker-compose up -d
```

#### Option B: Manual Start
```bash
# Terminal 1: Auth Service
cd services/auth_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Terminal 2: Notification Service
cd services/notification_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002

# Terminal 3: API Gateway
cd gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 4: Bot Service
cd services/bot_service
pip install -r requirements.txt
python -m app.bot_main

# Terminal 5: Frontend
cd frontend
npm install
npm run dev
```

## API Endpoint Changes

### Before (Monolithic)
```
http://localhost:8000/users
http://localhost:8000/groups
http://localhost:8000/expenses
```

### After (Microservices via Gateway)
```
http://localhost:8000/api/v1/users      # via Gateway → Auth Service
http://localhost:8000/api/v1/groups     # via Gateway → Auth Service
http://localhost:8000/api/v1/expenses   # via Gateway → (to be migrated)
```

## Frontend Configuration

Update your frontend API base URL:

**Before:**
```typescript
const API_BASE_URL = 'http://localhost:8000';
```

**After:**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

Add to `frontend/.env`:
```
VITE_API_BASE_URL=http://localhost:8000
```

## Bot Configuration

The bot now connects through the API Gateway:

**Before:**
```python
API_BASE_URL = "http://127.0.0.1:8000"
```

**After:**
```python
API_BASE_URL = settings.API_GATEWAY_URL  # http://gateway:8000 in Docker
```

## Troubleshooting

### Service Won't Start

1. Check if ports are available:
```bash
lsof -i :8000  # Gateway
lsof -i :8001  # Auth Service
lsof -i :8002  # Notification Service
lsof -i :12000 # Frontend
```

2. Check service health:
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

### Database Issues

If you get database errors:
```bash
# Check database file exists
ls -la assistant.db

# Check permissions
chmod 644 assistant.db
```

### Docker Issues

```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Feature Mapping

| Old Feature | New Service | Endpoint |
|-------------|-------------|----------|
| User Registration | Auth Service | POST /api/v1/register |
| User Login | Auth Service | POST /api/v1/link-telegram |
| Group Management | Auth Service | /api/v1/groups/* |
| Email Notifications | Notification Service | POST /api/v1/send-email |
| Telegram Notifications | Notification Service | POST /api/v1/send-push |
| Bot Interface | Bot Service | Telegram Bot API |

## Notes for Developers

### Adding New Services

1. Create service directory under `services/`
2. Follow the same structure as existing services
3. Add service to `docker-compose.yml`
4. Update gateway routing in `gateway/app/main.py`

### Shared Code

Put reusable code in `shared/`:
- `shared/utils/` - Utility functions
- `shared/database/` - Database base classes
- `shared/schemas/` - Common Pydantic models

### Testing Individual Services

Each service can be tested independently:
```bash
cd services/auth_service
pytest tests/
```

## Rollback Plan

If you need to rollback to the old structure:

```bash
# Stop new services
docker-compose down

# Restore database
cp assistant.db.backup assistant.db

# Restore environment
cp .env.backup .env

# Start old monolithic app
uvicorn main:app --reload
python -m bot.bot_main
```

## Support

For issues during migration:
1. Check service logs: `docker-compose logs -f`
2. Verify environment variables are set correctly
3. Ensure all required ports are available
4. Check the README.md for detailed setup instructions
