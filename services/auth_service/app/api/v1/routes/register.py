"""
User registration endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.user import UserCreate, User as UserSchema
from app.core.security import get_password_hash

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    db_user = db.query(User).filter(User.name == user.name).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        name=user.name,
        hashed_password=hashed_password,
        telegram_id=user.telegram_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user
