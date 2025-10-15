# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the Telegram Bot Token from the environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Optional: Check if the token is set
if not TELEGRAM_BOT_TOKEN:
    print("Warning: TELEGRAM_BOT_TOKEN is not set in the .env file.")
    # You might want to raise an error in a real production environment
    # raise ValueError("No TELEGRAM_BOT_TOKEN set for the bot")
