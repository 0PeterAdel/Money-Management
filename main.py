from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from . import models, database
from .database import SessionLocal, engine
from pydantic import BaseModel

# --- Create database tables ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================
# DTOs (Pydantic Models for Request/Response)
# =================================================================

# --- User Models ---
class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

# --- Group Models ---
class GroupBase(BaseModel):
    name: str
    description: str | None = None

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    members: List[User] = []

    class Config:
        orm_mode = True

# --- Expense Models ---
class ExpenseCreate(BaseModel):
    description: str
    total_amount: float
    paid_by_user_id: int
    group_id: int
    participant_ids: List[int]  # IDs of users participating in this expense

class Expense(BaseModel):
    id: int
    description: str
    total_amount: float

    class Config:
        orm_mode = True

# =================================================================
# API Endpoints
# =================================================================

@app.get("/")
def read_root():
    return {"message": "Welcome to the Finance Assistant System"}

# --- Users Endpoints ---
@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.name == user.name).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = models.User(name=user.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# --- Groups Endpoints ---
@app.post("/groups/", response_model=Group, status_code=status.HTTP_201_CREATED)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    new_group = models.Group(**group.dict())
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group

@app.post("/groups/{group_id}/add_member/{user_id}", response_model=Group)
def add_member_to_group(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user in group.members:
        raise HTTPException(status_code=400, detail="User is already a member of the group")

    group.members.append(user)
    db.commit()
    db.refresh(group)
    return group

# --- Expenses Endpoint ---
@app.post("/expenses/", response_model=Expense, status_code=status.HTTP_201_CREATED)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    # Step 1: Validate payer existence
    payer = db.query(models.User).filter(models.User.id == expense.paid_by_user_id).first()
    if not payer:
        raise HTTPException(
            status_code=404,
            detail=f"Payer user (ID: {expense.paid_by_user_id}) not found"
        )

    if expense.paid_by_user_id not in expense.participant_ids:
        raise HTTPException(
            status_code=400,
            detail="The payer must be included in the participants"
        )

    # Step 2: Create main expense record
    new_expense = models.Expense(
        description=expense.description,
        total_amount=expense.total_amount,
        paid_by_user_id=expense.paid_by_user_id,
        group_id=expense.group_id
    )
    db.add(new_expense)

    # Step 3: Calculate share and create debts
    participant_count = len(expense.participant_ids)
    if participant_count == 0:
        raise HTTPException(status_code=400, detail="At least one participant is required")

    share_amount = expense.total_amount / participant_count

    for user_id in expense.participant_ids:
        if user_id == expense.paid_by_user_id:
            continue  # Don't create debt for the payer

        debt = models.Debt(
            amount=share_amount,
            owes_user_id=user_id,
            owed_to_user_id=expense.paid_by_user_id,
            expense=new_expense  # Link to the created expense
        )
        db.add(debt)

    # Step 4: Commit to the database
    db.commit()
    db.refresh(new_expense)
    return new_expense