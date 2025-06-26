# bot/handlers/settings.py
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from .registration import set_language # Reuse the language function

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for the settings menu. For now, it just goes to language selection."""
    return await set_language(update, context)