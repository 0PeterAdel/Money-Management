# main.py

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from collections import defaultdict
import math

# Import everything from our other project files
import models
import database
import security
from database import SessionLocal, engine
from pydantic import BaseModel, ConfigDict
from models import WalletTransactionType

# --- Create all database tables based on models.py ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Assistant API",
    version="5.0",
    description="The final, robust API with expense categories, advanced wallet settlement, and full user/group management."
)

# --- Startup Event to Seed Database ---
@app.on_event("startup")
def startup_event():
    """Seeds the database with default categories if they don't exist."""
    db = SessionLocal()
    default_categories = ["Food", "Rent", "Maintenance", "Network", "Groceries", "Transport", "Other"]
    try:
        existing_categories_count = db.query(models.Category).count()
        if existing_categories_count == 0:
            for cat_name in default_categories:
                db.add(models.Category(name=cat_name))
            db.commit()
    finally:
        db.close()

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

class UserBase(BaseModel): name: str
class UserCreate(UserBase): password: str
class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Category(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class GroupBase(BaseModel): name: str; description: Optional[str] = None
class GroupCreate(GroupBase): pass
class Group(GroupBase):
    id: int
    members: List[User] = []
    model_config = ConfigDict(from_attributes=True)

class ExpenseCreate(BaseModel):
    description: str
    total_amount: float
    group_id: int
    participant_ids: List[int]
    category_name: str
    paid_by_user_id: Optional[int] = None
    paid_from_wallet: bool = False

class ExpenseResponse(BaseModel):
    id: int
    description: str
    total_amount: float
    category: Category
    model_config = ConfigDict(from_attributes=True)
    
class PaymentResponse(BaseModel):
    id: int; amount: float; date: datetime
    model_config = ConfigDict(from_attributes=True)

class DebtResponse(BaseModel):
    id: int; total_amount: float; remaining_amount: float; is_settled: bool; expense_id: int
    debtor: User; creditor: User
    payments: List[PaymentResponse] = []
    model_config = ConfigDict(from_attributes=True)

class BalanceSummaryResponse(BaseModel):
    debtor: User; creditor: User; amount: float

class MemberWalletBalance(BaseModel): user: User; balance: float
class WalletBalanceResponse(BaseModel):
    group_id: int; total_wallet_balance: float; member_balances: List[MemberWalletBalance]

class WalletDepositRequest(BaseModel): user_id: int; amount: float; description: Optional[str] = "Deposit"
class WalletWithdrawalRequest(BaseModel): user_id: int; amount: float; password: str

class SettleDebtsRequest(BaseModel):
    user_id: Optional[int] = None

class SettlementLog(BaseModel):
    debt_id: int
    amount_settled: float
    status: str

class SettlementSummaryResponse(BaseModel):
    message: str
    settlements: List[SettlementLog]

class MessageResponse(BaseModel): message: str

# =================================================================
# Helper Functions
# =================================================================
def get_user_wallet_balance(user_id: int, group_id: int, db: Session) -> float:
    balance = db.query(func.sum(models.WalletTransaction.amount)).filter(models.WalletTransaction.group_id == group_id, models.WalletTransaction.user_id == user_id).scalar() or 0
    return balance

def calculate_remaining_amount(debt: models.Debt) -> float:
    total_paid = sum(payment.amount for payment in debt.payments)
    return round(debt.total_amount - total_paid, 2)

def format_debt_response(debt: models.Debt) -> DebtResponse:
    return DebtResponse(id=debt.id, total_amount=debt.total_amount, remaining_amount=calculate_remaining_amount(debt), is_settled=debt.is_settled, expense_id=debt.expense_id, debtor=debt.debtor, creditor=debt.creditor, payments=debt.payments)

# =================================================================
# API Endpoints
# =================================================================
@app.get("/", tags=["General"])
def read_root(): return {"message": "Welcome to the Finance Assistant System"}

# --- Users & Security Endpoints ---
@app.post("/users", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users & Security"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.name == user.name).first()
    if db_user: raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(name=user.name, hashed_password=hashed_password)
    db.add(new_user); db.commit(); db.refresh(new_user)
    return new_user

@app.get("/users", response_model=List[User], tags=["Users & Security"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.User).offset(skip).limit(limit).all()

@app.delete("/users/{user_id}", response_model=MessageResponse, tags=["Users & Security"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    outstanding_debts_count = db.query(models.Debt).filter(((models.Debt.owes_user_id == user_id) | (models.Debt.owed_to_user_id == user_id)), models.Debt.is_settled == False).count()
    if outstanding_debts_count > 0: raise HTTPException(status_code=400, detail="Cannot delete user. They have outstanding debts.")
    wallet_balances_query = db.query(func.sum(models.WalletTransaction.amount)).filter(models.WalletTransaction.user_id == user_id).scalar() or 0
    if not math.isclose(wallet_balances_query, 0): raise HTTPException(status_code=400, detail="Cannot delete user. They have a non-zero balance in wallets.")
    db.delete(user); db.commit()
    return {"message": f"User '{user.name}' has been deleted."}

# --- Groups & Member Management Endpoints ---
@app.post("/groups", response_model=Group, status_code=status.HTTP_201_CREATED, tags=["Groups & Members"])
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    new_group = models.Group(**group.dict())
    db.add(new_group); db.commit(); db.refresh(new_group)
    return new_group

@app.post("/groups/{group_id}/add_member/{user_id}", response_model=Group, tags=["Groups & Members"])
def add_member_to_group(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    if user in group.members: raise HTTPException(status_code=400, detail="User is already a member")
    group.members.append(user)
    db.commit(); db.refresh(group)
    return group

@app.delete("/groups/{group_id}/remove_member/{user_id}", response_model=MessageResponse, tags=["Groups & Members"])
def remove_member_from_group(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user not in group.members: raise HTTPException(status_code=404, detail="User is not a member of this group")
    group_debts_count = db.query(models.Debt).join(models.Expense).filter(models.Expense.group_id == group_id, ((models.Debt.owes_user_id == user_id) | (models.Debt.owed_to_user_id == user_id)), models.Debt.is_settled == False).count()
    if group_debts_count > 0: raise HTTPException(status_code=400, detail="Cannot remove member. They have outstanding debts in this group.")
    user_balance_in_group = get_user_wallet_balance(user_id=user_id, group_id=group_id, db=db)
    if not math.isclose(user_balance_in_group, 0): raise HTTPException(status_code=400, detail=f"Cannot remove member. They have a non-zero wallet balance of {user_balance_in_group} in this group.")
    group.members.remove(user); db.commit()
    return {"message": f"User '{user.name}' removed from group '{group.name}'."}

# --- Categories Endpoint ---
@app.get("/categories", response_model=List[Category], tags=["Categories"])
def get_categories(db: Session = Depends(get_db)):
    """Retrieves all available expense categories."""
    return db.query(models.Category).order_by(models.Category.name).all()

# --- Expenses Endpoint (with Categories) ---
@app.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED, tags=["Expenses & Debts"])
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(func.lower(models.Category.name) == expense.category_name.lower().strip()).first()
    if not category:
        category = models.Category(name=expense.category_name.strip().capitalize())
        db.add(category)
        db.flush()
    if expense.paid_from_wallet and expense.paid_by_user_id: raise HTTPException(status_code=400, detail="Choose one payment method.")
    if not expense.paid_from_wallet and not expense.paid_by_user_id: raise HTTPException(status_code=400, detail="Must specify a payment method.")
    new_expense = models.Expense(description=expense.description, total_amount=expense.total_amount, group_id=expense.group_id, paid_by_user_id=expense.paid_by_user_id, category_id=category.id)
    db.add(new_expense)
    participant_count = len(expense.participant_ids)
    if participant_count == 0: raise HTTPException(status_code=400, detail="At least one participant is required")
    share_amount = round(expense.total_amount / participant_count, 2)
    if expense.paid_from_wallet:
        total_wallet_balance = (db.query(func.sum(models.WalletTransaction.amount)).filter(models.WalletTransaction.group_id == expense.group_id).scalar() or 0)
        if total_wallet_balance < expense.total_amount: raise HTTPException(status_code=400, detail=f"Insufficient wallet balance ({total_wallet_balance}) for expense ({expense.total_amount}).")
        for user_id in expense.participant_ids:
            db.add(models.WalletTransaction(amount=-share_amount, type=WalletTransactionType.EXPENSE, description=f"Share of: {expense.description}", group_id=expense.group_id, user_id=user_id))
    else:
        for user_id in expense.participant_ids:
            if user_id == expense.paid_by_user_id: continue
            db.add(models.Debt(total_amount=share_amount, owes_user_id=user_id, owed_to_user_id=expense.paid_by_user_id, expense=new_expense))
    db.commit(); db.refresh(new_expense)
    return new_expense

@app.get("/debts/history", response_model=List[DebtResponse], tags=["Expenses & Debts"])
def get_all_debts_history(db: Session = Depends(get_db)):
    debts = db.query(models.Debt).options(joinedload(models.Debt.debtor), joinedload(models.Debt.creditor), joinedload(models.Debt.payments)).all()
    return [format_debt_response(debt) for debt in debts]

# --- Group Wallet Endpoints ---
@app.post("/groups/{group_id}/wallet/deposit", response_model=WalletBalanceResponse, tags=["Group Wallet"])
def deposit_to_wallet(group_id: int, deposit: WalletDepositRequest, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    user = db.query(models.User).filter(models.User.id == deposit.user_id).first()
    if not user or user not in group.members: raise HTTPException(status_code=400, detail="User not found or not in group")
    if deposit.amount <= 0: raise HTTPException(status_code=400, detail="Deposit amount must be positive.")
    wallet_tx = models.WalletTransaction(amount=deposit.amount, type=WalletTransactionType.DEPOSIT, description=deposit.description, group_id=group_id, user_id=deposit.user_id)
    db.add(wallet_tx); db.commit()
    return get_wallet_balance(group_id=group_id, db=db)

@app.get("/groups/{group_id}/wallet/balance", response_model=WalletBalanceResponse, tags=["Group Wallet"])
def get_wallet_balance(group_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).options(joinedload(models.Group.members)).filter(models.Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    balances_query = (db.query(models.WalletTransaction.user_id, func.sum(models.WalletTransaction.amount).label("net_balance")).filter(models.WalletTransaction.group_id == group_id).group_by(models.WalletTransaction.user_id).all())
    balances_dict = {user_id: net_balance for user_id, net_balance in balances_query}
    member_balances_response = [MemberWalletBalance(user=member, balance=round(balances_dict.get(member.id, 0), 2)) for member in group.members]
    total_balance = round(sum(b.balance for b in member_balances_response), 2)
    return WalletBalanceResponse(group_id=group_id, total_wallet_balance=total_balance, member_balances=member_balances_response)

@app.post("/groups/{group_id}/wallet/withdraw", response_model=WalletBalanceResponse, tags=["Group Wallet"])
def withdraw_from_wallet(group_id: int, withdrawal: WalletWithdrawalRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == withdrawal.user_id).first()
    if not user or not security.verify_password(withdrawal.password, user.hashed_password): raise HTTPException(status_code=401, detail="Invalid user or password")
    user_balance = get_user_wallet_balance(user_id=withdrawal.user_id, group_id=group_id, db=db)
    if withdrawal.amount > user_balance: raise HTTPException(status_code=400, detail=f"Withdrawal amount exceeds user's balance. Max available: {user_balance}")
    if withdrawal.amount <= 0: raise HTTPException(status_code=400, detail="Withdrawal amount must be positive.")
    wallet_tx = models.WalletTransaction(amount=-withdrawal.amount, type=WalletTransactionType.WITHDRAWAL, description="User withdrawal", group_id=group_id, user_id=withdrawal.user_id)
    db.add(wallet_tx); db.commit()
    return get_wallet_balance(group_id=group_id, db=db)

# --- Advanced Wallet Settlement Endpoint ---
@app.post("/groups/{group_id}/wallet/settle-debts", response_model=SettlementSummaryResponse, tags=["Group Wallet"])
def settle_group_debts_from_wallet(group_id: int, request: SettleDebtsRequest, db: Session = Depends(get_db)):
    group = db.query(models.Group).options(joinedload(models.Group.members)).filter(models.Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    target_user_ids = []
    if request.user_id:
        user = db.query(models.User).filter(models.User.id == request.user_id).first()
        if not user or user not in group.members: raise HTTPException(status_code=404, detail="Target user not found or not in group")
        target_user_ids.append(user.id)
    else:
        target_user_ids = [member.id for member in group.members]
    settlement_logs = []
    wallet_balances = {member.id: get_user_wallet_balance(member.id, group_id, db) for member in group.members}
    debts_to_check = db.query(models.Debt).options(joinedload(models.Debt.creditor), joinedload(models.Debt.debtor)).join(models.Expense).filter(models.Debt.owes_user_id.in_(target_user_ids), models.Expense.group_id == group_id, models.Debt.is_settled == False).order_by(models.Expense.date).all()
    for debt in debts_to_check:
        remaining_amount = calculate_remaining_amount(debt)
        debtor_balance = wallet_balances.get(debt.owes_user_id, 0)
        if debtor_balance >= remaining_amount:
            wallet_balances[debt.owes_user_id] -= remaining_amount
            wallet_balances[debt.owed_to_user_id] = wallet_balances.get(debt.owed_to_user_id, 0) + remaining_amount
            debit_tx = models.WalletTransaction(amount=-remaining_amount, type=WalletTransactionType.SETTLEMENT, description=f"Paid debt to {debt.creditor.name}", group_id=group_id, user_id=debt.owes_user_id)
            credit_tx = models.WalletTransaction(amount=remaining_amount, type=WalletTransactionType.SETTLEMENT, description=f"Received settlement from {debt.debtor.name}", group_id=group_id, user_id=debt.owed_to_user_id)
            payment_record = models.Payment(amount=remaining_amount, debt_id=debt.id)
            db.add_all([debit_tx, credit_tx, payment_record])
            debt.is_settled = True
            settlement_logs.append(SettlementLog(debt_id=debt.id, amount_settled=remaining_amount, status="Fully Settled"))
        else:
            settlement_logs.append(SettlementLog(debt_id=debt.id, amount_settled=0, status="Insufficient Funds"))
    db.commit()
    return SettlementSummaryResponse(message="Wallet settlement process completed.", settlements=settlement_logs)
    
# --- Smart Features Endpoints ---
@app.get("/balance-summary", response_model=List[BalanceSummaryResponse], tags=["Smart Features"])
def get_balance_summary(db: Session = Depends(get_db)):
    # ... (code from previous version)
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
        new_debtor_balance, new_creditor_balance = debtor_balance + amount_to_transfer, creditor_balance - amount_to_transfer
        debtors[debtor_idx] = (debtor_id, new_debtor_balance)
        creditors[creditor_idx] = (creditor_id, new_creditor_balance)
        if math.isclose(debtors[debtor_idx][1], 0): debtor_idx += 1
        if math.isclose(creditors[creditor_idx][1], 0): creditor_idx += 1
    return settlement_plan
