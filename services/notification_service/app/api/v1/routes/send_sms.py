"""
SMS sending API endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.workers.sms_worker import send_sms

router = APIRouter()


class SMSRequest(BaseModel):
    """SMS request schema"""
    to: str
    message: str


@router.post("/send-sms")
async def send_sms_endpoint(sms_request: SMSRequest):
    """Send an SMS notification"""
    # Queue the SMS task
    task = send_sms.delay(
        to=sms_request.to,
        message=sms_request.message
    )
    
    return {
        "message": "SMS queued for sending",
        "task_id": task.id
    }
