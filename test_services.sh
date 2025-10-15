#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "Money Management Services Test Script"
echo "======================================"
echo ""

# Function to test HTTP endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected: $expected_status, Got: $response)"
        return 1
    fi
}

# Test counter
total_tests=0
passed_tests=0

echo "1. Testing API Gateway"
echo "----------------------"
test_endpoint "Gateway Root" "http://localhost:8000" && ((passed_tests++))
total_tests=$((total_tests + 1))

test_endpoint "Gateway Health" "http://localhost:8000/health" && ((passed_tests++))
total_tests=$((total_tests + 1))

echo ""
echo "2. Testing Auth Service"
echo "-----------------------"
test_endpoint "Auth Service Root" "http://localhost:8001" && ((passed_tests++))
total_tests=$((total_tests + 1))

test_endpoint "Auth Service Health" "http://localhost:8001/health" && ((passed_tests++))
total_tests=$((total_tests + 1))

echo ""
echo "3. Testing Notification Service"
echo "--------------------------------"
test_endpoint "Notification Service Root" "http://localhost:8002" && ((passed_tests++))
total_tests=$((total_tests + 1))

test_endpoint "Notification Service Health" "http://localhost:8002/health" && ((passed_tests++))
total_tests=$((total_tests + 1))

echo ""
echo "4. Testing Frontend"
echo "-------------------"
test_endpoint "Frontend" "http://localhost:12000" && ((passed_tests++))
total_tests=$((total_tests + 1))

echo ""
echo "5. Testing API Endpoints via Gateway"
echo "-------------------------------------"
test_endpoint "Get Users" "http://localhost:8000/api/v1/users" && ((passed_tests++))
total_tests=$((total_tests + 1))

test_endpoint "Get Groups" "http://localhost:8000/api/v1/groups" && ((passed_tests++))
total_tests=$((total_tests + 1))

echo ""
echo "6. Testing OpenAPI Documentation"
echo "---------------------------------"
test_endpoint "Gateway API Docs" "http://localhost:8000/docs" && ((passed_tests++))
total_tests=$((total_tests + 1))

test_endpoint "Auth API Docs" "http://localhost:8001/docs" && ((passed_tests++))
total_tests=$((total_tests + 1))

test_endpoint "Notification API Docs" "http://localhost:8002/docs" && ((passed_tests++))
total_tests=$((total_tests + 1))

echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "Total Tests: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$((total_tests - passed_tests))${NC}"
echo ""

if [ $passed_tests -eq $total_tests ]; then
    echo -e "${GREEN}✓ All tests passed! System is ready.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Check the output above.${NC}"
    echo ""
    echo "Troubleshooting tips:"
    echo "1. Ensure all services are running: docker-compose ps"
    echo "2. Check service logs: docker-compose logs -f"
    echo "3. Verify ports are not in use: lsof -i :8000,8001,8002,12000"
    echo "4. Try restarting services: docker-compose restart"
    exit 1
fi
