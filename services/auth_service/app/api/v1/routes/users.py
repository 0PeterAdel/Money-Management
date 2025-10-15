"""
User management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List
import math

from app.db.session import get_db
from app.db.models.user import User, Group
from app.schemas.user import User as UserSchema, Group as GroupSchema, GroupCreate, MessageResponse

router = APIRouter()


@router.get("/users", response_model=List[UserSchema])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of users"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/users/by-name/{username}", response_model=UserSchema)
def get_user_by_name(username: str, db: Session = Depends(get_db)):
    """Get user by username"""
    user = db.query(User).filter(
        func.lower(User.name) == username.lower()
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user (with validation)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Note: In a microservices architecture, you'd need to check with other services
    # for outstanding debts, wallet balances, etc. via API calls
    # For now, we'll do a simple deletion
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User '{user.name}' has been deleted."}


# Group endpoints
@router.post("/groups", response_model=GroupSchema, status_code=status.HTTP_201_CREATED)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    """Create a new group"""
    new_group = Group(**group.dict())
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


@router.get("/groups", response_model=List[GroupSchema])
def get_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of groups"""
    groups = db.query(Group).offset(skip).limit(limit).all()
    return groups


@router.get("/users/{user_id}/groups", response_model=List[GroupSchema])
def get_user_groups(user_id: int, db: Session = Depends(get_db)):
    """Get groups for a specific user"""
    user = db.query(User).options(
        joinedload(User.groups).joinedload(Group.members)
    ).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.groups


@router.post("/groups/{group_id}/add_member/{user_id}", response_model=GroupSchema)
def add_member_to_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Add a member to a group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user in group.members:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    group.members.append(user)
    db.commit()
    db.refresh(group)
    
    return group


@router.delete("/groups/{group_id}/remove_member/{user_id}", response_model=MessageResponse)
def remove_member_from_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Remove a member from a group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user not in group.members:
        raise HTTPException(
            status_code=404,
            detail="User is not a member of this group"
        )
    
    # Note: In production, you'd check with expense service for outstanding debts
    
    group.members.remove(user)
    db.commit()
    
    return {"message": f"User '{user.name}' removed from group '{group.name}'."}
