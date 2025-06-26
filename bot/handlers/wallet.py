# bot/handlers/wallet.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
import requests
from ..locales import t

API_BASE_URL = "http://127.0.0.1:8000"

# States for conversation
WALLET_GROUP_SELECT, WALLET_MENU, WALLET_DEPOSIT_AMOUNT, WALLET_WITHDRAW_AMOUNT, WALLET_WITHDRAW_PASSWORD = range(10, 15)

# --- Entry Point ---
async def my_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    user_id = context.user_data.get('system_user_id')
    if not user_id:
        await update.message.reply_text("Please /login first.")
        return ConversationHandler.END

    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/groups")
        if response.status_code == 200:
            groups = response.json()
            if not groups:
                await update.message.reply_text(t("expense_no_groups", lang))
                return ConversationHandler.END
            
            keyboard = [[InlineKeyboardButton(g['name'], callback_data=f"w_group_{g['id']}")] for g in groups]
            await update.message.reply_text(t("wallet_select_group", lang), reply_markup=InlineKeyboardMarkup(keyboard))
            return WALLET_GROUP_SELECT
        else:
            await update.message.reply_text(f"Error: {response.json().get('detail')}")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
        return ConversationHandler.END

# --- State Handlers ---
async def wallet_group_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    group_id = int(query.data.split('_')[2])
    context.user_data['wallet_flow'] = {'group_id': group_id}

    # Fetch wallet balance and display menu
    try:
        response = requests.get(f"{API_BASE_URL}/groups/{group_id}/wallet/balance")
        if response.status_code == 200:
            balance_data = response.json()
            user_balance = next((item['balance'] for item in balance_data['member_balances'] if item['user']['id'] == context.user_data['system_user_id']), 0)
            
            context.user_data['wallet_flow']['group_name'] = "Group" # Simplified, get real name
            context.user_data['wallet_flow']['user_balance'] = user_balance
            
            header = t("wallet_menu_header", lang, group_name=context.user_data['wallet_flow']['group_name'])
            balance_info = t("wallet_balance_info", lang, total=balance_data['total_wallet_balance'], user_balance=user_balance)
            
            keyboard = [
                [InlineKeyboardButton(t("btn_deposit", lang), callback_data="wallet_deposit")],
                [InlineKeyboardButton(t("btn_withdraw", lang), callback_data="wallet_withdraw")],
                [InlineKeyboardButton(t("btn_settle_debts", lang), callback_data="wallet_settle")],
                [InlineKeyboardButton(t("btn_back_to_groups", lang), callback_data="wallet_back")],
            ]
            await query.edit_message_text(f"{header}\n{balance_info}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return WALLET_MENU
        else:
            await query.edit_message_text(f"Error: {response.json().get('detail')}")
            return ConversationHandler.END
    except Exception as e:
        await query.edit_message_text(f"Error connecting to server: {e}")
        return ConversationHandler.END

async def wallet_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    if query.data == "wallet_deposit":
        await query.edit_message_text(t("ask_deposit_amount", lang))
        return WALLET_DEPOSIT_AMOUNT
    elif query.data == "wallet_withdraw":
        max_amount = context.user_data['wallet_flow']['user_balance']
        await query.edit_message_text(t("ask_withdraw_amount", lang, max_amount=max_amount))
        return WALLET_WITHDRAW_AMOUNT
    elif query.data == "wallet_settle":
        # Placeholder for settlement logic
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Settlement feature is under construction.")
        return WALLET_MENU
    elif query.data == "wallet_back":
        # This should ideally go back to the groups menu, for now we end
        await query.edit_message_text("Exited wallet menu.")
        return ConversationHandler.END

async def received_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    try:
        amount = float(update.message.text)
        payload = {
            "user_id": context.user_data['system_user_id'],
            "amount": amount,
            "description": "Deposit via Telegram Bot"
        }
        group_id = context.user_data['wallet_flow']['group_id']
        response = requests.post(f"{API_BASE_URL}/groups/{group_id}/wallet/deposit", json=payload)
        
        if response.status_code == 202:
            await update.message.reply_text(t("deposit_submitted", lang))
        else:
            await update.message.reply_text(f"Error: {response.json().get('detail')}")

    except ValueError:
        await update.message.reply_text(t("expense_invalid_amount", lang))
        return WALLET_DEPOSIT_AMOUNT # Ask again
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")

    return ConversationHandler.END

# Add other handlers for withdrawal etc.