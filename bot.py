# bot.py - Final Corrected Version

import logging
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"
POLLING_INTERVAL = 20 # Check for new votes every 20 seconds

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Function ---
async def send_vote_notification(context: ContextTypes.DEFAULT_TYPE, user_id: str, telegram_id: str, action: dict):
    details = action.get('details', {})
    action_id = action.get('id')
    action_type = action.get('action_type')
    initiator_name = action.get('initiator', {}).get('name', 'Someone')
    
    text = ""
    if action_type == "EXPENSE":
        text = (
            f"🔔 <b>New Expense Request (#{action_id})</b>\n\n"
            f"<code>{initiator_name}</code> wants to log an expense:\n"
            f"- <b>Description:</b> {details.get('description')}\n"
            f"- <b>Amount:</b> {details.get('total_amount')}\n"
            f"- <b>Category:</b> {details.get('category_name')}"
        )
    elif action_type == "WALLET_DEPOSIT":
         text = (
            f"💰 <b>New Deposit Request (#{action_id})</b>\n\n"
            f"<code>{initiator_name}</code> claims to have deposited "
            f"<b>{details.get('amount')}</b> into the group wallet.\n"
        )

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"vote_approve_{action_id}_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"vote_reject_{action_id}_{user_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(chat_id=telegram_id, text=text, reply_markup=reply_markup, parse_mode='HTML')
        # Mark as notified to avoid sending again
        context.bot_data.setdefault('notified_actions', set()).add(action_id)
    except Exception as e:
        logger.error(f"Failed to send notification for action {action_id} to {telegram_id}: {e}")

# --- Background Job ---
async def poll_for_pending_actions(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Polling for pending actions...")
    try:
        users_response = requests.get(f"{API_BASE_URL}/users")
        if users_response.status_code != 200:
            logger.error("Could not fetch users from API.")
            return
            
        users = users_response.json()
        # **FIXED**: Using context.bot_data to store state
        notified_actions = context.bot_data.setdefault('notified_actions', set())

        for user in users:
            user_id = user.get('id')
            telegram_id = user.get('telegram_id')
            if not telegram_id:
                continue

            actions_response = requests.get(f"{API_BASE_URL}/actions/pending?user_id={user_id}")
            if actions_response.status_code == 200:
                pending_actions = actions_response.json()
                for action in pending_actions:
                    action_id = action.get('id')
                    if action_id not in notified_actions:
                        logger.info(f"Found new action {action_id} for user {user_id}. Notifying...")
                        await send_vote_notification(context, str(user_id), telegram_id, action)
            else:
                logger.warning(f"Failed to fetch pending actions for user {user_id}")

    except Exception as e:
        logger.error(f"Error in polling job: {e}")

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    # **FIXED**: Using HTML tags (<b> and <code>) instead of markdown characters
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Welcome. Please register your account using:"
        rf"\n<code>/register &lt;your_username&gt; &lt;your_password&gt;</code>"
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = str(update.effective_user.id)
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: `/register <username> <password>`")
        return
        
    username, password = args
    payload = {"username": username, "password": password, "telegram_id": telegram_id}
    
    try:
        response = requests.post(f"{API_BASE_URL}/users/link-telegram", json=payload)
        if response.status_code == 200:
            await update.message.reply_text("✅ Success! Your Telegram account is now linked.")
        else:
            await update.message.reply_text(f"❌ Error: {response.json().get('detail', 'Could not link account.')}")
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        await update.message.reply_text("An error occurred while communicating with the server.")

# --- Callback Handler for Buttons ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        _, approval_str, action_id_str, voter_id_str = query.data.split('_')
        payload = {"voter_id": int(voter_id_str), "approve": (approval_str == "approve")}
        response = requests.post(f"{API_BASE_URL}/actions/{action_id_str}/vote", json=payload)
        if response.status_code == 200:
            final_status = response.json().get('status')
            await query.edit_message_text(text=f"Thank you for your vote! Final status of action #{action_id_str}: <b>{final_status}</b>", parse_mode='HTML')
        else:
            await query.edit_message_text(text=f"Error: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Error processing button callback: {e}")
        await query.edit_message_text(text="An error occurred.")

def main() -> None:
    """Start the bot and the background polling job."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CallbackQueryHandler(button_callback, pattern=r'^vote_'))

    # Add the background job
    job_queue = application.job_queue
    job_queue.run_repeating(poll_for_pending_actions, interval=POLLING_INTERVAL, first=5)

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()