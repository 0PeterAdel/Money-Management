# main.py - Final Version with Group Wallet Logic

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from collections import defaultdict
import math

import models
import database
from database import SessionLocal, engine
from pydantic import BaseModel, ConfigDict
from models import WalletTransactionType

# --- Create all database tables based on models.py ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Assistant API",
    version="3.0",
    description="An ultimate API to manage expenses, debts, partial payments, and a shared group wallet."
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
    group_id: int
    participant_ids: List[int]
    # **NEW**: Optional fields for different payment methods
    paid_by_user_id: Optional[int] = None
    paid_from_wallet: bool = False

class Expense(BaseModel):
    id: int
    description: str
    total_amount: float
    model_config = ConfigDict(from_attributes=True)

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
    remaining_amount: float
    is_settled: bool
    expense_id: int
    debtor: User
    creditor: User
    payments: List[PaymentResponse] = []
    model_config = ConfigDict(from_attributes=True)

class UserPaymentRequest(BaseModel):
    amount: float
    payer_id: int
    creditor_id: int

class BalanceSummaryResponse(BaseModel):
    debtor: User
    creditor: User
    amount: float

# --- NEW DTOs for Wallet Feature ---
class WalletDepositRequest(BaseModel):
    user_id: int
    amount: float
    description: Optional[str] = "Deposit"

class MemberWalletBalance(BaseModel):
    user: User
    balance: float

class WalletBalanceResponse(BaseModel):
    group_id: int
    total_wallet_balance: float
    member_balances: List[MemberWalletBalance]

# =================================================================
# Helper Functions (omitted for brevity, they are the same as before)
# ...

def calculate_remaining_amount(debt: models.Debt) -> float:
    total_paid = sum(payment.amount for payment in debt.payments)
    return round(debt.total_amount - total_paid, 2)

def format_debt_response(debt: models.Debt) -> DebtResponse:
    return DebtResponse(
        id=debt.id,
        total_amount=debt.total_amount,
        remaining_amount=calculate_remaining_amount(debt),
        is_settled=debt.is_settled,
        expense_id=debt.expense_id,
        debtor=debt.debtor,
        creditor=debt.creditor,
        payments=debt.payments
    )
# =================================================================
# API Endpoints
# =================================================================

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to the Finance Assistant System"}

# ... User and Group endpoints remain the same ...
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
    # --- **MODIFIED LOGIC** ---
    # Validate payment method
    if expense.paid_from_wallet and expense.paid_by_user_id:
        raise HTTPException(status_code=400, detail="Cannot specify both paid_from_wallet and paid_by_user_id. Choose one payment method.")
    if not expense.paid_from_wallet and not expense.paid_by_user_id:
        raise HTTPException(status_code=400, detail="Must specify a payment method: either paid_from_wallet or paid_by_user_id.")

    new_expense = models.Expense(
        description=expense.description,
        total_amount=expense.total_amount,
        group_id=expense.group_id,
        paid_by_user_id=expense.paid_by_user_id # Could be None
    )
    db.add(new_expense)

    participant_count = len(expense.participant_ids)
    if participant_count == 0:
        raise HTTPException(status_code=400, detail="At least one participant is required")
    share_amount = round(expense.total_amount / participant_count, 2)

    # --- Handle payment from Wallet ---
    if expense.paid_from_wallet:
        # Check if wallet has enough balance
        total_wallet_balance = db.query(func.sum(models.WalletTransaction.amount)).filter(models.WalletTransaction.group_id == expense.group_id).scalar() or 0
        if total_wallet_balance < expense.total_amount:
            raise HTTPException(status_code=400, detail=f"Insufficient wallet balance. Wallet has {total_wallet_balance}, but expense is {expense.total_amount}.")
        
        # Create negative wallet transaction for each participant
        for user_id in expense.participant_ids:
            wallet_tx = models.WalletTransaction(
                amount=-share_amount,
                type=WalletTransactionType.EXPENSE,
                description=f"Share of expense: {expense.description}",
                group_id=expense.group_id,
                user_id=user_id
            )
            db.add(wallet_tx)

    # --- Handle payment from a User (existing logic) ---
    else:
        for user_id in expense.participant_ids:
            if user_id == expense.paid_by_user_id:
                continue
            debt = models.Debt(
                total_amount=share_amount,
                owes_user_id=user_id,
                owed_to_user_id=expense.paid_by_user_id,
                expense=new_expense
            )
            db.add(debt)
    
    db.commit()
    db.refresh(new_expense)
    return new_expense

# ... Other debt/payment endpoints remain the same ...
@app.get("/debts/history", response_model=List[DebtResponse], tags=["Expenses & Debts"])
def get_all_debts_history(db: Session = Depends(get_db)):
    debts = db.query(models.Debt).options(joinedload(models.Debt.debtor), joinedload(models.Debt.creditor), joinedload(models.Debt.payments)).all()
    return [format_debt_response(debt) for debt in debts]

@app.post("/payments/pay-user", response_model=List[DebtResponse], tags=["Smart Features"])
def make_payment_to_user(payment_request: UserPaymentRequest, db: Session = Depends(get_db)):
    payer_id = payment_request.payer_id
    creditor_id = payment_request.creditor_id
    amount_to_pay = payment_request.amount
    debts_to_settle = (db.query(models.Debt).join(models.Expense).filter(models.Debt.owes_user_id == payer_id, models.Debt.owed_to_user_id == creditor_id, models.Debt.is_settled == False).order_by(models.Expense.date.asc()).all())
    if not debts_to_settle:
        raise HTTPException(status_code=404, detail=f"No outstanding debts found from user {payer_id} to user {creditor_id}")
    amount_left_to_apply = amount_to_pay
    updated_debts = []
    for debt in debts_to_settle:
        if amount_left_to_apply <= 0: break
        remaining_on_debt = calculate_remaining_amount(debt)
        if remaining_on_debt <= 0: continue
        payment_for_this_debt = min(amount_left_to_apply, remaining_on_debt)
        new_payment = models.Payment(amount=payment_for_this_debt, debt_id=debt.id)
        db.add(new_payment)
        if math.isclose(remaining_on_debt, payment_for_this_debt):
            debt.is_settled = True
        updated_debts.append(debt)
        amount_left_to_apply -= payment_for_this_debt
    if not updated_debts:
        raise HTTPException(status_code=400, detail="Could not apply payment. All debts might be settled or amount is zero.")
    db.commit()
    for debt in updated_debts: db.refresh(debt)
    return [format_debt_response(debt) for debt in updated_debts]

@app.get("/balance-summary", response_model=List[BalanceSummaryResponse], tags=["Smart Features"])
def get_balance_summary(db: Session = Depends(get_db)):
    net_balances = defaultdict(float)
    unsettled_debts = db.query(models.Debt).filter(models.Debt.is_settled == False).all()
    for debt in unsettled_debts:
        remaining = calculate_remaining_amount(debt)
        if remaining > 0:
            net_balances[debt.owed_to_user_id] += remaining
            net_balances[debt.owes_user_id] -= remaining
    debtors = sorted([(user_id, balance) for user_id, balance in net_balances.items() if balance < 0], key=lambda x: x[1])
    creditors = sorted([(user_id, balance) for user_id, balance in net_balances.items() if balance > 0], key=lambda x: x[1], reverse=True)
    settlement_plan = []
    debtor_idx, creditor_idx = 0, 0
    while debtor_idx < len(debtors) and creditor_idx < len(creditors):
        debtor_id, debtor_balance = debtors[debtor_idx]
        creditor_id, creditor_balance = creditors[creditor_idx]
        amount_to_transfer = round(min(abs(debtor_balance), creditor_balance), 2)
        if amount_to_transfer > 0:
            debtor_user = db.query(models.User).get(debtor_id)
            creditor_user = db.query(models.User).get(creditor_id)
            settlement_plan.append(BalanceSummaryResponse(debtor=debtor_user, creditor=creditor_user, amount=amount_to_transfer))
        new_debtor_balance = debtor_balance + amount_to_transfer
        new_creditor_balance = creditor_balance - amount_to_transfer
        debtors[debtor_idx] = (debtor_id, new_debtor_balance)
        creditors[creditor_idx] = (creditor_id, new_creditor_balance)
        if math.isclose(debtors[debtor_idx][1], 0): debtor_idx += 1
        if math.isclose(creditors[creditor_idx][1], 0): creditor_idx += 1
    return settlement_plan

# =================================================================
# NEW: Group Wallet Endpoints
# =================================================================

@app.post("/groups/{group_id}/wallet/deposit", response_model=WalletBalanceResponse, tags=["Group Wallet"])
def deposit_to_wallet(group_id: int, deposit: WalletDepositRequest, db: Session = Depends(get_db)):
    """Deposits money into the group's shared wallet for a specific user."""
    # Validate group and user
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    user = db.query(models.User).filter(models.User.id == deposit.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user not in group.members:
         raise HTTPException(status_code=400, detail="User is not a member of this group")

    if deposit.amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be positive.")

    # Create and save the deposit transaction
    wallet_tx = models.WalletTransaction(
        amount=deposit.amount,
        type=WalletTransactionType.DEPOSIT,
        description=deposit.description,
        group_id=group_id,
        user_id=deposit.user_id
    )
    db.add(wallet_tx)
    db.commit()

    # Return the new wallet balance
    return get_wallet_balance(group_id=group_id, db=db)


@app.get("/groups/{group_id}/wallet/balance", response_model=WalletBalanceResponse, tags=["Group Wallet"])
def get_wallet_balance(group_id: int, db: Session = Depends(get_db)):
    """Retrieves the total balance of the group wallet and the net balance for each member."""
    group = db.query(models.Group).options(joinedload(models.Group.members)).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # Calculate the net balance for each member
    member_balances_query = (
        db.query(
            models.WalletTransaction.user_id,
            func.sum(models.WalletTransaction.amount).label("net_balance")
        )
        .filter(models.WalletTransaction.group_id == group_id)
        .group_by(models.WalletTransaction.user_id)
        .all()
    )
    
    # Create a dictionary for easy lookup
    balances_dict = {user_id: net_balance for user_id, net_balance in member_balances_query}
    
    # Format the response
    member_balances_response = []
    total_balance = 0
    for member in group.members:
        balance = balances_dict.get(member.id, 0)
        member_balances_response.append(MemberWalletBalance(user=member, balance=balance))
        total_balance += balance

    return WalletBalanceResponse(
        group_id=group_id,
        total_wallet_balance=total_balance,
        member_balances=member_balances_response
    )
