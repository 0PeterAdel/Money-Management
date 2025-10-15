<p align="center">
  <img src="static/logo.png" alt="Project Logo" width="150"/>
</p>

<h1 align="center">Money Management System - Microservices Edition</h1>

<p align="center">
  <strong>A modern microservices-based financial assistant with Telegram bot, web interface, and collaborative expense tracking.</strong>
  <br><br>
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-FastAPI-05998b.svg" alt="Framework">
  <img src="https://img.shields.io/badge/Bot-python--telegram--bot-blue.svg" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61dafb.svg" alt="Frontend">
  <img src="https://img.shields.io/badge/Architecture-Microservices-green.svg" alt="Architecture">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  <img src="static/dec.jpeg" alt="Project Showcase" width="100%">
</p>

## 📜 About The Project

This is a comprehensive, self-hosted financial management system built with a **modern microservices architecture**. The system features:

- **Microservices Architecture**: Independently deployable services for auth, notifications, and bot functionality
- **API Gateway**: Centralized routing and request handling
- **Modern Web Interface**: React + TypeScript frontend with beautiful UI
- **Telegram Bot**: Bilingual (English/Arabic) conversational bot interface
- **Collaborative Features**: Democratic voting system for expenses and deposits
- **Scalable Design**: Docker-based deployment with container orchestration

The system moves beyond simple expense logging by introducing collaborative governance, where financial entries and deposits require confirmation from group members, ensuring transparency and trust.

---

## ✨ Core Features

This system is packed with features designed for real-world collaborative financial management:

### 👤 **User & Group Management**
- **Secure User Registration:** New users can sign up directly via the Telegram bot with a username and a securely hashed password.
- **Telegram Account Linking:** Users can link their system account to their Telegram ID for a seamless and personalized experience.
- **Group Creation & Management:** Users can create groups, add members by username, and remove members safely (only if they have no outstanding financial ties within the group).
- **Secure Account Deletion:** Users can delete their accounts only if all their debts across the entire system are settled and all wallet balances are zero.

### 💸 **Advanced Expense & Debt Tracking**
- **Collaborative Expense Logging:** When a user adds an expense, it is not immediately confirmed. It enters a *pending* state and a voting request is sent to all other participants.
- **Democratic Confirmation System:** An expense is only confirmed and added to the ledger after receiving **more than 50% approval** from its participants. This prevents fraudulent or incorrect entries.
- **Dynamic Categorization:** Log expenses under predefined categories (Food, Rent, etc.) or create new custom categories on the fly, which are then saved for future use.
- **Partial Debt Settlement:** Debts can be paid off in multiple partial payments, and the system accurately tracks the remaining amount.

### 💰 **Shared Group Wallet (The "Hassala")**
- **Collaborative Deposits:** Users can request to deposit funds into a group's shared wallet. This action also requires voting and confirmation from other group members.
- **Secure Withdrawals:** Users can withdraw their personal funds from the group wallet, a process secured by requiring their account password.
- **Pay from Wallet:** Expenses can be paid directly from the group wallet's balance instead of a single user's pocket, automatically deducting the share from each participant's balance within the wallet.
- **Intra-Wallet Debt Settlement:** Users can settle outstanding debts with other members directly from their available balance in the group wallet.

### 🤖 **Intelligent Bot Interface**
- **Bilingual Support:** The bot is fully bilingual, supporting both English and Arabic, with the ability to switch languages on the fly.
- **Conversational Flows:** Instead of complex commands, the bot guides the user through processes like adding an expense with a series of simple questions and interactive buttons.
- **Smart Summaries (`/balance`):** Calculates the most simplified settlement plan, taking into account all personal debts and wallet balances across all groups to give a true net balance. For example, if A owes B 50 and B owes A 30, the summary will simply state "A owes B 20".
- **Real-time Notifications:** The bot uses a polling mechanism to automatically notify users of pending actions that require their vote.

---

## 🏗️ Microservices Architecture

The project follows a **modern microservices architecture** with the following components:

```
Money-Management/
├── services/
│   ├── auth_service/          # Authentication & User Management Service
│   │   ├── app/
│   │   │   ├── api/v1/routes/ # API endpoints (login, register, users, groups)
│   │   │   ├── core/          # Config & security utilities
│   │   │   ├── db/            # Database models & session
│   │   │   ├── schemas/       # Pydantic schemas
│   │   │   └── main.py        # Service entry point
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── notification_service/  # Notification Service (Email, SMS, Push)
│   │   ├── app/
│   │   │   ├── api/v1/routes/ # Notification endpoints
│   │   │   ├── core/          # Config & Celery setup
│   │   │   ├── workers/       # Celery workers (email, sms)
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── bot_service/           # Telegram Bot Service
│       ├── app/
│       │   ├── bot_main.py    # Bot application
│       │   ├── locales.py     # Translations (EN/AR)
│       │   └── core/          # Configuration
│       ├── Dockerfile
│       └── requirements.txt
│
├── gateway/                   # API Gateway (Request Router)
│   ├── app/
│   │   ├── main.py           # Gateway routing logic
│   │   └── routes/           # Service proxy routes
│   ├── Dockerfile
│   └── requirements.txt
│
├── shared/                    # Shared utilities across services
│   ├── utils/                # Logging, exceptions
│   ├── database/             # Base database classes
│   └── schemas/              # Common schemas
│
├── frontend/                  # React + TypeScript Web Application
│   ├── src/                  # React components & pages
│   ├── public/               # Static assets
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml        # Container orchestration
├── .env.docker              # Docker environment variables
└── README.md                # This file
```

### Service Communication

```
┌─────────────┐
│   Frontend  │ (Port 12000)
│  React/TS   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ API Gateway │ (Port 8000)
└──────┬──────┘
       │
       ├─────→ Auth Service (Port 8001)
       │         ↓ SQLite/PostgreSQL
       │
       ├─────→ Notification Service (Port 8002)
       │         ↓ Redis + Celery Workers
       │
       └─────→ Bot Service
                 ↓ Telegram API
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker** and **Docker Compose** (Recommended)
- **Node.js 20+** (for frontend development)
- **Python 3.11+** (for local development without Docker)

### Quick Start with Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd Money-Management
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.docker .env
   # Edit .env and add your TELEGRAM_BOT_TOKEN
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - Frontend: http://localhost:12000
   - API Gateway: http://localhost:8000
   - Auth Service: http://localhost:8001
   - Notification Service: http://localhost:8002

5. **View logs:**
   ```bash
   docker-compose logs -f
   ```

6. **Stop all services:**
   ```bash
   docker-compose down
   ```

### Local Development (Without Docker)

#### Backend Services

Each service can be run independently:

**1. Auth Service**
```bash
cd services/auth_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

**2. Notification Service**
```bash
cd services/notification_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

**3. Bot Service**
```bash
cd services/bot_service
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your_token_here"
export API_GATEWAY_URL="http://localhost:8000"
python -m app.bot_main
```

**4. API Gateway**
```bash
cd gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:12000

---

## 🤖 How to Use the Bot

1.  **Find your bot** on Telegram and send the `/start` command.
2.  **Create a new account** using the `/register` command. The bot will guide you through creating a username and password.
3.  Once registered, you are automatically logged in and will see the **main menu keyboard**.
4.  You can now explore the features:
    * **👥 My Groups:** To create your first group and add members.
    * **💰 My Wallet:** To deposit funds into a group's shared wallet.
    * **💸 New Expense:** To log a new expense after creating a group.
    * **🗳️ My Votes:** To see actions waiting for your confirmation.

---

## 🛠️ Technology Stack

### Backend Services
- **Framework:** FastAPI 0.115+
- **ORM:** SQLAlchemy 2.0
- **Database:** SQLite (development) / PostgreSQL (production ready)
- **Validation:** Pydantic 2.11+
- **Security:** Passlib + bcrypt for password hashing
- **Task Queue:** Celery + Redis (for async notifications)

### Frontend
- **Framework:** React 19 + TypeScript
- **Build Tool:** Vite 7
- **UI Library:** Radix UI + Tailwind CSS
- **State Management:** React Hooks
- **HTTP Client:** Axios
- **Routing:** React Router 7

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **API Gateway:** Custom FastAPI gateway with httpx
- **Message Broker:** Redis (for Celery)
- **Bot Framework:** python-telegram-bot 22+

---

## 📚 API Documentation

Once the services are running, you can access the interactive API documentation:

- **API Gateway:** http://localhost:8000/docs
- **Auth Service:** http://localhost:8001/docs
- **Notification Service:** http://localhost:8002/docs

### Key Endpoints

#### Auth Service (via Gateway)
- `POST /api/v1/register` - Register new user
- `POST /api/v1/link-telegram` - Link Telegram account
- `GET /api/v1/users` - Get all users
- `GET /api/v1/users/{user_id}` - Get user by ID
- `POST /api/v1/groups` - Create group
- `GET /api/v1/groups` - Get all groups

#### Notification Service (via Gateway)
- `POST /api/v1/send-email` - Send email notification
- `POST /api/v1/send-sms` - Send SMS notification
- `POST /api/v1/send-push` - Send push notification (Telegram)

---

## 🧪 Testing

### Running Tests

```bash
# Test individual services
cd services/auth_service
pytest

cd services/notification_service
pytest
```

### Health Checks

```bash
# Check service health
curl http://localhost:8000/health  # Gateway
curl http://localhost:8001/health  # Auth Service
curl http://localhost:8002/health  # Notification Service
```

---

## 🔒 Security Considerations

- **Password Hashing:** All passwords are hashed using bcrypt
- **Environment Variables:** Sensitive data stored in `.env` files (not committed)
- **CORS:** Configured for specific origins in production
- **Service Isolation:** Microservices architecture provides natural security boundaries
- **Input Validation:** Pydantic models validate all input data

---

## 🚢 Production Deployment

### Environment Variables

Create a `.env` file with production values:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_production_bot_token

# Database (use PostgreSQL in production)
DATABASE_URL=postgresql://user:pass@postgres:5432/money_management

# Security
SECRET_KEY=generate-a-long-random-secure-key-here

# Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Service URLs
AUTH_SERVICE_URL=http://auth_service:8001
NOTIFICATION_SERVICE_URL=http://notification_service:8002
API_GATEWAY_URL=http://gateway:8000
```

### Docker Production Build

```bash
# Build images
docker-compose build

# Run in production mode
docker-compose up -d

# Scale services if needed
docker-compose up -d --scale auth_service=3
```

---

## 📈 Monitoring & Logging

All services use structured logging with the shared logging utility:

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f auth_service
docker-compose logs -f gateway
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 Future Enhancements

- [ ] JWT authentication for API access
- [ ] WebSocket support for real-time notifications
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Multi-currency support
- [ ] Export reports (PDF, Excel)
- [ ] Integration with payment gateways
- [ ] Machine learning expense categorization

---

## 📄 License

This project is distributed under the MIT License. See `LICENSE` for more information.

---

## 👨‍💻 Author

Created with ❤️ for collaborative financial management

---

## 🙏 Acknowledgments

- FastAPI for the amazing web framework
- Telegram for the Bot API
- React community for the excellent frontend tools
- All contributors and users of this project

