# bot.py
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    # You can add logic here to register the user's telegram_id to their account in your database
    # For example, by asking for their username/password and calling a backend endpoint.
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Welcome to the Finance Bot.",
    )

async def check_votes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays pending actions for the user to vote on."""
    telegram_id = update.effective_user.id
    
    # First, find the user_id in our system from their telegram_id
    try:
        # We need an endpoint in our FastAPI to do this lookup. Let's assume we create one.
        # For now, let's pretend we have the user_id. A real implementation needs this lookup.
        # This is a simplification. In a real app, you would have a /users/by-telegram/{telegram_id} endpoint.
        # For this example, we will ask the user for their ID.
        if not context.args:
            await update.message.reply_text("Please provide your system User ID. Usage: /votes <your_user_id>")
            return
            
        user_id = context.args[0]
        
        response = requests.get(f"{API_BASE_URL}/actions/pending?user_id={user_id}")
        
        if response.status_code != 200:
            await update.message.reply_text(f"Error fetching data from the server: {response.text}")
            return

        pending_actions = response.json()

        if not pending_actions:
            await update.message.reply_text("You have no pending actions to vote on. ✅")
            return

        await update.message.reply_text("You have the following pending requests:")
        for action in pending_actions:
            details = action.get('details', {})
            action_id = action.get('id')
            action_type = action.get('action_type')
            initiator_name = action.get('initiator', {}).get('name', 'Someone')
            
            text = ""
            if action_type == "EXPENSE":
                text = (
                    f"🔔 *New Expense Request* (#{action_id})\n\n"
                    f"`{initiator_name}` wants to log an expense:\n"
                    f"- *Description:* {details.get('description')}\n"
                    f"- *Amount:* {details.get('total_amount')}\n"
                )
            elif action_type == "WALLET_DEPOSIT":
                 text = (
                    f"💰 *New Deposit Request* (#{action_id})\n\n"
                    f"`{initiator_name}` claims to have deposited "
                    f"*{details.get('amount')}* into the group wallet.\n"
                )

            # Create the buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm", callback_data=f"vote_approve_{action_id}_{user_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"vote_reject_{action_id}_{user_id}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in /votes command: {e}")
        await update.message.reply_text("An error occurred while fetching your pending votes.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and sends the vote to the backend."""
    query = update.callback_query
    await query.answer() # Acknowledge the button press

    # Data is in the format "vote_approve_{action_id}_{voter_id}" or "vote_reject_{action_id}_{voter_id}"
    try:
        vote_type, approval_str, action_id_str, voter_id_str = query.data.split('_')
        
        action_id = int(action_id_str)
        voter_id = int(voter_id_str)
        approve = approval_str == "approve"

        # Now, send this vote to our FastAPI backend
        payload = {"voter_id": voter_id, "approve": approve}
        response = requests.post(f"{API_BASE_URL}/actions/{action_id}/vote", json=payload)
        
        if response.status_code == 200:
            final_status = response.json().get('status')
            await query.edit_message_text(text=f"Thank you for your vote! Your vote has been registered.\nFinal status of action #{action_id}: *{final_status}*.", parse_mode='Markdown')
        else:
            await query.edit_message_text(text=f"Error submitting your vote: {response.json().get('detail', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Error processing button callback: {e}")
        await query.edit_message_text(text="An error occurred.")


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured! Please set it in your .env file.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("votes", check_votes))

    # on button clicks, handle the callback
    application.add_handler(CallbackQueryHandler(button_callback, pattern=r'^vote_'))

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
