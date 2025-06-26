# bot/handlers/info.py
from telegram import Update
from telegram.ext import ContextTypes
import requests
from ..locales import t

API_BASE_URL = "http://127.0.0.1:8000"

async def balance_summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('is_logged_in'):
        await update.message.reply_text("Please /login first.")
        return

    lang = context.user_data.get('lang', 'en')
    user_id = context.user_data.get('system_user_id')

    try:
        response = requests.get(f"{API_BASE_URL}/balance-summary")
        if response.status_code == 200:
            summary = response.json()
            if not summary:
                await update.message.reply_text(t("no_debts", lang))
                return

            message = f"{t('balance_header', lang)}\n\n"
            for item in summary:
                debtor_name = item['debtor']['name']
                creditor_name = item['creditor']['name']
                amount = item['amount']
                
                if item['debtor']['id'] == user_id:
                    message += f"• {t('you_owe', lang)} *{creditor_name}* `{amount}` EGP\n"
                elif item['creditor']['id'] == user_id:
                     message += f"• *{debtor_name}* {t('owes_you', lang)} `{amount}` EGP\n"

            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"Error: {response.json().get('detail')}")
    except Exception as e:
        await update.message.reply_text(f"Error connecting to server: {e}")