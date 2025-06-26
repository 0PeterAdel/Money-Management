# bot/handlers/voting.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import requests
from ..locales import t

API_BASE_URL = "http://127.0.0.1:8000"

async def my_votes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    user_id = context.user_data.get('system_user_id')
    if not user_id:
        await update.message.reply_text("Please /login first.")
        return

    try:
        response = requests.get(f"{API_BASE_URL}/actions/pending?user_id={user_id}")
        if response.status_code != 200:
            await update.message.reply_text(f"Error fetching data: {response.json().get('detail')}")
            return
        
        pending_actions = response.json()
        if not pending_actions:
            await update.message.reply_text(t("no_pending_votes", lang))
            return

        await update.message.reply_text(t("my_votes_header", lang), parse_mode="Markdown")
        for action in pending_actions:
            details = action.get('details', {})
            action_id = action.get('id')
            action_type = action.get('action_type')
            initiator_name = action.get('initiator', {}).get('name', 'Someone')
            
            text = ""
            if action_type == "EXPENSE":
                text = (
                    f"🔔 *Expense Request* (#{action_id})\n"
                    f"`{initiator_name}` logged: `{details.get('description')}` for `{details.get('total_amount')}`"
                )
            elif action_type == "WALLET_DEPOSIT":
                 text = (
                    f"💰 *Deposit Request* (#{action_id})\n"
                    f"`{initiator_name}` deposited `{details.get('amount')}`"
                )

            keyboard = [[
                InlineKeyboardButton(t("confirm", lang), callback_data=f"vote_approve_{action_id}_{user_id}"),
                InlineKeyboardButton(t("cancel", lang), callback_data=f"vote_reject_{action_id}_{user_id}"),
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")
