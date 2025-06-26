# bot/handlers/registration.py - FULL UPDATED FILE

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import requests
from ..locales import t

# --- States for Conversations ---
# Login states
LOGIN_USERNAME, LOGIN_PASSWORD = range(2)
# Register states
REGISTER_USERNAME, REGISTER_PASSWORD, REGISTER_CONFIRM_PASSWORD = range(2, 5)
# Language state
LANGUAGE = range(5, 6)

API_BASE_URL = "http://127.0.0.1:8000"

# --- Helper function to create main menu ---
def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [t("btn_balance", lang), t("btn_new_expense", lang)],
        [t("btn_groups", lang), t("btn_my_votes", lang)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if 'lang' not in context.user_data: context.user_data['lang'] = 'en'
    lang = context.user_data['lang']
    
    await update.message.reply_text(t("welcome", lang, name=user.first_name))
    
    if context.user_data.get('is_logged_in'):
        await update.message.reply_text(text=t("main_menu_prompt", lang), reply_markup=get_main_menu_keyboard(lang))
    return ConversationHandler.END

# --- LOGIN FLOW ---
async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("ask_username", lang), reply_markup=ReplyKeyboardRemove())
    return LOGIN_USERNAME

async def login_received_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['username'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("ask_password", lang))
    return LOGIN_PASSWORD

async def login_received_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username, password = context.user_data['username'], update.message.text
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
        else:
            await update.message.reply_text(t("login_fail", lang))
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
    return ConversationHandler.END

# --- REGISTRATION FLOW ---
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("register_start", lang), reply_markup=ReplyKeyboardRemove())
    return REGISTER_USERNAME

async def register_received_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    lang = context.user_data.get('lang', 'en')
    try:
        response = requests.get(f"{API_BASE_URL}/users/by-name/{username}")
        if response.status_code == 200:
            await update.message.reply_text(t("register_username_taken", lang))
            return REGISTER_USERNAME # Ask again
    except Exception: # Assuming 404 means username is available
        pass

    context.user_data['reg_username'] = username
    await update.message.reply_text(t("register_ask_password", lang, username=username))
    return REGISTER_PASSWORD

async def register_received_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_password'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("register_ask_confirm_password", lang))
    return REGISTER_CONFIRM_PASSWORD

async def register_received_confirm_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = context.user_data['reg_password']
    confirm_password = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    if password != confirm_password:
        await update.message.reply_text(t("register_password_mismatch", lang))
        return REGISTER_PASSWORD # Go back to password step

    username = context.user_data['reg_username']
    telegram_id = str(update.effective_user.id)
    
    payload = {"name": username, "password": password, "telegram_id": telegram_id}
    try:
        response = requests.post(f"{API_BASE_URL}/users", json=payload)
        if response.status_code == 201:
            user_data = response.json()
            context.user_data['system_user_id'] = user_data.get('id')
            context.user_data['is_logged_in'] = True
            await update.message.reply_text(t("register_success", lang))
            await update.message.reply_text(text=t("main_menu_prompt", lang), reply_markup=get_main_menu_keyboard(lang))
        else:
            await update.message.reply_text(f"Error: {response.json().get('detail')}")
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
    
    # Clean up registration data
    del context.user_data['reg_username']
    del context.user_data['reg_password']
    return ConversationHandler.END

# --- LANGUAGE FLOW ---
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (same as before)
    keyboard = [["English 🇬🇧", "العربية 🇪🇬"]]
    await update.message.reply_text("Please select your language:\nالرجاء اختيار لغتك:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return LANGUAGE

async def received_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (same as before)
    text, lang = (update.message.text, 'en') if "English" in update.message.text else (update.message.text, 'ar')
    context.user_data['lang'] = lang
    await update.message.reply_text(t("lang_updated", lang))
    if context.user_data.get('is_logged_in'):
        await update.message.reply_text(text=t("main_menu_prompt", lang), reply_markup=get_main_menu_keyboard(lang))
    else:
        await update.message.reply_text("...", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- CANCEL ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (same as before)
    lang = context.user_data.get('lang', 'en')
    reply_markup = get_main_menu_keyboard(lang) if context.user_data.get('is_logged_in') else ReplyKeyboardRemove()
    await update.message.reply_text("Operation cancelled.", reply_markup=reply_markup)
    return ConversationHandler.END