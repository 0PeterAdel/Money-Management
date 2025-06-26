# bot/bot_main.py - THE DEFINITIVE FINAL VERSION

import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
)
from config import TELEGRAM_BOT_TOKEN
# Import all handlers
from .handlers.registration import (
    start_command, login_start, register_start,
    login_received_username, login_received_password,
    register_received_username, register_received_password, register_received_confirm_password,
    set_language, received_language, cancel,
    LOGIN_USERNAME, LOGIN_PASSWORD, REGISTER_USERNAME, REGISTER_PASSWORD, REGISTER_CONFIRM_PASSWORD, LANGUAGE
)
from .handlers.info import balance_summary_command
from .handlers.expenses import (
    new_expense_start, group_selected, received_description, received_amount,
    category_selected, participant_selected, expense_confirmed,
    SELECT_GROUP, GET_DESCRIPTION, GET_AMOUNT, SELECT_CATEGORY, SELECT_PARTICIPANTS, CONFIRM_EXPENSE
)
from .handlers.groups import (
    my_groups_command, group_menu_handler, received_group_name, received_group_description, group_view_handler,
    GROUP_MENU, GROUP_CREATE_NAME, GROUP_CREATE_DESC, GROUP_VIEW
)
from .handlers.voting import my_votes_command, vote_button_callback
from .handlers.wallet import (
    my_wallet_command, wallet_group_selected, wallet_menu_handler, received_deposit_amount,
    WALLET_GROUP_SELECT, WALLET_MENU, WALLET_DEPOSIT_AMOUNT
)
from .locales import t

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # --- Conversation Handlers ---
    # Each conversation is now modular
    login_conv = ConversationHandler(
        entry_points=[CommandHandler("login", login_start)],
        states={
            LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_received_username)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_received_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    register_conv = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_received_username)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_received_password)],
            REGISTER_CONFIRM_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_received_confirm_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    settings_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^({t("btn_settings", "en")}|{t("btn_settings", "ar")})$'), set_language)],
        states={ LANGUAGE: [MessageHandler(filters.Regex("^(English 🇬🇧|العربية 🇪🇬)$"), received_language)] },
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
            GROUP_MENU: [CallbackQueryHandler(group_menu_handler, pattern="^group_view_|^group_create_new$")],
            GROUP_CREATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_group_name)],
            GROUP_CREATE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_group_description)],
            GROUP_VIEW: [CallbackQueryHandler(group_view_handler, pattern="^group_action_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    wallet_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^({t("btn_wallet", "en")}|{t("btn_wallet", "ar")})$'), my_wallet_command)],
        states={
            WALLET_GROUP_SELECT: [CallbackQueryHandler(wallet_group_selected, pattern="^w_group_")],
            WALLET_MENU: [CallbackQueryHandler(wallet_menu_handler, pattern="^wallet_")],
            WALLET_DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_deposit_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # --- Add all handlers ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(login_conv)
    application.add_handler(register_conv)
    application.add_handler(settings_conv)
    application.add_handler(expense_conv)
    application.add_handler(groups_conv)
    application.add_handler(wallet_conv)

    application.add_handler(MessageHandler(filters.Regex(f'^({t("btn_balance", "en")}|{t("btn_balance", "ar")})$'), balance_summary_command))
    application.add_handler(MessageHandler(filters.Regex(f'^({t("btn_my_votes", "en")}|{t("btn_my_votes", "ar")})$'), my_votes_command))
    
    # Add the main callback handler for voting buttons
    application.add_handler(CallbackQueryHandler(vote_button_callback, pattern=r'^vote_'))
    
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()