"""
SMS notification worker (Celery task)
"""
from app.core.celery_config import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="send_sms")
def send_sms(to: str, message: str):
    """
    Send an SMS notification
    
    Args:
        to: Recipient phone number
        message: SMS message
    """
    try:
        # TODO: Implement actual SMS sending using Twilio or other SMS service
        logger.info(f"Sending SMS to {to}: {message}")
        
        # Placeholder for actual SMS sending logic
        # from twilio.rest import Client
        # ... SMS sending code ...
        
        return {"status": "sent", "to": to}
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        raise
