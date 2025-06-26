# bot/handlers/registration.py - FULL UPDATED FILE

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
import requests
from ..locales import t # Use .. for relative import

# --- States for Conversation ---
USERNAME, PASSWORD, LANGUAGE = range(3)
API_BASE_URL = "http://127.0.0.1:8000"


# --- Helper function to create main menu ---
def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [t("btn_balance", lang), t("btn_new_expense", lang)],
        [t("btn_groups", lang), t("btn_settings", lang)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Set default language if not already set
    if 'lang' not in context.user_data:
        context.user_data['lang'] = 'en' 
    
    lang = context.user_data['lang']
    await update.message.reply_text(t("welcome", lang, name=user.first_name))
    
    # If user is already logged in, show them the main menu directly
    if context.user_data.get('is_logged_in'):
        await update.message.reply_text(
            text=t("main_menu_prompt", lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
    return ConversationHandler.END


async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    # Remove any existing keyboard
    await update.message.reply_text(t("ask_username", lang), reply_markup=ReplyKeyboardRemove())
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
            
            # First, send the success message
            await update.message.reply_text(t("login_success", lang))
            
            # **NEW**: Then, send the main menu prompt with the new keyboard
            await update.message.reply_text(
                text=t("main_menu_prompt", lang),
                reply_markup=get_main_menu_keyboard(lang)
            )
            
            return ConversationHandler.END
        else:
            await update.message.reply_text(t("login_fail", lang))
            # On failure, don't show a menu. Let them try /login again.
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
        return ConversationHandler.END


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["English 🇬🇧", "العربية 🇪🇬"]]
    await update.message.reply_text(
        "Please select your language:\nالرجاء اختيار لغتك:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, input_field_placeholder="Select a language"),
    )
    return LANGUAGE


async def received_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "English" in text:
        context.user_data['lang'] = 'en'
        lang = 'en'
    elif "العربية" in text:
        context.user_data['lang'] = 'ar'
        lang = 'ar'
    else:
        # Default case if something goes wrong
        lang = context.user_data.get('lang', 'en')
        
    await update.message.reply_text(t("lang_updated", lang))
    
    # If user is logged in, show the menu again in the new language
    if context.user_data.get('is_logged_in'):
        await update.message.reply_text(
            text=t("main_menu_prompt", lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        # If not logged in, remove the one-time language keyboard
        await update.message.reply_text("...", reply_markup=ReplyKeyboardRemove())


    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    # If user is logged in, show the main menu on cancel, otherwise remove keyboard.
    if context.user_data.get('is_logged_in'):
        reply_markup = get_main_menu_keyboard(lang)
    else:
        reply_markup = ReplyKeyboardRemove()
        
    await update.message.reply_text("Operation cancelled.", reply_markup=reply_markup)
    return ConversationHandler.END