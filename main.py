# main.py - Final Version with Partial Payments

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime

import models
import database
from database import SessionLocal, engine
from pydantic import BaseModel, ConfigDict

# --- Create all database tables based on models.py ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Assistant API",
    version="1.2",
    description="An API to manage personal and group expenses, track debts, and make partial payments."
)

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================
# DTOs (Pydantic Models)
# =================================================================

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class GroupBase(BaseModel):
    name: str
    description: str | None = None

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    members: List[User] = []
    model_config = ConfigDict(from_attributes=True)

class ExpenseCreate(BaseModel):
    description: str
    total_amount: float
    paid_by_user_id: int
    group_id: int
    participant_ids: List[int]

class Expense(BaseModel):
    id: int
    description: str
    total_amount: float
    model_config = ConfigDict(from_attributes=True)

# --- NEW/UPDATED Models for Debts and Payments ---
class PaymentResponse(BaseModel):
    id: int
    amount: float
    date: datetime
    model_config = ConfigDict(from_attributes=True)

class PaymentCreate(BaseModel):
    amount: float

class DebtResponse(BaseModel):
    id: int
    total_amount: float
    remaining_amount: float # New field
    is_settled: bool
    expense_id: int
    debtor: User
    creditor: User
    payments: List[PaymentResponse] = [] # List of all payments
    model_config = ConfigDict(from_attributes=True)


# =================================================================
# API Endpoints
# =================================================================

# ... All User and Group endpoints remain the same ...
@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to the Finance Assistant System"}

@app.post("/users", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.name == user.name).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = models.User(name=user.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users", response_model=List[User], tags=["Users"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@app.post("/groups", response_model=Group, status_code=status.HTTP_201_CREATED, tags=["Groups"])
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    new_group = models.Group(**group.dict())
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group

@app.post("/groups/{group_id}/add_member/{user_id}", response_model=Group, tags=["Groups"])
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

# --- Expenses & Debts Endpoints ---
@app.post("/expenses", response_model=Expense, status_code=status.HTTP_201_CREATED, tags=["Expenses & Debts"])
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    # ... (logic remains mostly the same, but we now save total_amount to the Debt)
    payer = db.query(models.User).filter(models.User.id == expense.paid_by_user_id).first()
    if not payer:
        raise HTTPException(status_code=404, detail=f"Payer user (ID: {expense.paid_by_user_id}) not found")
    if expense.paid_by_user_id not in expense.participant_ids:
        raise HTTPException(status_code=400, detail="The payer must be included in the participants")
    new_expense = models.Expense(
        description=expense.description,
        total_amount=expense.total_amount,
        paid_by_user_id=expense.paid_by_user_id,
        group_id=expense.group_id
    )
    db.add(new_expense)
    participant_count = len(expense.participant_ids)
    if participant_count == 0:
        raise HTTPException(status_code=400, detail="At least one participant is required")
    share_amount = round(expense.total_amount / participant_count, 2)
    for user_id in expense.participant_ids:
        if user_id == expense.paid_by_user_id:
            continue
        debt = models.Debt(
            total_amount=share_amount, # Changed from 'amount' to 'total_amount'
            owes_user_id=user_id,
            owed_to_user_id=expense.paid_by_user_id,
            expense=new_expense
        )
        db.add(debt)
    db.commit()
    db.refresh(new_expense)
    return new_expense

# --- Helper function to format debt responses ---
def format_debt_responses(debts: List[models.Debt]) -> List[DebtResponse]:
    response = []
    for debt in debts:
        total_paid = sum(payment.amount for payment in debt.payments)
        remaining = debt.total_amount - total_paid
        response.append(
            DebtResponse(
                id=debt.id,
                total_amount=debt.total_amount,
                remaining_amount=remaining,
                is_settled=debt.is_settled,
                expense_id=debt.expense_id,
                debtor=debt.debtor,
                creditor=debt.creditor,
                payments=debt.payments
            )
        )
    return response

@app.get("/debts", response_model=List[DebtResponse], tags=["Expenses & Debts"])
def get_unsettled_debts(db: Session = Depends(get_db)):
    debts = (
        db.query(models.Debt)
        .filter(models.Debt.is_settled == False)
        .options(joinedload(models.Debt.debtor), joinedload(models.Debt.creditor), joinedload(models.Debt.payments))
        .all()
    )
    return format_debt_responses(debts)

@app.get("/debts/history", response_model=List[DebtResponse], tags=["Expenses & Debts"])
def get_all_debts_history(db: Session = Depends(get_db)):
    debts = (
        db.query(models.Debt)
        .options(joinedload(models.Debt.debtor), joinedload(models.Debt.creditor), joinedload(models.Debt.payments))
        .all()
    )
    return format_debt_responses(debts)

# --- NEW Endpoint to make a payment ---
@app.post("/debts/{debt_id}/pay", response_model=DebtResponse, tags=["Expenses & Debts"])
def make_payment_for_debt(debt_id: int, payment_data: PaymentCreate, db: Session = Depends(get_db)):
    # Step 1: Find the debt
    debt = db.query(models.Debt).filter(models.Debt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail=f"Debt with ID {debt_id} not found")
    if debt.is_settled:
        raise HTTPException(status_code=400, detail="This debt has already been settled")

    # Step 2: Calculate remaining amount and validate payment
    total_paid = sum(p.amount for p in debt.payments)
    remaining_amount = debt.total_amount - total_paid
    
    if payment_data.amount > remaining_amount:
        raise HTTPException(status_code=400, detail=f"Payment of {payment_data.amount} exceeds the remaining amount of {remaining_amount}")
    
    # Step 3: Create and save the new payment record
    new_payment = models.Payment(amount=payment_data.amount, debt_id=debt.id)
    db.add(new_payment)
    
    # Step 4: Check if the debt is now fully settled
    if (total_paid + payment_data.amount) >= debt.total_amount:
        debt.is_settled = True
        
    db.commit()
    db.refresh(debt)
    
    # Return the updated debt status
    # We need to manually calculate the new remaining amount for the response
    final_total_paid = total_paid + new_payment.amount
    final_remaining = debt.total_amount - final_total_paid

    return DebtResponse(
        id=debt.id,
        total_amount=debt.total_amount,
        remaining_amount=final_remaining,
        is_settled=debt.is_settled,
        expense_id=debt.expense_id,
        debtor=debt.debtor,
        creditor=debt.creditor,
        payments=debt.payments
    )