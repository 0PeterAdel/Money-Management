# bot/handlers/groups.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
import requests
from ..locales import t

API_BASE_URL = "http://127.0.0.1:8000"

# States for conversation
GROUP_MENU, GROUP_CREATE_NAME, GROUP_CREATE_DESC, GROUP_VIEW = range(4)

# --- Helper Functions ---
async def get_groups_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches user's groups and displays them as a menu."""
    lang = context.user_data.get('lang', 'en')
    user_id = context.user_data.get('system_user_id')
    
    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/groups")
        if response.status_code == 200:
            groups = response.json()
            keyboard = [[InlineKeyboardButton(g['name'], callback_data=f"group_view_{g['id']}")] for g in groups]
            keyboard.append([InlineKeyboardButton(t("btn_create_group", lang), callback_data="group_create_new")])
            
            message_text = t("groups_select_prompt", lang)
            # If called from a button press (query), edit the message. If from a command, send new.
            if update.callback_query:
                await update.callback_query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await update.message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(f"Error fetching groups: {response.json().get('detail')}")
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
    return GROUP_MENU

# --- Conversation Entry Point ---
async def my_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('is_logged_in'):
        await update.message.reply_text("Please /login first.")
        return ConversationHandler.END
    return await get_groups_menu(update, context)

# --- State Handlers ---
async def group_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "group_create_new":
        lang = context.user_data.get('lang', 'en')
        await query.edit_message_text(t("create_group_ask_name", lang))
        return GROUP_CREATE_NAME
    else: # A specific group was selected
        group_id = int(query.data.split('_')[2])
        context.user_data['current_group_id'] = group_id
        
        # In a real app, you'd fetch the single group details here
        # For now, we'll just show a placeholder menu
        lang = context.user_data.get('lang', 'en')
        keyboard = [
            [InlineKeyboardButton(t("btn_add_member", lang), callback_data="group_action_add")],
            [InlineKeyboardButton(t("btn_view_wallet", lang), callback_data="group_action_wallet")],
            [InlineKeyboardButton(t("btn_back_to_groups", lang), callback_data="group_action_back")],
        ]
        await query.edit_message_text("Selected Group Menu (WIP)", reply_markup=InlineKeyboardMarkup(keyboard))
        return GROUP_VIEW

async def received_group_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_group_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("create_group_ask_desc", lang, group_name=update.message.text))
    return GROUP_CREATE_DESC

async def received_group_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    group_name = context.user_data['new_group_name']
    lang = context.user_data.get('lang', 'en')
    
    payload = {"name": group_name, "description": description}
    response = requests.post(f"{API_BASE_URL}/groups", json=payload)
    
    if response.status_code == 201:
        await update.message.reply_text(t("group_created_success", lang, group_name=group_name))
    else:
        await update.message.reply_text(f"Error: {response.json().get('detail')}")
        
    del context.user_data['new_group_name']
    # Go back to the main groups menu
    return await get_groups_menu(update, context)
    
async def group_view_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "group_action_back":
        return await get_groups_menu(update, context)
    else:
        # Placeholder for other actions like Add Member, View Wallet, etc.
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This action is under construction.")
        return GROUP_VIEW