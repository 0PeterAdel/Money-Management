# bot/handlers/wallet.py - FULLY IMPLEMENTED

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
import requests
from ..locales import t

API_BASE_URL = "http://127.0.0.1:8000"

# States for conversation
(
    WALLET_GROUP_SELECT,
    WALLET_MENU,
    WALLET_DEPOSIT_AMOUNT,
    WALLET_WITHDRAW_AMOUNT,
    WALLET_WITHDRAW_PASSWORD,
    WALLET_SETTLE_CONFIRM,
) = range(30, 36) # Using a new range to avoid conflicts


# --- Entry Point ---
async def my_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    user_id = context.user_data.get('system_user_id')
    if not user_id:
        await update.message.reply_text("Please /login first.")
        return ConversationHandler.END

    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/groups")
        response.raise_for_status()
        groups = response.json()
        if not groups:
            await update.message.reply_text(t("expense_no_groups", lang))
            return ConversationHandler.END
        
        keyboard = [[InlineKeyboardButton(g['name'], callback_data=f"w_group_{g['id']}")] for g in groups]
        await update.message.reply_text(t("wallet_select_group", lang), reply_markup=InlineKeyboardMarkup(keyboard))
        return WALLET_GROUP_SELECT
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
        return ConversationHandler.END

# --- State Handlers ---
async def wallet_group_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    group_id = int(query.data.split('_')[2])
    context.user_data['wallet_flow'] = {'group_id': group_id}

    try:
        response = requests.get(f"{API_BASE_URL}/groups/{group_id}/wallet/balance")
        response.raise_for_status()
        balance_data = response.json()
        
        # Get group name - inefficient, but works for now. Better to have group name in balance response.
        group_response = requests.get(f"{API_BASE_URL}/groups")
        group_name = next((g['name'] for g in group_response.json() if g['id'] == group_id), "Group")
        context.user_data['wallet_flow']['group_name'] = group_name

        user_balance = next((item['balance'] for item in balance_data['member_balances'] if item['user']['id'] == context.user_data['system_user_id']), 0)
        context.user_data['wallet_flow']['user_balance'] = user_balance
        
        header = t("wallet_menu_header", lang, group_name=group_name)
        balance_info = t("wallet_balance_info", lang, total=balance_data['total_wallet_balance'], user_balance=user_balance)
        
        keyboard = [
            [InlineKeyboardButton(t("btn_deposit", lang), callback_data="wallet_action_deposit")],
            [InlineKeyboardButton(t("btn_withdraw", lang), callback_data="wallet_action_withdraw")],
            [InlineKeyboardButton(t("btn_settle_debts", lang), callback_data="wallet_action_settle")],
            [InlineKeyboardButton(t("btn_back_to_main", lang), callback_data="wallet_action_back")],
        ]
        await query.edit_message_text(f"{header}\n{balance_info}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return WALLET_MENU
    except requests.exceptions.RequestException as e:
        await query.edit_message_text(f"Error: {e.response.json().get('detail') if e.response else e}")
        return ConversationHandler.END

async def wallet_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    action = query.data.split('_')[2]

    if action == "deposit":
        await query.edit_message_text(t("ask_deposit_amount", lang))
        return WALLET_DEPOSIT_AMOUNT
    elif action == "withdraw":
        max_amount = context.user_data['wallet_flow']['user_balance']
        await query.edit_message_text(t("ask_withdraw_amount", lang, max_amount=max_amount))
        return WALLET_WITHDRAW_AMOUNT
    elif action == "settle":
        keyboard = [[
            InlineKeyboardButton(t("confirm", lang), callback_data="settle_confirm_yes"),
            InlineKeyboardButton(t("cancel", lang), callback_data="settle_confirm_no")
        ]]
        await query.edit_message_text(t("settle_debts_confirm", lang), reply_markup=InlineKeyboardMarkup(keyboard))
        return WALLET_SETTLE_CONFIRM
    elif action == "back":
        from .registration import get_main_menu_keyboard
        await query.edit_message_text(t("main_menu_prompt", lang), reply_markup=get_main_menu_keyboard(lang))
        del context.user_data['wallet_flow']
        return ConversationHandler.END

async def received_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    try:
        amount = float(update.message.text)
        payload = {"user_id": context.user_data['system_user_id'], "amount": amount}
        group_id = context.user_data['wallet_flow']['group_id']
        response = requests.post(f"{API_BASE_URL}/groups/{group_id}/wallet/deposit", json=payload)
        response.raise_for_status()
        await update.message.reply_text(t("deposit_submitted", lang))
    except ValueError:
        await update.message.reply_text(t("expense_invalid_amount", lang))
        return WALLET_DEPOSIT_AMOUNT
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error: {e.response.json().get('detail') if e.response else e}")
    
    del context.user_data['wallet_flow']
    return ConversationHandler.END

async def received_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    try:
        amount = float(update.message.text)
        context.user_data['wallet_flow']['withdraw_amount'] = amount
        await update.message.reply_text(t("ask_withdraw_password", lang))
        return WALLET_WITHDRAW_PASSWORD
    except ValueError:
        await update.message.reply_text(t("expense_invalid_amount", lang))
        return WALLET_WITHDRAW_AMOUNT

async def received_withdraw_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    password = update.message.text
    
    payload = {
        "user_id": context.user_data['system_user_id'],
        "amount": context.user_data['wallet_flow']['withdraw_amount'],
        "password": password
    }
    group_id = context.user_data['wallet_flow']['group_id']
    
    try:
        response = requests.post(f"{API_BASE_URL}/groups/{group_id}/wallet/withdraw", json=payload)
        response.raise_for_status()
        await update.message.reply_text(t("withdrawal_success", lang))
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error: {e.response.json().get('detail') if e.response else e}")
        
    del context.user_data['wallet_flow']
    return ConversationHandler.END

async def wallet_settle_debts_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')

    if query.data == "settle_confirm_yes":
        group_id = context.user_data['wallet_flow']['group_id']
        payload = {"user_id": None} # Settle for all users
        try:
            response = requests.post(f"{API_BASE_URL}/groups/{group_id}/wallet/settle-debts", json=payload)
            response.raise_for_status()
            summary = response.json()
            # You can format the summary here, for now just a simple message
            await query.edit_message_text(f"Settlement process initiated! Results:\n{summary['message']}")
        except requests.exceptions.RequestException as e:
            await query.edit_message_text(f"Error: {e.response.json().get('detail') if e.response else e}")
    else: # Cancelled
        await query.edit_message_text("Settlement cancelled.")

    del context.user_data['wallet_flow']
    return ConversationHandler.END