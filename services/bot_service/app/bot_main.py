"""
Telegram Bot Main Application
"""
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from app.core.config import settings
from app.locales import t

# Configuration
API_BASE_URL = settings.API_GATEWAY_URL
TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation States
(
    LOGGED_OUT,
    LOGGED_IN,
    AWAIT_LOGIN_USERNAME,
    AWAIT_LOGIN_PASSWORD,
    AWAIT_REG_USERNAME,
    AWAIT_REG_PASSWORD,
    AWAIT_REG_CONFIRM_PASSWORD,
    AWAIT_LANGUAGE,
) = range(8)


def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [t("btn_balance", lang), t("btn_new_expense", lang)],
        [t("btn_groups", lang), t("btn_wallet", lang)],
        [t("btn_my_votes", lang), t("btn_settings", lang)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.clear()
    context.user_data['lang'] = 'en'
    await update.message.reply_text(t("welcome", 'en', name=user.first_name))
    return LOGGED_OUT


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("ask_username", lang))
    return AWAIT_LOGIN_USERNAME


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("register_start", lang))
    return AWAIT_REG_USERNAME


async def await_login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['username_to_check'] = update.message.text
    await update.message.reply_text(t("ask_password", context.user_data.get('lang', 'en')))
    return AWAIT_LOGIN_PASSWORD


async def await_login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = context.user_data.get('username_to_check')
    password = update.message.text
    telegram_id = str(update.effective_user.id)
    lang = context.user_data.get('lang', 'en')
    
    payload = {"username": username, "password": password, "telegram_id": telegram_id}
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/link-telegram", json=payload)
        if response.status_code == 200:
            user_data = response.json()
            context.user_data.update({
                'system_user_id': user_data.get('id'),
                'is_logged_in': True
            })
            await update.message.reply_text(
                t("login_success", lang),
                reply_markup=get_main_menu_keyboard(lang)
            )
            return LOGGED_IN
        else:
            await update.message.reply_text(t("login_fail", lang))
            return LOGGED_OUT
    except Exception as e:
        await update.message.reply_text(f"Server connection error: {e}")
        return LOGGED_OUT


async def await_reg_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/users/by-name/{username}")
        if response.status_code == 200:
            await update.message.reply_text(t("register_username_taken", lang))
            return AWAIT_REG_USERNAME
    except requests.exceptions.RequestException:
        pass
    
    context.user_data['reg_username'] = username
    await update.message.reply_text(t("register_ask_password", lang, username=username))
    return AWAIT_REG_PASSWORD


async def await_reg_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_password'] = update.message.text
    await update.message.reply_text(
        t("register_ask_confirm_password", context.user_data.get('lang', 'en'))
    )
    return AWAIT_REG_CONFIRM_PASSWORD


async def await_reg_confirm_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = context.user_data['reg_password']
    confirm_password = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    if password != confirm_password:
        await update.message.reply_text(t("register_password_mismatch", lang))
        return AWAIT_REG_PASSWORD
    
    username = context.user_data['reg_username']
    telegram_id = str(update.effective_user.id)
    payload = {"name": username, "password": password, "telegram_id": telegram_id}
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/register", json=payload)
        if response.status_code == 201:
            user_data = response.json()
            context.user_data.update({
                'system_user_id': user_data.get('id'),
                'is_logged_in': True
            })
            await update.message.reply_text(
                t("register_success", lang),
                reply_markup=get_main_menu_keyboard(lang)
            )
            del context.user_data['reg_username'], context.user_data['reg_password']
            return LOGGED_IN
        else:
            await update.message.reply_text(f"Error: {response.json().get('detail')}")
            return LOGGED_OUT
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
        return LOGGED_OUT


async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('is_logged_in'):
        await update.message.reply_text("Please use /login or /register to start.")
        return LOGGED_OUT
    
    await update.message.reply_text("Feature coming soon! Stay tuned.")
    return LOGGED_IN


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text("Operation cancelled.")
    return LOGGED_IN


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured!")
        return
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            LOGGED_OUT: [
                CommandHandler('login', login_command),
                CommandHandler('register', register_command),
            ],
            AWAIT_LOGIN_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, await_login_username)
            ],
            AWAIT_LOGIN_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, await_login_password)
            ],
            AWAIT_REG_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, await_reg_username)
            ],
            AWAIT_REG_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, await_reg_password)
            ],
            AWAIT_REG_CONFIRM_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, await_reg_confirm_password)
            ],
            LOGGED_IN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_router)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    logger.info("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
