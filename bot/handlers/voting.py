# bot/handlers/voting.py - FULLY IMPLEMENTED

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import requests
import json
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
            # Format date nicely
            date_str = action.get('created_at', '').split('T')[0]
            
            text = ""
            if action_type == "EXPENSE":
                text = (f"🔔 *Expense Request* (#{action_id})\n"
                        f"{t('vote_exp_details', lang, desc=details.get('description'), amount=details.get('total_amount'), category=details.get('category_name'), initiator=initiator_name, date=date_str)}")
            elif action_type == "WALLET_DEPOSIT":
                 text = (f"💰 *Deposit Request* (#{action_id})\n"
                        f"{t('vote_dep_details', lang, desc=details.get('description', 'Deposit'), amount=details.get('amount'), initiator=initiator_name, date=date_str)}")

            keyboard = [[
                InlineKeyboardButton(t("confirm", lang), callback_data=f"vote_approve_{action_id}_{user_id}"),
                InlineKeyboardButton(t("cancel", lang), callback_data=f"vote_reject_{action_id}_{user_id}"),
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")

# --- NEW: The missing callback handler for vote buttons ---
async def vote_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the vote from the button and sends it to the backend."""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    try:
        _, approval_str, action_id_str, voter_id_str = query.data.split('_')
        payload = {"voter_id": int(voter_id_str), "approve": (approval_str == "approve")}
        response = requests.post(f"{API_BASE_URL}/actions/{action_id_str}/vote", json=payload)
        
        if response.status_code == 200:
            final_status = response.json().get('status')
            await query.edit_message_text(text=f"Thank you for your vote! ✅\nFinal status of action #{action_id_str}: *{final_status}*", parse_mode='Markdown')
        else:
            await query.edit_message_text(text=f"Error: {response.json().get('detail', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Error processing button callback: {e}")
        await query.edit_message_text(text="An error occurred.")
