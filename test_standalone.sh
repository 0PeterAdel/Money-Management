#!/bin/bash

# Test each microservice standalone
# This script tests if each service can run independently

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "================================================"
echo "Testing Microservices Standalone"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counter
total_tests=0
passed_tests=0

# Function to test a service
test_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Testing: $service_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd "$BASE_DIR/$service_dir"
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}✗ requirements.txt not found${NC}"
        return 1
    fi
    echo -e "${GREEN}✓${NC} requirements.txt found"
    total_tests=$((total_tests + 1))
    passed_tests=$((passed_tests + 1))
    
    # Check if venv exists, create if not
    if [ ! -d "venv" ]; then
        echo "  Creating virtual environment..."
        python3 -m venv venv
    fi
    echo -e "${GREEN}✓${NC} Virtual environment ready"
    total_tests=$((total_tests + 1))
    passed_tests=$((passed_tests + 1))
    
    # Activate venv and check dependencies
    source venv/bin/activate
    
    echo "  Installing/checking dependencies..."
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓${NC} Dependencies installed"
    total_tests=$((total_tests + 1))
    passed_tests=$((passed_tests + 1))
    
    # Try importing the main module
    if [ -f "app/main.py" ]; then
        python -c "from app.main import app; print('Import successful')" 2>&1 | grep -q "Import successful"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Service code imports successfully"
            total_tests=$((total_tests + 1))
            passed_tests=$((passed_tests + 1))
        else
            echo -e "${RED}✗${NC} Service code import failed"
            total_tests=$((total_tests + 1))
        fi
    fi
    
    deactivate
    echo ""
}

# Test Auth Service
test_service "Auth Service" "services/auth_service" 8001

# Test Notification Service
test_service "Notification Service" "services/notification_service" 8002

# Test Bot Service
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing: Bot Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Load environment variables from .env
if [ -f "$BASE_DIR/.env" ]; then
    export $(cat "$BASE_DIR/.env" | grep -v '^#' | xargs)
    echo -e "${GREEN}✓${NC} Environment variables loaded from .env"
else
    echo -e "${YELLOW}⚠${NC} No .env file found at $BASE_DIR/.env"
fi

cd "$BASE_DIR/services/bot_service"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}✓${NC} Bot Service dependencies installed"
total_tests=$((total_tests + 1))
passed_tests=$((passed_tests + 1))

# Test bot config loads with environment variables
if python -c "from app.core.config import settings; print(f'Bot config loaded. Token set: {bool(settings.TELEGRAM_BOT_TOKEN)}')" 2>&1 | grep -q "Bot config loaded"; then
    echo -e "${GREEN}✓${NC} Bot configuration loads successfully"
    total_tests=$((total_tests + 1))
    passed_tests=$((passed_tests + 1))
else
    echo -e "${RED}✗${NC} Bot configuration failed (TELEGRAM_BOT_TOKEN may not be set)"
    total_tests=$((total_tests + 1))
fi
deactivate
echo ""

# Test Gateway
test_service "API Gateway" "gateway" 8000

# Summary
echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "Total Tests: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$((total_tests - passed_tests))${NC}"
echo ""

if [ $passed_tests -eq $total_tests ]; then
    echo -e "${GREEN}✓ All services are ready to run standalone!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start Redis: sudo systemctl start redis"
    echo "  2. Run services: ./start_all_local.sh"
    echo "  3. Or start individually - see RUN_WITHOUT_DOCKER.md"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Check the output above.${NC}"
    exit 1
fi
