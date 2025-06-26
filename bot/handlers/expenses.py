# bot/handlers/expenses.py - FIXED & UPDATED

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
import requests
from ..locales import t

API_BASE_URL = "http://127.0.0.1:8000"

# States for the conversation, starting from 6 to avoid conflicts with other handlers
SELECT_GROUP, GET_DESCRIPTION, GET_AMOUNT, SELECT_CATEGORY, SELECT_PARTICIPANTS, CONFIRM_EXPENSE = range(6, 12)

async def new_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    user_id = context.user_data.get('system_user_id')
    if not user_id:
        await update.message.reply_text("Please /login first.")
        return ConversationHandler.END

    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/groups")
        response.raise_for_status() # Raise an exception for bad status codes
        groups = response.json()
        if not groups:
            await update.message.reply_text(t("expense_no_groups", lang))
            return ConversationHandler.END
        
        # FIXED: Callback data now matches the pattern expected by bot_main.py
        keyboard = [[InlineKeyboardButton(g['name'], callback_data=f"exp_group_{g['id']}")] for g in groups]
        await update.message.reply_text(t("expense_start", lang), reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_GROUP
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
        return ConversationHandler.END

# FIXED: Renamed this function to match the import in bot_main.py
async def group_selected_for_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    group_id = int(query.data.split('_')[2])
    # Fetch all groups to get details. In a larger app, a specific /groups/{id} endpoint would be better.
    response = requests.get(f"{API_BASE_URL}/users/{context.user_data['system_user_id']}/groups")
    group = next((g for g in response.json() if g['id'] == group_id), None)

    if not group:
        await query.edit_message_text("Error: Group not found.")
        return ConversationHandler.END

    context.user_data['expense_flow'] = {
        'group_id': group_id,
        'group_name': group['name'],
        'members': group['members']
    }
    
    lang = context.user_data.get('lang', 'en')
    await query.edit_message_text(text=t("expense_ask_desc", lang))
    return GET_DESCRIPTION

async def received_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['expense_flow']['description'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("expense_ask_amount", lang))
    return GET_AMOUNT

async def received_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    try:
        amount = float(update.message.text)
        context.user_data['expense_flow']['amount'] = amount
        
        response = requests.get(f"{API_BASE_URL}/categories")
        response.raise_for_status()
        categories = response.json()
        keyboard = [[InlineKeyboardButton(c['name'], callback_data=f"cat_{c['name']}")] for c in categories]
        await update.message.reply_text(t("expense_ask_category", lang), reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_CATEGORY
    except ValueError:
        await update.message.reply_text(t("expense_invalid_amount", lang))
        return GET_AMOUNT
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
        return ConversationHandler.END

# FIXED: Renamed for clarity and consistency
async def category_selected_for_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    category_name = query.data.split('_', 1)[1]
    context.user_data['expense_flow']['category'] = category_name
    
    user_id = context.user_data['system_user_id']
    context.user_data['expense_flow']['participants'] = {user_id}
    
    members = context.user_data['expense_flow']['members']
    participants = context.user_data['expense_flow']['participants']
    keyboard = []
    for member in members:
        status_icon = "✅" if member['id'] in participants else "🔲"
        keyboard.append([InlineKeyboardButton(f"{status_icon} {member['name']}", callback_data=f"part_{member['id']}")])
    keyboard.append([InlineKeyboardButton(t("done_selecting", lang), callback_data="part_done")])
    
    # Send a new message for participant selection instead of editing the previous one
    await query.edit_message_text(text=f"Category set to: {category_name}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t("expense_ask_participants", lang),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return SELECT_PARTICIPANTS

# FIXED: Renamed for clarity and consistency
async def participant_selected_for_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    data = query.data
    
    if data == "part_done":
        expense_data = context.user_data['expense_flow']
        participants_set = expense_data['participants']
        member_map = {m['id']: m['name'] for m in expense_data['members']}
        participant_names = ", ".join([member_map.get(pid, 'Unknown') for pid in participants_set])
        
        summary_text = t("expense_summary_header", lang) + t("expense_summary_body", lang, 
            group_name=expense_data['group_name'],
            description=expense_data['description'],
            amount=expense_data['amount'],
            category=expense_data['category'],
            participants=participant_names
        )
        
        # FIXED: Callback data now matches the pattern expected by bot_main.py
        keyboard = [[
            InlineKeyboardButton(t("confirm", lang), callback_data="exp_confirm_yes"),
            InlineKeyboardButton(t("cancel", lang), callback_data="exp_confirm_no")
        ]]
        await query.edit_message_text(text=summary_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return CONFIRM_EXPENSE

    participant_id = int(data.split('_')[1])
    participants = context.user_data['expense_flow']['participants']
    if participant_id in participants:
        # Prevent the user from un-selecting themselves
        if participant_id != context.user_data['system_user_id']:
            participants.remove(participant_id)
    else:
        participants.add(participant_id)
    
    members = context.user_data['expense_flow']['members']
    keyboard = []
    for member in members:
        status_icon = "✅" if member['id'] in participants else "🔲"
        keyboard.append([InlineKeyboardButton(f"{status_icon} {member['name']}", callback_data=f"part_{member['id']}")])
    keyboard.append([InlineKeyboardButton(t("done_selecting", lang), callback_data="part_done")])
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_PARTICIPANTS

async def expense_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    if query.data == "exp_confirm_yes":
        expense_data = context.user_data['expense_flow']
        payload = {
            "description": expense_data['description'],
            "total_amount": expense_data['amount'],
            "group_id": expense_data['group_id'],
            "participant_ids": list(expense_data['participants']),
            "category_name": expense_data['category'],
            "paid_by_user_id": context.user_data['system_user_id']
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/expenses", json=payload)
            response.raise_for_status()
            await query.edit_message_text(t("expense_request_sent", lang))
        except requests.exceptions.RequestException as e:
            error_detail = e.response.json().get('detail') if e.response else str(e)
            await query.edit_message_text(f"Error: {error_detail}")
            
    else: # Cancelled
        await query.edit_message_text("Expense creation cancelled.")

    if 'expense_flow' in context.user_data:
        del context.user_data['expense_flow']
    return ConversationHandler.END