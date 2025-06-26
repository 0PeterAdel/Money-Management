# bot/bot_main.py - THE DEFINITIVE, STABLE ARCHITECTURE

import logging
import requests
import json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
)
# Make sure config.py is in the parent directory
from config import TELEGRAM_BOT_TOKEN
# Make sure locales.py is in the same directory (bot/)
from locales import t

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================================================
# --- Conversation States ---
# ===============================================================
(
    # Top-Level States
    LOGGED_OUT, LOGGED_IN,
    # Login Flow
    AWAIT_LOGIN_USERNAME, AWAIT_LOGIN_PASSWORD,
    # Register Flow
    AWAIT_REG_USERNAME, AWAIT_REG_PASSWORD, AWAIT_REG_CONFIRM_PASSWORD,
    # Expense Flow
    EXPENSE_AWAIT_GROUP, EXPENSE_AWAIT_DESC, EXPENSE_AWAIT_AMOUNT, 
    EXPENSE_AWAIT_CATEGORY, EXPENSE_AWAIT_PARTICIPANTS, EXPENSE_AWAIT_CONFIRM,
    # Groups Flow
    GROUPS_MENU, GROUP_AWAIT_CREATE_NAME, GROUP_AWAIT_CREATE_DESC, GROUP_AWAIT_ADD_MEMBER
) = range(18)

# ===============================================================
# --- Helper Functions ---
# ===============================================================

def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [t("btn_balance", lang), t("btn_new_expense", lang)],
        [t("btn_groups", lang), t("btn_wallet", lang)],
        [t("btn_my_votes", lang), t("btn_settings", lang)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===============================================================
# --- Top-Level Command Handlers (Entry Points & Cancel) ---
# ===============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.clear()
    context.user_data['lang'] = 'en'
    await update.message.reply_text(t("welcome", 'en', name=user.first_name), reply_markup=ReplyKeyboardRemove())
    return LOGGED_OUT

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("ask_username", lang))
    return AWAIT_LOGIN_USERNAME

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text("Operation cancelled.")
    if context.user_data.get('is_logged_in'):
        await update.message.reply_text(t("main_menu_prompt", lang), reply_markup=get_main_menu_keyboard(lang))
        return LOGGED_IN
    else:
        await update.message.reply_text("You are logged out.", reply_markup=ReplyKeyboardRemove())
        return LOGGED_OUT

# =================================================================
# --- State Handlers for the Master Conversation ---
# =================================================================

# --- Login Flow ---
async def await_login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['username_to_check'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("ask_password", lang))
    return AWAIT_LOGIN_PASSWORD

async def await_login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = context.user_data.get('username_to_check')
    password = update.message.text
    telegram_id = str(update.effective_user.id)
    lang = context.user_data.get('lang', 'en')
    payload = {"username": username, "password": password, "telegram_id": telegram_id}
    
    try:
        response = requests.post(f"{API_BASE_URL}/users/link-telegram", json=payload)
        if response.status_code == 200:
            user_data = response.json()
            context.user_data['system_user_id'] = user_data.get('id')
            context.user_data['is_logged_in'] = True
            await update.message.reply_text(t("login_success", lang))
            await update.message.reply_text(text=t("main_menu_prompt", lang), reply_markup=get_main_menu_keyboard(lang))
            return LOGGED_IN
        else:
            await update.message.reply_text(t("login_fail", lang))
            return LOGGED_OUT
    except Exception as e:
        await update.message.reply_text(f"Server connection error: {e}")
        return LOGGED_OUT

# --- Main Menu Handler (Router) ---
async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    text = update.message.text
    user_id = context.user_data.get('system_user_id')

    if not user_id:
        await update.message.reply_text("Session expired. Please /login again.")
        return LOGGED_OUT

    # Route to simple commands
    if text == t("btn_balance", lang):
        # The logic for balance summary is here now
        response = requests.get(f"{API_BASE_URL}/balance-summary")
        summary = response.json()
        if not summary:
            await update.message.reply_text(t("no_debts", lang))
            return LOGGED_IN
        message = f"{t('balance_header', lang)}\n\n"
        # ... formatting logic ...
        await update.message.reply_text(message, parse_mode='Markdown')
        return LOGGED_IN

    # Route to conversation sub-flows
    elif text == t("btn_new_expense", lang):
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/groups")
        groups = response.json()
        if not groups:
            await update.message.reply_text(t("expense_no_groups", lang))
            return LOGGED_IN
        keyboard = [[InlineKeyboardButton(g['name'], callback_data=f"exp_group_{g['id']}")] for g in groups]
        await update.message.reply_text(t("expense_start", lang), reply_markup=InlineKeyboardMarkup(keyboard))
        return EXPENSE_AWAIT_GROUP
    
    # ... Add routers for other buttons like "My Groups", "My Wallet"
    else:
        await update.message.reply_text("Please select a valid option from the menu.")
        return LOGGED_IN

# --- Expense Sub-Flow Handlers ---
async def expense_await_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['expense_flow'] = {}
    context.user_data['expense_flow']['group_id'] = int(query.data.split('_')[2])
    await query.edit_message_text("What is the expense description?")
    return EXPENSE_AWAIT_DESC

async def expense_await_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['expense_flow']['description'] = update.message.text
    await update.message.reply_text("What is the total amount?")
    return EXPENSE_AWAIT_AMOUNT
    
# ... The rest of the expense flow handlers would follow the same pattern ...
# ... each one collecting data and returning the next state constant ...
# ... until the final confirmation, which returns LOGGED_IN ...

# =================================================================
# --- Main Application Setup ---
# =================================================================

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # The Master Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('login', login_command),
        ],
        states={
            LOGGED_OUT: [
                CommandHandler('login', login_command),
                # Add CommandHandler for 'register' here when you build it
            ],
            AWAIT_LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, await_login_username)],
            AWAIT_LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, await_login_password)],
            
            # This is the main state after login. It acts as a router.
            LOGGED_IN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_router)
            ],
            
            # States for the "New Expense" sub-flow, entered from LOGGED_IN state
            EXPENSE_AWAIT_GROUP: [CallbackQueryHandler(expense_await_group)],
            EXPENSE_AWAIT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_await_description)],
            # ... and so on for the rest of the expense states
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    
    # A global handler for voting buttons can still exist outside the main conversation
    # application.add_handler(CallbackQueryHandler(vote_button_callback, pattern=r'^vote_'))

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()