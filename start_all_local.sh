#!/bin/bash

# Start all Money Management services locally (without Docker)
# This script opens 6 terminal windows for each service

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "================================================"
echo "Starting Money Management Services (Local Mode)"
echo "================================================"
echo ""
echo "This will start 6 services in separate terminals:"
echo "  1. Auth Service         → http://localhost:8001"
echo "  2. Notification Service → http://localhost:8002"
echo "  3. Celery Worker        → Background task processor"
echo "  4. API Gateway          → http://localhost:8000"
echo "  5. Bot Service          → Telegram Bot"
echo "  6. Frontend             → http://localhost:12000"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and add your TELEGRAM_BOT_TOKEN"
    echo "Then run this script again."
    exit 1
fi

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "  ✓ Python 3 found"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi
echo "  ✓ Node.js found"

# Check Redis
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis not found. Installing..."
    sudo apt install redis-server -y
fi

# Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    echo "  ⚠️  Starting Redis..."
    sudo systemctl start redis 2>/dev/null || redis-server --daemonize yes
fi
echo "  ✓ Redis running"

echo ""
echo "Starting services..."
echo ""

# Function to open terminal based on available terminal emulator
open_terminal() {
    local title=$1
    local cmd=$2
    
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$title" -- bash -c "$cmd; exec bash" 2>/dev/null &
    elif command -v xterm &> /dev/null; then
        xterm -T "$title" -e bash -c "$cmd; exec bash" &
    elif command -v konsole &> /dev/null; then
        konsole --title "$title" -e bash -c "$cmd; exec bash" &
    elif command -v xfce4-terminal &> /dev/null; then
        xfce4-terminal --title="$title" -e "bash -c '$cmd; exec bash'" &
    else
        echo "❌ No supported terminal emulator found"
        echo "Please install: gnome-terminal, xterm, konsole, or xfce4-terminal"
        exit 1
    fi
}

# 1. Auth Service
echo "  → Starting Auth Service (port 8001)..."
open_terminal "Auth Service :8001" \
"cd '$BASE_DIR/services/auth_service' && \
echo '════════════════════════════════════════' && \
echo '  Auth Service' && \
echo '  Port: 8001' && \
echo '════════════════════════════════════════' && \
echo '' && \
python3 -m venv venv 2>/dev/null || true && \
source venv/bin/activate && \
pip install -q -r requirements.txt && \
export DATABASE_URL='sqlite:///$BASE_DIR/assistant.db' && \
export SECRET_KEY='dev-secret-key-change-in-production' && \
echo '✓ Starting Auth Service...' && \
echo '' && \
uvicorn app.main:app --reload --port 8001 --host 0.0.0.0"

sleep 2

# 2. Notification Service
echo "  → Starting Notification Service (port 8002)..."
open_terminal "Notification Service :8002" \
"cd '$BASE_DIR/services/notification_service' && \
echo '════════════════════════════════════════' && \
echo '  Notification Service' && \
echo '  Port: 8002' && \
echo '════════════════════════════════════════' && \
echo '' && \
python3 -m venv venv 2>/dev/null || true && \
source venv/bin/activate && \
pip install -q -r requirements.txt && \
export CELERY_BROKER_URL='redis://localhost:6379/0' && \
export CELERY_RESULT_BACKEND='redis://localhost:6379/0' && \
source '$BASE_DIR/.env' && \
echo '✓ Starting Notification Service...' && \
echo '' && \
uvicorn app.main:app --reload --port 8002 --host 0.0.0.0"

sleep 2

# 3. Celery Worker
echo "  → Starting Celery Worker..."
open_terminal "Celery Worker" \
"cd '$BASE_DIR/services/notification_service' && \
echo '════════════════════════════════════════' && \
echo '  Celery Worker' && \
echo '  Processing async tasks' && \
echo '════════════════════════════════════════' && \
echo '' && \
source venv/bin/activate && \
export CELERY_BROKER_URL='redis://localhost:6379/0' && \
export CELERY_RESULT_BACKEND='redis://localhost:6379/0' && \
echo '✓ Starting Celery Worker...' && \
echo '' && \
celery -A app.core.celery_config worker --loglevel=info"

sleep 2

# 4. API Gateway
echo "  → Starting API Gateway (port 8000)..."
open_terminal "API Gateway :8000" \
"cd '$BASE_DIR/gateway' && \
echo '════════════════════════════════════════' && \
echo '  API Gateway' && \
echo '  Port: 8000' && \
echo '════════════════════════════════════════' && \
echo '' && \
python3 -m venv venv 2>/dev/null || true && \
source venv/bin/activate && \
pip install -q -r requirements.txt && \
export AUTH_SERVICE_URL='http://localhost:8001' && \
export NOTIFICATION_SERVICE_URL='http://localhost:8002' && \
echo '✓ Starting API Gateway...' && \
echo '' && \
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0"

sleep 2

# 5. Bot Service
echo "  → Starting Bot Service..."
open_terminal "Bot Service (Telegram)" \
"cd '$BASE_DIR/services/bot_service' && \
echo '════════════════════════════════════════' && \
echo '  Bot Service' && \
echo '  Telegram Bot' && \
echo '════════════════════════════════════════' && \
echo '' && \
python3 -m venv venv 2>/dev/null || true && \
source venv/bin/activate && \
pip install -q -r requirements.txt && \
export API_GATEWAY_URL='http://localhost:8000' && \
source '$BASE_DIR/.env' && \
echo '✓ Starting Bot Service...' && \
echo '' && \
python -m app.bot_main"

sleep 2

# 6. Frontend
echo "  → Starting Frontend (port 12000)..."
open_terminal "Frontend :12000" \
"cd '$BASE_DIR/frontend' && \
echo '════════════════════════════════════════' && \
echo '  Frontend (React + Vite)' && \
echo '  Port: 12000' && \
echo '════════════════════════════════════════' && \
echo '' && \
if [ ! -d 'node_modules' ]; then \
  echo 'Installing npm packages (first time only)...' && \
  npm install; \
fi && \
echo 'VITE_API_BASE_URL=http://localhost:8000' > .env.local && \
echo '✓ Starting Frontend...' && \
echo '' && \
npm run dev"

sleep 2

echo ""
echo "================================================"
echo "✅ All services are starting!"
echo "================================================"
echo ""
echo "📊 Service Status:"
echo "  Wait 30 seconds for all services to start..."
echo ""
echo "🌐 Access URLs:"
echo "  Frontend:       http://localhost:12000"
echo "  API Gateway:    http://localhost:8000/docs"
echo "  Auth Service:   http://localhost:8001/docs"
echo "  Notification:   http://localhost:8002/docs"
echo ""
echo "🧪 Test Services:"
echo "  ./test_services.sh"
echo ""
echo "🛑 To Stop:"
echo "  Press Ctrl+C in each terminal window"
echo "  Or run: pkill -f uvicorn && pkill -f celery && pkill -f 'npm run dev'"
echo ""
echo "📚 Documentation:"
echo "  See RUN_WITHOUT_DOCKER.md for details"
echo ""
