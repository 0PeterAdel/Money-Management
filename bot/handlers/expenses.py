# bot/handlers/expenses.py

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
import requests
from ..locales import t

# This file will handle the new expense conversation flow.
# We will build this out in the next steps. For now, it's a placeholder.

async def new_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if not context.user_data.get('is_logged_in'):
        await update.message.reply_text("Please /login first.")
        return ConversationHandler.END

    # TODO: Start the conversation to add a new expense
    # For now, just a placeholder message.
    await update.message.reply_text(f"Okay, let's add a new expense. This feature is coming soon!")
    
    return ConversationHandler.END