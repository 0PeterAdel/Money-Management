<p align="center">
  <img src="static/logo.png" alt="Project Logo" width="150"/>
</p>

<h1 align="center">Collaborative Finance Assistant</h1>

<p align="center">
  <strong>An intelligent, self-hosted financial assistant managed via Telegram, designed for collaborative group and personal expense tracking.</strong>
  <br><br>
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-FastAPI-05998b.svg" alt="Framework">
  <img src="https://img.shields.io/badge/Bot-python--telegram--bot-blue.svg" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  <img src="static/dec.jpeg" alt="Project Showcase" width="100%">
</p>

## 📜 About The Project

This project is a comprehensive, self-hosted financial management system designed to function as a personal and group financial assistant. It moves beyond simple expense logging by introducing a layer of collaborative governance, where financial entries and deposits require confirmation from group members, ensuring transparency and trust.

The entire system is controlled through a sophisticated, bilingual (English/Arabic) Telegram bot that offers a seamless, conversational user experience. The backend is a robust API built with FastAPI, handling all the complex logic, data storage, and security.

The ultimate goal is to create a "Jarvis" for personal and group life management, starting with the most critical aspect: finances.

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

## 🏗️ Project Structure

The project is organized into two main components: the FastAPI backend and the Telegram Bot frontend.


Money-Management/
├── .env                  # <-- Store your secret keys here (e.g., bot token)
├── .gitignore            # <-- Ensures secret files are not uploaded to Git
├── main.py               # FastAPI application: The core backend API
├── models.py             # SQLAlchemy database models (the schema)
├── database.py           # Database engine and session configuration
├── security.py           # Password hashing and verification functions
├── config.py             # Loads environment variables from .env
├── notifications.py      # (Optional) Helper for sending notifications
├── requirements.txt      # List of all Python dependencies
├── bot/                  # Directory for all Telegram Bot code
│   ├── init.py
│   ├── bot_main.py       # The main, all-in-one bot application file
│   └── locales.py        # Contains all English and Arabic text strings
└── venv/                 # Python virtual environment


---

## 🚀 Getting Started

Follow these steps to get the project running on your local machine.

### Prerequisites

* Python 3.11+
* `pip` for package management

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd Money-Management
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(If `requirements.txt` does not exist, create it with `pip freeze > requirements.txt` after installing the packages mentioned below).*

4.  **Create the `.env` file:**
    Create a file named `.env` in the project root and add your Telegram bot token:
    ```env
    TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE_FROM_BOTFATHER"
    ```

### Running the Application

This project requires **two separate terminals** to run simultaneously: one for the API and one for the Telegram Bot.

1.  **Terminal 1: Start the Backend API**
    Make sure your virtual environment is activated, then run:
    ```bash
    uvicorn main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`. You can see the interactive documentation at `http://127.0.0.1:8000/docs`.

2.  **Terminal 2: Start the Telegram Bot**
    Open a new terminal, activate the same virtual environment, and run:
    ```bash
    python -m bot.bot_main
    ```
    The bot is now running and will start communicating with your API.

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

* **Backend:** FastAPI, SQLAlchemy, Pydantic
* **Database:** SQLite (for simplicity, easily upgradable to PostgreSQL)
* **Bot Framework:** `python-telegram-bot`
* **Security:** `passlib` with `bcrypt` for password hashing
* **Configuration:** `python-dotenv`

---

## 📄 License

This project is distributed under the MIT License. See `LICENSE` for more information.

