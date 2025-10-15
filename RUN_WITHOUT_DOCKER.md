# Running Without Docker - Complete Guide

This guide shows you how to run **all services locally** without Docker.

---

## 📋 Prerequisites

### Required Software
- **Python 3.11+** installed
- **Node.js 20+** and npm installed
- **Redis** installed and running (for Celery)
- **Git** (already have it)

### Install Prerequisites

#### On Kali Linux / Debian / Ubuntu:
```bash
# Python (usually already installed)
python3 --version

# Node.js and npm
sudo apt update
sudo apt install nodejs npm -y

# Redis (for notification service)
sudo apt install redis-server -y
sudo systemctl start redis
sudo systemctl enable redis

# Verify installations
python3 --version
node --version
npm --version
redis-cli ping  # Should return "PONG"
```

---

## 🚀 Step-by-Step Setup

### Step 1: Setup Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env
```

**Update `.env` with:**
```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Database (local)
DATABASE_URL=sqlite:///./assistant.db

# Security
SECRET_KEY=your-secret-key-here

# Redis (local)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Service URLs (local)
AUTH_SERVICE_URL=http://localhost:8001
NOTIFICATION_SERVICE_URL=http://localhost:8002
API_GATEWAY_URL=http://localhost:8000

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🔧 Terminal Setup (You'll Need 6 Terminals)

### Terminal 1: Auth Service

```bash
# Navigate to auth service
cd ~/Zone/Rebos/Money-Management/services/auth_service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="sqlite:///../../assistant.db"
export SECRET_KEY="your-secret-key-here"

# Run the service
uvicorn app.main:app --reload --port 8001 --host 0.0.0.0
```

**Service will be at:** http://localhost:8001

---

### Terminal 2: Notification Service

```bash
# Navigate to notification service
cd ~/Zone/Rebos/Money-Management/services/notification_service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# Run the service
uvicorn app.main:app --reload --port 8002 --host 0.0.0.0
```

**Service will be at:** http://localhost:8002

---

### Terminal 3: Celery Worker (for Notifications)

```bash
# Navigate to notification service
cd ~/Zone/Rebos/Money-Management/services/notification_service

# Activate virtual environment (same as Terminal 2)
source venv/bin/activate

# Set environment variables
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# Run Celery worker
celery -A app.core.celery_config worker --loglevel=info
```

---

### Terminal 4: API Gateway

```bash
# Navigate to gateway
cd ~/Zone/Rebos/Money-Management/gateway

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AUTH_SERVICE_URL="http://localhost:8001"
export NOTIFICATION_SERVICE_URL="http://localhost:8002"

# Run the gateway
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

**Gateway will be at:** http://localhost:8000

---

### Terminal 5: Bot Service

```bash
# Navigate to bot service
cd ~/Zone/Rebos/Money-Management/services/bot_service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export API_GATEWAY_URL="http://localhost:8000"

# Run the bot
python -m app.bot_main
```

**Bot will connect to Telegram**

---

### Terminal 6: Frontend

```bash
# Navigate to frontend
cd ~/Zone/Rebos/Money-Management/frontend

# Install dependencies (first time only)
npm install

# Create .env.local file
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

# Run the frontend
npm run dev
```

**Frontend will be at:** http://localhost:12000

---

## 📝 Quick Start Script

Create a helper script to make this easier:

```bash
# Create the script
cat > ~/Zone/Rebos/Money-Management/start_all_local.sh << 'EOF'
#!/bin/bash

# Start all services locally in separate terminal windows

BASE_DIR="$HOME/Zone/Rebos/Money-Management"

echo "Starting all services..."
echo ""
echo "This will open 6 terminal windows:"
echo "  1. Auth Service (port 8001)"
echo "  2. Notification Service (port 8002)"
echo "  3. Celery Worker"
echo "  4. API Gateway (port 8000)"
echo "  5. Bot Service"
echo "  6. Frontend (port 12000)"
echo ""

# Function to open terminal and run command
open_terminal() {
    local title=$1
    local cmd=$2
    
    # For gnome-terminal
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$title" -- bash -c "$cmd; exec bash"
    # For xterm
    elif command -v xterm &> /dev/null; then
        xterm -T "$title" -e "$cmd; bash" &
    # For konsole
    elif command -v konsole &> /dev/null; then
        konsole --title "$title" -e bash -c "$cmd; exec bash" &
    else
        echo "No supported terminal found. Please run commands manually."
        exit 1
    fi
}

# 1. Auth Service
open_terminal "Auth Service (8001)" \
"cd $BASE_DIR/services/auth_service && \
python3 -m venv venv && source venv/bin/activate && \
pip install -q -r requirements.txt && \
export DATABASE_URL='sqlite:///../../assistant.db' && \
export SECRET_KEY='dev-secret-key' && \
echo 'Starting Auth Service on port 8001...' && \
uvicorn app.main:app --reload --port 8001"

sleep 2

# 2. Notification Service
open_terminal "Notification Service (8002)" \
"cd $BASE_DIR/services/notification_service && \
python3 -m venv venv && source venv/bin/activate && \
pip install -q -r requirements.txt && \
export CELERY_BROKER_URL='redis://localhost:6379/0' && \
export CELERY_RESULT_BACKEND='redis://localhost:6379/0' && \
echo 'Starting Notification Service on port 8002...' && \
uvicorn app.main:app --reload --port 8002"

sleep 2

# 3. Celery Worker
open_terminal "Celery Worker" \
"cd $BASE_DIR/services/notification_service && \
source venv/bin/activate && \
export CELERY_BROKER_URL='redis://localhost:6379/0' && \
export CELERY_RESULT_BACKEND='redis://localhost:6379/0' && \
echo 'Starting Celery Worker...' && \
celery -A app.core.celery_config worker --loglevel=info"

sleep 2

# 4. API Gateway
open_terminal "API Gateway (8000)" \
"cd $BASE_DIR/gateway && \
python3 -m venv venv && source venv/bin/activate && \
pip install -q -r requirements.txt && \
export AUTH_SERVICE_URL='http://localhost:8001' && \
export NOTIFICATION_SERVICE_URL='http://localhost:8002' && \
echo 'Starting API Gateway on port 8000...' && \
uvicorn app.main:app --reload --port 8000"

sleep 2

# 5. Bot Service
open_terminal "Bot Service" \
"cd $BASE_DIR/services/bot_service && \
python3 -m venv venv && source venv/bin/activate && \
pip install -q -r requirements.txt && \
export API_GATEWAY_URL='http://localhost:8000' && \
echo 'Starting Bot Service...' && \
python -m app.bot_main"

sleep 2

# 6. Frontend
open_terminal "Frontend (12000)" \
"cd $BASE_DIR/frontend && \
npm install && \
echo 'VITE_API_BASE_URL=http://localhost:8000' > .env.local && \
echo 'Starting Frontend on port 12000...' && \
npm run dev"

echo ""
echo "✅ All services starting in separate terminals!"
echo ""
echo "Access your application at:"
echo "  Frontend:  http://localhost:12000"
echo "  Gateway:   http://localhost:8000/docs"
echo ""
EOF

# Make it executable
chmod +x ~/Zone/Rebos/Money-Management/start_all_local.sh
```

**Then run:**
```bash
./start_all_local.sh
```

---

## 🧪 Testing After Start

Wait 30 seconds for all services to start, then test:

```bash
# Test Auth Service
curl http://localhost:8001/health

# Test Notification Service
curl http://localhost:8002/health

# Test Gateway
curl http://localhost:8000/health

# Test Frontend
curl http://localhost:12000

# Test API via Gateway
curl http://localhost:8000/api/v1/users
```

---

## 🔍 Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8000
lsof -i :8001
lsof -i :8002
lsof -i :12000

# Kill process on port
kill -9 $(lsof -t -i:8000)
```

### Redis Not Running

```bash
# Start Redis
sudo systemctl start redis

# Check Redis status
sudo systemctl status redis

# Test Redis
redis-cli ping  # Should return PONG
```

### Module Not Found Errors

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Errors

```bash
# Create database directory
mkdir -p ~/Zone/Rebos/Money-Management

# Check database exists
ls -la ~/Zone/Rebos/Money-Management/assistant.db

# If not, it will be created automatically on first run
```

### Frontend Won't Start

```bash
cd ~/Zone/Rebos/Money-Management/frontend

# Clear cache
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Try again
npm run dev
```

---

## 📊 Service Checklist

When all services are running, you should see:

- [ ] **Terminal 1:** Auth Service logs (port 8001)
- [ ] **Terminal 2:** Notification Service logs (port 8002)
- [ ] **Terminal 3:** Celery worker logs
- [ ] **Terminal 4:** Gateway logs (port 8000)
- [ ] **Terminal 5:** Bot Service logs (Telegram polling)
- [ ] **Terminal 6:** Frontend dev server (port 12000)

**Plus:**
- [ ] Redis running in background

---

## 🛑 Stopping All Services

### Manual Stop
Press `Ctrl+C` in each terminal window

### Kill All Processes
```bash
# Kill Python services
pkill -f uvicorn
pkill -f celery
pkill -f bot_main

# Kill Node/Frontend
pkill -f "npm run dev"

# Stop Redis (optional)
sudo systemctl stop redis
```

---

## 💡 Pro Tips

### 1. Use tmux for Better Terminal Management

```bash
# Install tmux
sudo apt install tmux

# Create a session with all services
tmux new-session -s moneyapp \; \
  split-window -h \; \
  split-window -v \; \
  select-pane -t 0 \; \
  split-window -v

# Then run each service in a pane
```

### 2. Create Aliases

Add to `~/.bashrc`:

```bash
alias mm-auth='cd ~/Zone/Rebos/Money-Management/services/auth_service && source venv/bin/activate'
alias mm-notif='cd ~/Zone/Rebos/Money-Management/services/notification_service && source venv/bin/activate'
alias mm-gate='cd ~/Zone/Rebos/Money-Management/gateway && source venv/bin/activate'
alias mm-bot='cd ~/Zone/Rebos/Money-Management/services/bot_service && source venv/bin/activate'
alias mm-front='cd ~/Zone/Rebos/Money-Management/frontend'
```

### 3. Environment File per Service

Create `.env` in each service directory for easier management.

---

## 📚 Service URLs Reference

| Service | URL | API Docs |
|---------|-----|----------|
| **Auth Service** | http://localhost:8001 | http://localhost:8001/docs |
| **Notification Service** | http://localhost:8002 | http://localhost:8002/docs |
| **API Gateway** | http://localhost:8000 | http://localhost:8000/docs |
| **Frontend** | http://localhost:12000 | - |
| **Bot** | Telegram | - |

---

## ✅ Success!

When everything is running, you should be able to:
- ✅ Access frontend at http://localhost:12000
- ✅ Register/login via web interface
- ✅ Use Telegram bot
- ✅ Create groups and expenses
- ✅ Receive notifications

**Your Money Management System is now running locally without Docker!** 🎉

---

## 🔄 Switching Back to Docker

If you want to go back to Docker:

```bash
# Stop all local services (Ctrl+C in each terminal)

# Start with Docker
docker-compose up -d
```

Docker is still the **recommended** way for production and easier development! 🐳
