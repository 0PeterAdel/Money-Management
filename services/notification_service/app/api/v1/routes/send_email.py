"""
Email sending API endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from app.workers.email_worker import send_email

router = APIRouter()


class EmailRequest(BaseModel):
    """Email request schema"""
    to: EmailStr
    subject: str
    body: str


@router.post("/send-email")
async def send_email_endpoint(email_request: EmailRequest):
    """Send an email notification"""
    # Queue the email task
    task = send_email.delay(
        to=email_request.to,
        subject=email_request.subject,
        body=email_request.body
    )
    
    return {
        "message": "Email queued for sending",
        "task_id": task.id
    }
