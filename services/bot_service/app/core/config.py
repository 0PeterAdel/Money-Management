"""
Configuration for Bot Service
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
# config.py is at: services/bot_service/app/core/config.py
# .env is at: .env (4 levels up)
possible_paths = [
    Path(__file__).resolve().parents[4] / ".env",  # Absolute: bot_service/app/core/config.py -> root
    Path(__file__).parent.parent.parent.parent.parent / ".env",  # Relative path
    Path.cwd().parent.parent / ".env",  # From bot_service directory
]

env_loaded = False
for env_path in possible_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        env_loaded = True
        print(f"Loaded .env from: {env_path}", file=sys.stderr)
        break

if not env_loaded:
    print(f"Warning: No .env file found in standard locations", file=sys.stderr)


class Settings:
    """Application settings"""
    APP_NAME: str = "Bot Service"
    VERSION: str = "1.0.0"
    
    def __init__(self):
        # Telegram Bot (loaded after __init__ to ensure dotenv is loaded first)
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        # API Gateway URL
        self.API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
        
        # Validate critical settings
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN is not set!\n"
                "Please set it in .env file or environment variables."
            )


settings = Settings()
