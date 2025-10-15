# Quick Command Reference

## 🚀 Essential Commands

### Start & Stop

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart auth_service

# Stop and remove everything (including volumes)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f auth_service
docker-compose logs -f gateway
docker-compose logs -f bot_service
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 auth_service
```

### Check Status

```bash
# List running containers
docker-compose ps

# Check resource usage
docker stats

# Check individual service
docker-compose ps auth_service
```

### Testing

```bash
# Run automated tests
./test_services.sh

# Test individual services
curl http://localhost:8000/health  # Gateway
curl http://localhost:8001/health  # Auth
curl http://localhost:8002/health  # Notification

# Test API endpoints
curl http://localhost:8000/api/v1/users
curl http://localhost:8000/api/v1/groups
```

## 🔧 Development Commands

### Rebuild Services

```bash
# Rebuild all services
docker-compose build

# Rebuild specific service
docker-compose build auth_service

# Rebuild without cache
docker-compose build --no-cache

# Build and start
docker-compose up -d --build
```

### Access Container Shell

```bash
# Access auth service shell
docker-compose exec auth_service /bin/bash

# Access gateway shell
docker-compose exec gateway /bin/bash

# Run Python commands
docker-compose exec auth_service python -c "print('Hello')"
```

### Database Operations

```bash
# Access SQLite database
docker-compose exec auth_service sqlite3 /app/assistant.db

# Backup database
docker cp money-management-auth_service-1:/app/assistant.db ./backup.db

# Restore database
docker cp ./backup.db money-management-auth_service-1:/app/assistant.db
```

## 🧹 Cleanup Commands

```bash
# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything (careful!)
docker system prune -a

# Clean Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
```

## 📦 Package Management

### Python Dependencies

```bash
# Install new package in auth service
docker-compose exec auth_service pip install package-name

# Update requirements.txt
docker-compose exec auth_service pip freeze > requirements.txt

# Reinstall all dependencies
docker-compose exec auth_service pip install -r requirements.txt
```

### Frontend Dependencies

```bash
# Install new npm package
docker-compose exec frontend npm install package-name

# Update package.json
docker-compose exec frontend npm update

# Install all dependencies
docker-compose exec frontend npm install
```

## 🔍 Debugging Commands

### Check Ports

```bash
# Check if ports are in use
lsof -i :8000  # Gateway
lsof -i :8001  # Auth
lsof -i :8002  # Notification
lsof -i :12000 # Frontend
lsof -i :6379  # Redis

# Kill process on port
kill -9 $(lsof -t -i:8000)
```

### Network Debugging

```bash
# List Docker networks
docker network ls

# Inspect network
docker network inspect money-management_app_network

# Test connectivity between services
docker-compose exec gateway ping auth_service
docker-compose exec gateway curl http://auth_service:8001/health
```

### Environment Variables

```bash
# View environment variables
docker-compose exec auth_service env

# Check specific variable
docker-compose exec auth_service echo $DATABASE_URL

# Load new .env file
docker-compose down
docker-compose up -d
```

## 📊 Monitoring Commands

### Real-time Monitoring

```bash
# Watch container stats
docker stats

# Watch logs
docker-compose logs -f --tail=50

# Watch specific service
watch -n 2 'curl -s http://localhost:8001/health'
```

### Performance Testing

```bash
# Test response time
time curl http://localhost:8000/api/v1/users

# Load testing (with apache bench)
ab -n 1000 -c 10 http://localhost:8000/health

# Monitor resource usage
docker stats --no-stream
```

## 🗄️ Backup & Restore

### Database Backup

```bash
# Create timestamped backup
cp assistant.db backups/assistant-$(date +%Y%m%d-%H%M%S).db

# Backup from Docker container
docker-compose exec auth_service cp /app/assistant.db /app/backup.db
docker cp money-management-auth_service-1:/app/backup.db ./backup.db

# Automated daily backup (add to cron)
0 2 * * * cd /path/to/Money-Management && cp assistant.db backups/assistant-$(date +%Y%m%d).db
```

### Full System Backup

```bash
# Backup configuration
tar -czf config-backup.tar.gz .env docker-compose.yml

# Backup code
tar -czf code-backup.tar.gz services/ gateway/ shared/

# Complete backup
tar -czf full-backup-$(date +%Y%m%d).tar.gz \
  services/ gateway/ shared/ frontend/ \
  docker-compose.yml .env assistant.db
```

## 🔄 Update & Upgrade

### Pull Latest Images

```bash
# Pull latest base images
docker-compose pull

# Rebuild with latest
docker-compose build --pull

# Update and restart
docker-compose pull && docker-compose up -d
```

### Update Dependencies

```bash
# Update Python packages
docker-compose exec auth_service pip install --upgrade pip
docker-compose exec auth_service pip list --outdated

# Update npm packages
docker-compose exec frontend npm outdated
docker-compose exec frontend npm update
```

## 🧪 Testing Commands

### Unit Testing

```bash
# Run pytest in auth service
docker-compose exec auth_service pytest

# Run with coverage
docker-compose exec auth_service pytest --cov=app

# Run specific test
docker-compose exec auth_service pytest tests/test_users.py
```

### Integration Testing

```bash
# Test service communication
docker-compose exec gateway curl http://auth_service:8001/health
docker-compose exec bot_service curl http://gateway:8000/health

# Test database connection
docker-compose exec auth_service python -c "from app.db.base import engine; print(engine)"
```

## 🔐 Security Commands

### Check Security

```bash
# Scan for vulnerabilities
docker scan money-management-auth_service

# Check image security
docker-compose exec auth_service pip check

# Audit npm packages
docker-compose exec frontend npm audit
```

### Update Secrets

```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file
nano .env  # Update SECRET_KEY

# Restart services
docker-compose restart
```

## 📝 Quick Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# Docker Compose shortcuts
alias dc='docker-compose'
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dclogs='docker-compose logs -f'
alias dcps='docker-compose ps'
alias dcrestart='docker-compose restart'

# Money Management specific
alias mmstart='cd ~/Zone/Rebos/Money-Management && docker-compose up -d'
alias mmstop='cd ~/Zone/Rebos/Money-Management && docker-compose down'
alias mmlogs='cd ~/Zone/Rebos/Money-Management && docker-compose logs -f'
alias mmtest='cd ~/Zone/Rebos/Money-Management && ./test_services.sh'
```

## 🆘 Emergency Commands

### Service Not Responding

```bash
# Force restart
docker-compose restart auth_service

# Stop and start
docker-compose stop auth_service
docker-compose start auth_service

# Recreate container
docker-compose up -d --force-recreate auth_service
```

### Database Locked

```bash
# Stop all services
docker-compose down

# Remove lock files
rm -f assistant.db-shm assistant.db-wal

# Restart
docker-compose up -d
```

### Port Conflicts

```bash
# Find and kill processes
lsof -ti:8000 | xargs kill -9
lsof -ti:8001 | xargs kill -9
lsof -ti:8002 | xargs kill -9
lsof -ti:12000 | xargs kill -9

# Restart services
docker-compose up -d
```

### Nuclear Option (Reset Everything)

```bash
# WARNING: This will delete all data!

# Stop and remove everything
docker-compose down -v

# Remove all containers
docker container prune -f

# Remove all images
docker image prune -a -f

# Remove all volumes
docker volume prune -f

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

## 📚 Documentation Commands

```bash
# View README
cat README.md | less

# View Quick Start
cat QUICKSTART.md | less

# Generate API docs
docker-compose exec auth_service python -c "from app.main import app; print(app.openapi())" | jq
```

## 🎯 Common Workflows

### New Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes in services/auth_service/

# 3. Rebuild and test
docker-compose build auth_service
docker-compose up -d auth_service
./test_services.sh

# 4. Check logs
docker-compose logs -f auth_service
```

### Deploy to Production

```bash
# 1. Update .env with production values
cp .env.example .env.production
nano .env.production

# 2. Build production images
docker-compose -f docker-compose.yml build

# 3. Push to registry (if using)
docker-compose push

# 4. Deploy
docker-compose -f docker-compose.yml --env-file .env.production up -d

# 5. Verify
./test_services.sh
```

---

## 💡 Pro Tips

1. **Always check logs first**: `docker-compose logs -f [service]`
2. **Test after changes**: `./test_services.sh`
3. **Backup before updates**: `cp assistant.db backup.db`
4. **Use health checks**: All services have `/health` endpoint
5. **Monitor resources**: `docker stats` shows real-time usage

---

**For more information, see:**
- QUICKSTART.md - Getting started
- README.md - Full documentation
- VERIFICATION.md - Testing guide
