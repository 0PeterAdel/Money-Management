# bot/handlers/registration.py
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
import requests
from ..locales import t # Use .. for relative import

# --- States for Conversation ---
USERNAME, PASSWORD, LANGUAGE = range(3)
API_BASE_URL = "http://127.0.0.1:8000"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['lang'] = 'en' # Default to English
    await update.message.reply_text(t("welcome", 'en', name=user.first_name))
    return ConversationHandler.END

async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("ask_username", lang))
    return USERNAME

async def received_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['username'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("ask_password", lang))
    return PASSWORD

async def received_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = context.user_data['username']
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
            return ConversationHandler.END
        else:
            await update.message.reply_text(t("login_fail", lang))
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
        return ConversationHandler.END

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["English 🇬🇧", "العربية 🇪🇬"]]
    await update.message.reply_text(
        "Please select your language:\nالرجاء اختيار لغتك:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
    )
    return LANGUAGE

async def received_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "English" in text:
        context.user_data['lang'] = 'en'
        await update.message.reply_text(t("lang_updated", 'en'), reply_markup=ReplyKeyboardRemove())
    elif "العربية" in text:
        context.user_data['lang'] = 'ar'
        await update.message.reply_text(t("lang_updated", 'ar'), reply_markup=ReplyKeyboardRemove())
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END