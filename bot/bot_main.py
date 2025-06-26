# bot/bot_main.py - FINAL VERSION WITH ALL HANDLERS

import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
)
from config import TELEGRAM_BOT_TOKEN
# Import handlers from the new structure
from .handlers.registration import (
    start_command, login_start, received_username, received_password,
    set_language, received_language, cancel,
    USERNAME, PASSWORD, LANGUAGE
)
from .handlers.info import balance_summary_command
from .handlers.expenses import (
    new_expense_start, group_selected, received_description, received_amount,
    category_selected, participant_selected, expense_confirmed,
    SELECT_GROUP, GET_DESCRIPTION, GET_AMOUNT, SELECT_CATEGORY, SELECT_PARTICIPANTS, CONFIRM_EXPENSE
)
# NEW import for group management
from .handlers.groups import (
    my_groups_command, group_menu_handler, received_group_name, received_group_description, group_view_handler,
    GROUP_MENU, GROUP_CREATE_NAME, GROUP_CREATE_DESC, GROUP_VIEW
)

from .locales import t

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# This is a placeholder for the settings command
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the language selection conversation."""
    return await set_language(update, context)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # --- Conversation Handlers ---
    login_conv = ConversationHandler(
        entry_points=[CommandHandler("login", login_start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    lang_conv = ConversationHandler(
        entry_points=[CommandHandler("language", set_language)],
        states={
            LANGUAGE: [MessageHandler(filters.Regex("^(English 🇬🇧|العربية 🇪🇬)$"), received_language)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    expense_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^({t("btn_new_expense", "en")}|{t("btn_new_expense", "ar")})$'), new_expense_start)],
        states={
            SELECT_GROUP: [CallbackQueryHandler(group_selected, pattern="^group_")],
            GET_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_description)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_amount)],
            SELECT_CATEGORY: [CallbackQueryHandler(category_selected, pattern="^cat_")],
            SELECT_PARTICIPANTS: [CallbackQueryHandler(participant_selected, pattern="^part_")],
            CONFIRM_EXPENSE: [CallbackQueryHandler(expense_confirmed, pattern="^exp_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    groups_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^({t("btn_groups", "en")}|{t("btn_groups", "ar")})$'), my_groups_command)],
        states={
            GROUP_MENU: [CallbackQueryHandler(group_menu_handler, pattern="^group_")],
            GROUP_CREATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_group_name)],
            GROUP_CREATE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_group_description)],
            GROUP_VIEW: [CallbackQueryHandler(group_view_handler, pattern="^group_action_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Settings conversation, which reuses the language handler
    settings_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^({t("btn_settings", "en")}|{t("btn_settings", "ar")})$'), settings_command)],
        states={
            LANGUAGE: [MessageHandler(filters.Regex("^(English 🇬🇧|العربية 🇪🇬)$"), received_language)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # --- Add all handlers ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(login_conv)
    application.add_handler(lang_conv)
    application.add_handler(expense_conv)
    application.add_handler(groups_conv)
    application.add_handler(settings_conv)

    # Add handler for the balance button
    application.add_handler(
        MessageHandler(filters.Regex(f'^({t("btn_balance", "en")}|{t("btn_balance", "ar")})$'), balance_summary_command)
    )
    
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()