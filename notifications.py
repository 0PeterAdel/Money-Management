# notifications.py
import telegram
from config import TELEGRAM_BOT_TOKEN
import asyncio

# Initialize the bot outside the function to reuse the object
if TELEGRAM_BOT_TOKEN:
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
else:
    bot = None

async def send_telegram_message(chat_id: str, message: str):
    """
    Sends a message to a specific Telegram chat ID.
    """
    if not bot:
        print("Telegram bot is not configured. Skipping notification.")
        return

    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        print(f"Successfully sent message to chat_id: {chat_id}")
    except Exception as e:
        print(f"Failed to send message to {chat_id}. Error: {e}")

# Example of how to run this async function from a sync context if needed
# This is useful for testing the function directly.
if __name__ == '__main__':
    # Replace with a real chat_id for testing
    test_chat_id = "YOUR_PERSONAL_TELEGRAM_ID" 
    asyncio.run(send_telegram_message(chat_id=test_chat_id, message="*Hello!* This is a test message from your Finance App."))
