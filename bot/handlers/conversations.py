# bot/conversations.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
import requests
import json
from .locales import t

API_BASE_URL = "http://127.0.0.1:8000"

# ===============================================================
# --- STATE DEFINITIONS ---
# Define all possible states for our single ConversationHandler
(
    # Top-Level States
    LOGGED_OUT,
    LOGGED_IN,  # This is the main menu state

    # Registration Flow
    REGISTER_USERNAME, REGISTER_PASSWORD, REGISTER_CONFIRM_PASSWORD,
    
    # Login Flow
    LOGIN_USERNAME, LOGIN_PASSWORD,

    # Language/Settings Flow
    AWAIT_LANGUAGE,

    # New Expense Flow
    EXPENSE_SELECT_GROUP, EXPENSE_GET_DESC, EXPENSE_GET_AMOUNT, 
    EXPENSE_SELECT_CATEGORY, EXPENSE_SELECT_PARTICIPANTS, EXPENSE_CONFIRM,

    # Group Management Flow
    GROUP_MENU, GROUP_CREATE_NAME, GROUP_CREATE_DESC, GROUP_VIEW, 
    ADD_MEMBER_USERNAME, REMOVE_MEMBER_SELECT,

    # Wallet Flow
    WALLET_GROUP_SELECT, WALLET_MENU, WALLET_DEPOSIT_AMOUNT, 
    WALLET_WITHDRAW_AMOUNT, WALLET_WITHDRAW_PASSWORD, WALLET_SETTLE_CONFIRM,
) = range(22)
# ===============================================================


# ===============================================================
# --- HELPER FUNCTIONS (for creating keyboards) ---
# ===============================================================

def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [t("btn_balance", lang), t("btn_new_expense", lang)],
        [t("btn_groups", lang), t("btn_wallet", lang)],
        [t("btn_my_votes", lang), t("btn_settings", lang)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder=t("main_menu_prompt", lang))


# ===============================================================
# --- COMMAND HANDLERS (Entry Points & Simple Commands) ---
# ===============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.clear()
    context.user_data['lang'] = 'en'
    await update.message.reply_text(t("welcome", 'en', name=user.first_name), reply_markup=ReplyKeyboardRemove())
    return LOGGED_OUT

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("ask_username", lang))
    return LOGIN_USERNAME

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("register_start", lang))
    return REGISTER_USERNAME
    
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This is a simple command that runs and returns to the main menu
    lang = context.user_data.get('lang', 'en')
    user_id = context.user_data.get('system_user_id')
    
    try:
        response = requests.get(f"{API_BASE_URL}/balance-summary")
        response.raise_for_status()
        summary = response.json()
        
        if not summary:
            await update.message.reply_text(t("no_debts", lang))
            return LOGGED_IN

        message = f"{t('balance_header', lang)}\n\n"
        user_involved = False
        for item in summary:
            debtor_name = item['debtor']['name']
            creditor_name = item['creditor']['name']
            amount = item['amount']
            
            if item['debtor']['id'] == user_id:
                user_involved = True
                message += f"• {t('you_owe', lang)} *{creditor_name}* `{amount}` EGP\n"
            elif item['creditor']['id'] == user_id:
                user_involved = True
                message += f"• *{debtor_name}* {t('owes_you', lang)} `{amount}` EGP\n"

        if not user_involved:
             message += t("no_debts", lang)

        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        
    return LOGGED_IN # Stay in the main menu state

# You would create similar simple command handlers for my_votes, etc.

# ===============================================================
# --- CONVERSATION STATE HANDLERS ---
# ===============================================================

# --- Login Flow ---
async def received_username_for_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['username_to_check'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("ask_password", lang))
    return LOGIN_PASSWORD

async def received_password_for_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            return LOGGED_IN # <--- Transition to the main menu state
        else:
            await update.message.reply_text(t("login_fail", lang))
            return LOGGED_OUT # <--- Go back to logged out state
    except Exception as e:
        await update.message.reply_text(f"Server connection error: {e}")
        return LOGGED_OUT

# --- Main Menu Handlers ---
# These are the entry points for the sub-flows
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    text = update.message.text

    if text == t("btn_balance", lang):
        return await balance_command(update, context) # Or similar simple handler
    
    if text == t("btn_new_expense", lang):
        # Start the expense flow
        user_id = context.user_data.get('system_user_id')
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/groups")
        groups = response.json()
        if not groups:
            await update.message.reply_text(t("expense_no_groups", lang))
            return LOGGED_IN
        keyboard = [[InlineKeyboardButton(g['name'], callback_data=f"exp_group_{g['id']}")] for g in groups]
        await update.message.reply_text(t("expense_start", lang), reply_markup=InlineKeyboardMarkup(keyboard))
        return EXPENSE_SELECT_GROUP

    # ... Add similar entry points for other buttons like "My Groups" and "My Wallet"
    
    await update.message.reply_text("Please choose from the menu.")
    return LOGGED_IN

# --- Expense Sub-Flow Handlers ---
async def expense_await_group_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['expense_group_id'] = int(query.data.split('_')[2])
    await query.edit_message_text("What is the expense description?")
    return EXPENSE_GET_DESC

async def expense_await_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['expense_description'] = update.message.text
    await update.message.reply_text("What is the total amount?")
    return EXPENSE_GET_AMOUNT

# ... And so on for the rest of the expense flow handlers, each returning the next state
# and finally returning LOGGED_IN when the flow is complete or cancelled.

# --- Universal Cancel ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    # Clean up any temporary data from conversations
    for key in list(context.user_data.keys()):
        if key.startswith('expense_') or key.startswith('group_') or key.startswith('wallet_'):
            del context.user_data[key]
            
    await update.message.reply_text("Operation cancelled.")
    
    if context.user_data.get('is_logged_in'):
        await update.message.reply_text(t("main_menu_prompt", lang), reply_markup=get_main_menu_keyboard(lang))
        return LOGGED_IN
    else:
        await update.message.reply_text("You are logged out.", reply_markup=ReplyKeyboardRemove())
        return LOGGED_OUT