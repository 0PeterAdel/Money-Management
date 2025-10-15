"""
User login and authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.user import LinkTelegramRequest, User as UserSchema
from app.core.security import verify_password

router = APIRouter()


@router.post("/link-telegram", response_model=UserSchema)
def link_telegram_account(
    link_request: LinkTelegramRequest,
    db: Session = Depends(get_db)
):
    """Link a Telegram account to an existing user"""
    # Find user
    user = db.query(User).filter(User.name == link_request.username).first()
    
    if not user or not verify_password(link_request.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Check if telegram_id is already linked
    existing_link = db.query(User).filter(
        User.telegram_id == link_request.telegram_id
    ).first()
    
    if existing_link and existing_link.id != user.id:
        raise HTTPException(
            status_code=400,
            detail="This Telegram account is already linked to another user."
        )
    
    # Link telegram account
    user.telegram_id = link_request.telegram_id
    db.commit()
    db.refresh(user)
    
    return user
