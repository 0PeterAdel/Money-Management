"""
Push notification API endpoints (Telegram)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import telegram
import asyncio
from app.core.config import settings

router = APIRouter()


class PushRequest(BaseModel):
    """Push notification request schema"""
    chat_id: str
    message: str


@router.post("/send-push")
async def send_push_endpoint(push_request: PushRequest):
    """Send a push notification via Telegram"""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Telegram bot is not configured"
        )
    
    try:
        bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=push_request.chat_id,
            text=push_request.message,
            parse_mode='Markdown'
        )
        
        return {
            "message": "Push notification sent successfully",
            "chat_id": push_request.chat_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send push notification: {str(e)}"
        )
