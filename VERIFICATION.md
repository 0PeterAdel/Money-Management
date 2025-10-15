# Project Verification & Testing Guide

## ✅ Structure Verification

Your project now has the following microservices structure:

```
✓ services/auth_service/        - User & Group Management
✓ services/notification_service/ - Email, SMS, Push Notifications  
✓ services/bot_service/          - Telegram Bot
✓ gateway/                       - API Gateway
✓ shared/                        - Shared Utilities
✓ frontend/                      - React Web App
✓ docker-compose.yml             - Container Orchestration
```

## 🧪 Testing Steps

### Step 1: Environment Setup

```bash
# Copy environment template
cp .env.docker .env

# Edit .env and add your TELEGRAM_BOT_TOKEN
nano .env  # or code .env
```

### Step 2: Start Services with Docker

```bash
# Build and start all services
docker-compose up -d

# Check running containers
docker-compose ps
```

Expected output:
```
NAME                    SERVICE              STATUS
auth_service            auth_service         running
notification_service    notification_service running
bot_service             bot_service          running
gateway                 gateway              running
redis                   redis                running
celery_worker           celery_worker        running
frontend                frontend             running
```

### Step 3: Run Automated Tests

```bash
# Make script executable (if not already)
chmod +x test_services.sh

# Run tests
./test_services.sh
```

Expected output:
```
✓ Gateway Root - PASSED
✓ Gateway Health - PASSED
✓ Auth Service Root - PASSED
✓ Auth Service Health - PASSED
✓ Notification Service Root - PASSED
✓ Notification Service Health - PASSED
✓ Frontend - PASSED
✓ All tests passed! System is ready.
```

### Step 4: Manual Service Verification

```bash
# Test Gateway
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Test Auth Service
curl http://localhost:8001/health
# Expected: {"status":"healthy"}

# Test Notification Service
curl http://localhost:8002/health
# Expected: {"status":"healthy"}

# Test API Docs are accessible
curl -I http://localhost:8000/docs
# Expected: HTTP/1.1 200 OK
```

### Step 5: Frontend Verification

1. Open browser: http://localhost:12000
2. You should see the login page
3. Try registering a new user
4. Login with the credentials

### Step 6: Test User Registration (API)

```bash
# Create a test user via API
curl -X POST http://localhost:8000/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "testuser",
    "password": "testpass123"
  }'
```

Expected response:
```json
{
  "id": 1,
  "name": "testuser",
  "telegram_id": null,
  "created_at": "2025-10-14T..."
}
```

### Step 7: Test Telegram Bot

1. Find your bot on Telegram
2. Send `/start`
3. Send `/register`
4. Follow the registration flow
5. Try `/login` with the web credentials

### Step 8: Check Service Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f gateway
docker-compose logs -f auth_service
docker-compose logs -f bot_service
```

## 🔍 Troubleshooting

### Issue: Ports Already in Use

```bash
# Check what's using the ports
lsof -i :8000  # Gateway
lsof -i :8001  # Auth Service
lsof -i :8002  # Notification Service
lsof -i :12000 # Frontend

# Stop old services
pkill -f uvicorn
pkill -f "npm run dev"
```

### Issue: Docker Containers Won't Start

```bash
# Stop all containers
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache

# Start again
docker-compose up -d
```

### Issue: Database Errors

```bash
# Check if database file exists
ls -la assistant.db

# If using old database, ensure it's in the right location
# The auth_service expects it at the root level or mounted volume
```

### Issue: Frontend Can't Connect to Backend

1. Check `.env` file has correct values:
   ```
   VITE_API_BASE_URL=http://localhost:8000
   ```

2. Restart frontend:
   ```bash
   docker-compose restart frontend
   ```

3. Check browser console for CORS errors

### Issue: Bot Not Responding

1. Verify bot token in `.env`:
   ```bash
   grep TELEGRAM_BOT_TOKEN .env
   ```

2. Check bot service logs:
   ```bash
   docker-compose logs bot_service
   ```

3. Ensure bot is not blocked by Telegram

## 📊 Performance Verification

### Check Resource Usage

```bash
# View container stats
docker stats

# Expected: Each service using ~30-60MB RAM
```

### Test Response Times

```bash
# Test gateway latency
time curl http://localhost:8000/health

# Should be < 100ms
```

## 🎯 Feature Testing Checklist

- [ ] User Registration (Web & Bot)
- [ ] User Login (Web & Bot)
- [ ] Create Group
- [ ] Add Members to Group
- [ ] Create Expense
- [ ] View Expenses
- [ ] Wallet Operations
- [ ] Notifications
- [ ] Balance Summary

## 📈 Success Criteria

✅ All services start without errors
✅ All health checks pass
✅ Frontend loads and is accessible
✅ API documentation is accessible
✅ User registration works
✅ Telegram bot responds
✅ Database operations work
✅ Services can communicate with each other

## 🎊 Next Steps After Verification

1. **Production Deployment**
   - Update `.env` with production values
   - Use PostgreSQL instead of SQLite
   - Set strong SECRET_KEY
   - Configure proper CORS origins

2. **Add More Features**
   - Migrate remaining endpoints from `main.py`
   - Add JWT authentication
   - Implement WebSocket for real-time updates
   - Add more notification channels

3. **Monitoring Setup**
   - Add Prometheus metrics
   - Setup Grafana dashboards
   - Configure alerts
   - Add APM (Application Performance Monitoring)

4. **CI/CD Pipeline**
   - Setup GitHub Actions
   - Automated testing
   - Automated deployments
   - Docker image publishing

## 🆘 Need Help?

1. **Check Documentation**
   - README.md - Full documentation
   - QUICKSTART.md - Quick setup guide
   - MIGRATION_GUIDE.md - Migration instructions

2. **Check Service Logs**
   ```bash
   docker-compose logs -f [service_name]
   ```

3. **Health Check Endpoints**
   - Gateway: http://localhost:8000/health
   - Auth: http://localhost:8001/health
   - Notification: http://localhost:8002/health

4. **API Documentation**
   - Gateway: http://localhost:8000/docs
   - Auth: http://localhost:8001/docs
   - Notification: http://localhost:8002/docs

## ✨ Verification Complete!

If all tests pass, your microservices architecture is ready for use! 🚀
