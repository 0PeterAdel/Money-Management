# bot/bot_main.py
import logging
from telegram.ext import (
    Application, CommandHandler, ConversationHandler, MessageHandler, filters
)
from config import TELEGRAM_BOT_TOKEN
# Import handlers from the new structure
from handlers.registration import (
    start_command, login_start, received_username, received_password,
    set_language, received_language, cancel,
    USERNAME, PASSWORD, LANGUAGE
)
from handlers.info import balance_summary_command

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # --- Conversation Handler for Login ---
    login_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login_start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # --- Conversation Handler for Language ---
    lang_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("language", set_language)],
        states={
            LANGUAGE: [MessageHandler(filters.Regex("^(English 🇬🇧|العربية 🇪🇬)$"), received_language)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add all handlers to the application
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(login_conv_handler)
    application.add_handler(lang_conv_handler)
    application.add_handler(CommandHandler("balance", balance_summary_command))
    
    # ... Here you would add handlers for /new_expense, /my_votes, etc.
    
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()