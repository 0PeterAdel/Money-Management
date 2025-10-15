# Quick Start Guide

Get the Money Management System up and running in minutes!

## Prerequisites

- Docker & Docker Compose installed
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))

## 🚀 5-Minute Setup

### Step 1: Clone & Configure

```bash
# Clone the repository
git clone <your-repo-url>
cd Money-Management

# Copy environment template
cp .env.docker .env

# Edit .env and add your bot token
nano .env  # or use your favorite editor
```

### Step 2: Start All Services

```bash
# Start everything with Docker Compose
docker-compose up -d

# Watch the logs (optional)
docker-compose logs -f
```

### Step 3: Verify Services

```bash
# Check all services are running
docker-compose ps

# Test health endpoints
curl http://localhost:8000/health  # Gateway
curl http://localhost:8001/health  # Auth Service
curl http://localhost:8002/health  # Notification Service
```

### Step 4: Access the Application

- **Web Interface:** http://localhost:12000
- **API Documentation:** http://localhost:8000/docs
- **Telegram Bot:** Find your bot on Telegram and send `/start`

## 🎯 First Steps

### 1. Create Your First User (via Web)

1. Open http://localhost:12000
2. Click "Register"
3. Enter username and password
4. Login with your credentials

### 2. Or Create User via Telegram Bot

1. Find your bot on Telegram
2. Send `/start`
3. Send `/register`
4. Follow the prompts

### 3. Create Your First Group

**Via Web:**
1. Go to "Groups" section
2. Click "Create Group"
3. Enter group name and description
4. Add members

**Via Telegram:**
1. Send "👥 My Groups"
2. Click "Create New Group"
3. Follow the prompts

### 4. Add Your First Expense

**Via Web:**
1. Go to "Expenses" section
2. Click "New Expense"
3. Fill in details
4. Submit for approval

**Via Telegram:**
1. Send "💸 New Expense"
2. Select group
3. Enter description, amount, category
4. Select participants
5. Confirm

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f auth_service
docker-compose logs -f gateway
docker-compose logs -f bot_service
```

### Check Service Status

```bash
# List running containers
docker-compose ps

# Check resource usage
docker stats
```

## 🛑 Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

## 🔧 Development Mode

### Run Services Locally (Without Docker)

**1. Setup Python Environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**2. Start Auth Service**
```bash
cd services/auth_service
pip install -r requirements.txt
export DATABASE_URL="sqlite:///../../assistant.db"
uvicorn app.main:app --reload --port 8001
```

**3. Start Gateway**
```bash
cd gateway
pip install -r requirements.txt
export AUTH_SERVICE_URL="http://localhost:8001"
export NOTIFICATION_SERVICE_URL="http://localhost:8002"
uvicorn app.main:app --reload --port 8000
```

**4. Start Frontend**
```bash
cd frontend
npm install
npm run dev
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check if ports are already in use
lsof -i :8000  # Gateway
lsof -i :8001  # Auth
lsof -i :8002  # Notification
lsof -i :12000 # Frontend

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Bot Not Responding

1. Verify `TELEGRAM_BOT_TOKEN` in `.env`
2. Check bot service logs: `docker-compose logs bot_service`
3. Ensure bot is not blocked by Telegram
4. Test with `/start` command

### Frontend Can't Connect to Backend

1. Check gateway is running: `curl http://localhost:8000/health`
2. Verify CORS settings in `gateway/app/main.py`
3. Check browser console for errors
4. Ensure `VITE_API_BASE_URL` is set correctly

### Database Errors

```bash
# Check database file exists
ls -la assistant.db

# Reset database (WARNING: deletes all data)
rm assistant.db
docker-compose restart auth_service
```

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) if upgrading
- Explore the [API Documentation](http://localhost:8000/docs)
- Customize environment variables in `.env`

## 🆘 Getting Help

1. Check service logs: `docker-compose logs -f [service_name]`
2. Review the [README.md](README.md) for detailed setup
3. Verify all prerequisites are met
4. Check GitHub Issues for similar problems

## 🎉 You're All Set!

Your Money Management System is now running. Happy expense tracking! 🚀
