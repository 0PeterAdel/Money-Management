#!/bin/bash

# Stop all Money Management services running locally

echo "================================================"
echo "Stopping All Local Services"
echo "================================================"
echo ""

echo "Stopping services..."

# Stop Python/FastAPI services (uvicorn)
if pgrep -f "uvicorn" > /dev/null; then
    echo "  → Stopping FastAPI services (Auth, Notification, Gateway)..."
    pkill -f "uvicorn"
    sleep 1
    echo "    ✓ Stopped"
else
    echo "  ⊘ No FastAPI services running"
fi

# Stop Celery worker
if pgrep -f "celery" > /dev/null; then
    echo "  → Stopping Celery worker..."
    pkill -f "celery"
    sleep 1
    echo "    ✓ Stopped"
else
    echo "  ⊘ No Celery worker running"
fi

# Stop Bot service
if pgrep -f "bot_main" > /dev/null; then
    echo "  → Stopping Bot service..."
    pkill -f "bot_main"
    sleep 1
    echo "    ✓ Stopped"
else
    echo "  ⊘ No Bot service running"
fi

# Stop Frontend (npm/vite)
if pgrep -f "npm run dev" > /dev/null || pgrep -f "vite" > /dev/null; then
    echo "  → Stopping Frontend..."
    pkill -f "npm run dev"
    pkill -f "vite"
    sleep 1
    echo "    ✓ Stopped"
else
    echo "  ⊘ No Frontend running"
fi

echo ""
echo "================================================"
echo "✅ All services stopped!"
echo "================================================"
echo ""
echo "To start again: ./start_all_local.sh"
echo ""
