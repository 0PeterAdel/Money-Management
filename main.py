# main.py - The Definitive Final Version with All Features

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from collections import defaultdict
import math
import json

import models, database, security
from database import SessionLocal, engine
from pydantic import BaseModel, ConfigDict
from models import WalletTransactionType, ActionType, ActionStatus
# Make sure notifications.py exists and is correctly configured
from notifications import send_telegram_message
from fastapi.middleware.cors import CORSMiddleware

# --- Create all database tables ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Assistant API",
    version="6.0",
    description="The ultimate collaborative finance API with a secure voting and confirmation system."
)

origins = [
    "http://localhost:12000",
    "http://127.0.0.1:12000",
    "http://0.0.0.0:12000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Startup Event to Seed Default Categories ---
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    default_categories = ["Food", "Rent", "Maintenance", "Network", "Groceries", "Transport", "Other"]
    try:
        if db.query(models.Category).count() == 0:
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
class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True





# =================================================================
# DTOs (Pydantic Models) - Defines the shape of API data
# =================================================================
class UserBase(BaseModel): name: str
class UserCreate(UserBase):
    password: str
    telegram_id: Optional[str] = None
class User(UserBase):
    id: int
    telegram_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    
class ActionVoteResponse(BaseModel):
    voter: User
    vote: Optional[bool] = None
class PendingActionResponse(BaseModel):
    id: int
    action_type: ActionType
    status: ActionStatus
    details: dict 
    initiator: User
    votes: List[ActionVoteResponse]
    model_config = ConfigDict(from_attributes=True)
class VoteRequest(BaseModel):
    voter_id: int
    approve: bool
    
class Category(BaseModel): id: int; name: str; model_config = ConfigDict(from_attributes=True)
class GroupBase(BaseModel): name: str; description: Optional[str] = None
class GroupCreate(GroupBase): pass
class Group(GroupBase): id: int; members: List[User] = []; model_config = ConfigDict(from_attributes=True)
class ExpenseRequest(BaseModel): description: str; total_amount: float; group_id: int; participant_ids: List[int]; category_name: str; paid_by_user_id: int
class ExpenseResponse(BaseModel): id: int; description: str; total_amount: float; category: Category; model_config = ConfigDict(from_attributes=True)
class WalletDepositRequest(BaseModel): user_id: int; amount: float; description: Optional[str] = "Deposit"
class MemberWalletBalance(BaseModel): user: User; balance: float
class WalletBalanceResponse(BaseModel): group_id: int; total_wallet_balance: float; member_balances: List[MemberWalletBalance]
class BalanceSummaryResponse(BaseModel): debtor: User; creditor: User; amount: float
class MessageResponse(BaseModel): message: str
class WalletWithdrawalRequest(BaseModel): user_id: int; amount: float; password: str
class SettleDebtsRequest(BaseModel): user_id: Optional[int] = None
class SettlementLog(BaseModel): debt_id: int; amount_settled: float; status: str
class SettlementSummaryResponse(BaseModel): message: str; settlements: List[SettlementLog]
class DebtResponse(BaseModel):
    id: int; total_amount: float; remaining_amount: float; is_settled: bool; expense_id: int
    debtor: User; creditor: User
    payments: List['PaymentResponse'] = []
    model_config = ConfigDict(from_attributes=True)
class PaymentResponse(BaseModel):
    id: int; amount: float; date: datetime
    model_config = ConfigDict(from_attributes=True)
class LinkTelegramRequest(BaseModel):
    username: str
    password: str
    telegram_id: str
    
# =================================================================
# Helper Functions & Core Logic
# =================================================================
def get_user_wallet_balance(user_id: int, group_id: int, db: Session) -> float:
    balance = db.query(func.sum(models.WalletTransaction.amount)).filter(
        models.WalletTransaction.group_id == group_id, 
        models.WalletTransaction.user_id == user_id,
        models.WalletTransaction.status == ActionStatus.CONFIRMED
    ).scalar() or 0
    return balance

def calculate_remaining_amount(debt: models.Debt) -> float:
    total_paid = sum(payment.amount for payment in debt.payments)
    return round(debt.total_amount - total_paid, 2)

def _execute_confirmed_expense(details: dict, db: Session):
    category = db.query(models.Category).filter(func.lower(models.Category.name) == details['category_name'].lower().strip()).first()
    if not category: category = models.Category(name=details['category_name'].strip().capitalize()); db.add(category); db.flush()
    new_expense = models.Expense(
        description=details['description'], total_amount=details['total_amount'], group_id=details['group_id'],
        paid_by_user_id=details['paid_by_user_id'], category_id=category.id, status=ActionStatus.CONFIRMED
    )
    db.add(new_expense)
    share = round(details['total_amount'] / len(details['participant_ids']), 2)
    for user_id in details['participant_ids']:
        if user_id == details['paid_by_user_id']: continue
        db.add(models.Debt(total_amount=share, owes_user_id=user_id, owed_to_user_id=details['paid_by_user_id'], expense=new_expense))
    db.flush()

def _execute_confirmed_deposit(details: dict, db: Session):
    deposit_tx = models.WalletTransaction(
        amount=details['amount'], type=WalletTransactionType.DEPOSIT, description=details.get('description', 'Deposit'),
        group_id=details['group_id'], user_id=details['user_id'], status=ActionStatus.CONFIRMED
    )
    db.add(deposit_tx)
    db.flush()

def _process_action_vote(action_id: int, db: Session):
    action = db.query(models.PendingAction).options(joinedload(models.PendingAction.votes)).filter(models.PendingAction.id == action_id).first()
    if not action or action.status != ActionStatus.PENDING: return
    votes, total_voters = action.votes, len(action.votes)
    approvals = sum(1 for v in votes if v.vote is True)
    rejections = sum(1 for v in votes if v.vote is False)
    if approvals / total_voters > 0.5:
        action.status = ActionStatus.CONFIRMED
        details = json.loads(action.details)
        if action.action_type == ActionType.EXPENSE: _execute_confirmed_expense(details, db)
        elif action.action_type == ActionType.WALLET_DEPOSIT: _execute_confirmed_deposit(details, db)
    elif rejections / total_voters >= 0.5:
        action.status = ActionStatus.REJECTED
    db.commit()

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
    new_user = models.User(name=user.name, hashed_password=hashed_password, telegram_id=user.telegram_id)
    db.add(new_user); db.commit(); db.refresh(new_user)
    return new_user

@app.get("/users", response_model=List[User], tags=["Users & Security"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.User).offset(skip).limit(limit).all()

@app.get("/users/by-name/{username}", response_model=User, tags=["Users & Security"])
def get_user_by_name(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(func.lower(models.User.name) == username.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users/link-telegram", response_model=User, tags=["Users & Security"])
def link_telegram_account(link_request: LinkTelegramRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == link_request.username).first()
    if not user or not security.verify_password(link_request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    existing_link = db.query(models.User).filter(models.User.telegram_id == link_request.telegram_id).first()
    if existing_link and existing_link.id != user.id:
        raise HTTPException(status_code=400, detail="This Telegram account is already linked to another user.")
    user.telegram_id = link_request.telegram_id
    db.commit(); db.refresh(user)
    return user

@app.delete("/users/{user_id}", response_model=MessageResponse, tags=["Users & Security"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    outstanding_debts_count = db.query(models.Debt).join(models.Expense).filter(((models.Debt.owes_user_id == user_id) | (models.Debt.owed_to_user_id == user_id)), models.Debt.is_settled == False, models.Expense.status == ActionStatus.CONFIRMED).count()
    if outstanding_debts_count > 0: raise HTTPException(status_code=400, detail="Cannot delete user. They have outstanding confirmed debts.")
    wallet_balances_query = db.query(func.sum(models.WalletTransaction.amount)).filter(models.WalletTransaction.user_id == user_id, models.WalletTransaction.status == ActionStatus.CONFIRMED).scalar() or 0
    if not math.isclose(wallet_balances_query, 0): raise HTTPException(status_code=400, detail="Cannot delete user. They have a non-zero balance in wallets.")
    pending_actions_count = db.query(models.PendingAction).filter(models.PendingAction.initiator_id == user_id, models.PendingAction.status == ActionStatus.PENDING).count()
    if pending_actions_count > 0: raise HTTPException(status_code=400, detail="Cannot delete user. They have pending actions that must be resolved.")
    db.delete(user); db.commit()
    return {"message": f"User '{user.name}' has been deleted."}

# --- Groups & Members ---
@app.post("/groups", response_model=Group, status_code=status.HTTP_201_CREATED, tags=["Groups & Members"])
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    new_group = models.Group(**group.dict()); db.add(new_group); db.commit(); db.refresh(new_group); return new_group

@app.get("/groups", response_model=List[GroupResponse], tags=["Groups & Members"])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Group).offset(skip).limit(limit).all()

@app.get("/users/{user_id}/groups", response_model=List[Group], tags=["Groups & Members"])
def get_user_groups(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).options(joinedload(models.User.groups).joinedload(models.Group.members)).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.groups
    
@app.post("/groups/{group_id}/add_member/{user_id}", response_model=Group, tags=["Groups & Members"])
def add_member_to_group(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    if user in group.members: raise HTTPException(status_code=400, detail="User is already a member")
    group.members.append(user); db.commit(); db.refresh(group); return group

@app.delete("/groups/{group_id}/remove_member/{user_id}", response_model=MessageResponse, tags=["Groups & Members"])
def remove_member_from_group(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user not in group.members: raise HTTPException(status_code=404, detail="User is not a member of this group")
    group_debts_count = db.query(models.Debt).join(models.Expense).filter(models.Expense.group_id == group_id, ((models.Debt.owes_user_id == user_id) | (models.Debt.owed_to_user_id == user_id)), models.Debt.is_settled == False, models.Expense.status == ActionStatus.CONFIRMED).count()
    if group_debts_count > 0: raise HTTPException(status_code=400, detail="Cannot remove member. They have outstanding debts in this group.")
    user_balance_in_group = get_user_wallet_balance(user_id=user_id, group_id=group_id, db=db)
    if not math.isclose(user_balance_in_group, 0): raise HTTPException(status_code=400, detail=f"Cannot remove member. They have a non-zero wallet balance of {user_balance_in_group} in this group.")
    group.members.remove(user); db.commit()
    return {"message": f"User '{user.name}' removed from group '{group.name}'."}

# --- Actions and Voting Endpoints ---
@app.get("/categories", response_model=List[Category], tags=["Categories"])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.name).all()

@app.post("/actions/{action_id}/vote", response_model=PendingActionResponse, tags=["Actions & Voting"])
def cast_vote(action_id: int, vote_data: VoteRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    vote_record = db.query(models.ActionVote).filter(models.ActionVote.action_id == action_id, models.ActionVote.voter_id == vote_data.voter_id).first()
    if not vote_record: raise HTTPException(status_code=404, detail="You are not eligible to vote on this action.")
    if vote_record.vote is not None: raise HTTPException(status_code=400, detail="You have already voted.")
    vote_record.vote = vote_data.approve
    db.commit()
    background_tasks.add_task(_process_action_vote, action_id, db)
    db.refresh(vote_record.action)
    action = vote_record.action
    action.details = json.loads(action.details)
    return action

@app.get("/actions/pending", response_model=List[PendingActionResponse], tags=["Actions & Voting"])
def get_pending_actions_for_user(user_id: int, db: Session = Depends(get_db)):
    pending_votes = db.query(models.ActionVote).filter(models.ActionVote.voter_id == user_id, models.ActionVote.vote == None).options(joinedload(models.ActionVote.action).joinedload(models.PendingAction.initiator)).all()
    actions = [vote.action for vote in pending_votes if vote.action.status == ActionStatus.PENDING]
    for action in actions:
        action.details = json.loads(action.details)
    return actions

# --- MODIFIED Endpoints to Create Pending Actions ---
@app.post("/expenses", response_model=PendingActionResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Expenses & Debts"])
def request_new_expense(expense: ExpenseRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    group = db.query(models.Group).options(joinedload(models.Group.members)).filter(models.Group.id == expense.group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    voter_users = db.query(models.User).filter(models.User.id.in_(expense.participant_ids), models.User.id != expense.paid_by_user_id).all()
    if not voter_users: raise HTTPException(status_code=400, detail="An expense must have at least one other participant to confirm.")
    action_details = json.dumps(expense.dict())
    pending_action = models.PendingAction(action_type=ActionType.EXPENSE, details=action_details, group_id=expense.group_id, initiator_id=expense.paid_by_user_id)
    db.add(pending_action); db.flush()
    for voter_id in expense.participant_ids:
        db.add(models.ActionVote(action_id=pending_action.id, voter_id=voter_id, vote=(True if voter_id == expense.paid_by_user_id else None)))
    db.commit(); db.refresh(pending_action)
    background_tasks.add_task(_process_action_vote, pending_action.id, db)
    db.refresh(pending_action)
    pending_action.details = json.loads(pending_action.details)
    return pending_action

@app.post("/groups/{group_id}/wallet/deposit", response_model=PendingActionResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Group Wallet"])
def request_wallet_deposit(group_id: int, deposit: WalletDepositRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    group = db.query(models.Group).options(joinedload(models.Group.members)).filter(models.Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    if deposit.amount <= 0: raise HTTPException(status_code=400, detail="Deposit must be positive.")
    voter_users = [m for m in group.members if m.id != deposit.user_id]
    if not voter_users:
        details = deposit.dict()
        details['group_id'] = group_id
        _execute_confirmed_deposit(details, db)
        db.commit()
        raise HTTPException(status_code=200, detail="Deposit auto-confirmed as you are the only member.")
    deposit_details = deposit.dict()
    deposit_details['group_id'] = group_id
    action_details = json.dumps(deposit_details)
    pending_action = models.PendingAction(action_type=ActionType.WALLET_DEPOSIT, details=action_details, group_id=group_id, initiator_id=deposit.user_id)
    db.add(pending_action); db.flush()
    for member in group.members:
        db.add(models.ActionVote(action_id=pending_action.id, voter_id=member.id, vote=(True if member.id == deposit.user_id else None)))
    db.commit(); db.refresh(pending_action)
    background_tasks.add_task(_process_action_vote, pending_action.id, db)
    db.refresh(pending_action)
    pending_action.details = json.loads(pending_action.details)
    return pending_action

# --- Wallet & Debt Read/Management Endpoints ---
@app.get("/debts/history", response_model=List[DebtResponse], tags=["Expenses & Debts"])
def get_all_debts_history(db: Session = Depends(get_db)):
    debts = db.query(models.Debt).options(joinedload(models.Debt.debtor), joinedload(models.Debt.creditor), joinedload(models.Debt.payments)).join(models.Expense).filter(models.Expense.status == ActionStatus.CONFIRMED).all()
    return [format_debt_response(debt) for debt in debts]

@app.get("/groups/{group_id}/wallet/balance", response_model=WalletBalanceResponse, tags=["Group Wallet"])
def get_wallet_balance(group_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).options(joinedload(models.Group.members)).filter(models.Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    balances_query = (db.query(models.WalletTransaction.user_id, func.sum(models.WalletTransaction.amount).label("net_balance")).filter(models.WalletTransaction.group_id == group_id, models.WalletTransaction.status == ActionStatus.CONFIRMED).group_by(models.WalletTransaction.user_id).all())
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
    wallet_tx = models.WalletTransaction(amount=-withdrawal.amount, type=WalletTransactionType.WITHDRAWAL, description="User withdrawal", group_id=group_id, user_id=withdrawal.user_id, status=ActionStatus.CONFIRMED)
    db.add(wallet_tx); db.commit()
    return get_wallet_balance(group_id=group_id, db=db)

@app.post("/groups/{group_id}/wallet/settle-debts", response_model=SettlementSummaryResponse, tags=["Group Wallet"])
def settle_group_debts_from_wallet(group_id: int, request: SettleDebtsRequest, db: Session = Depends(get_db)):
    group = db.query(models.Group).options(joinedload(models.Group.members)).filter(models.Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    target_user_ids = [request.user_id] if request.user_id else [m.id for m in group.members]
    settlement_logs = []
    wallet_balances = {member.id: get_user_wallet_balance(member.id, group_id, db) for member in group.members}
    debts_to_check = db.query(models.Debt).options(joinedload(models.Debt.creditor), joinedload(models.Debt.debtor)).join(models.Expense).filter(models.Debt.owes_user_id.in_(target_user_ids), models.Expense.group_id == group_id, models.Debt.is_settled == False, models.Expense.status == ActionStatus.CONFIRMED).order_by(models.Expense.date).all()
    for debt in debts_to_check:
        remaining_amount = calculate_remaining_amount(debt)
        debtor_balance = wallet_balances.get(debt.owes_user_id, 0)
        if debtor_balance >= remaining_amount:
            wallet_balances[debt.owes_user_id] -= remaining_amount
            wallet_balances[debt.owed_to_user_id] = wallet_balances.get(debt.owed_to_user_id, 0) + remaining_amount
            debit_tx = models.WalletTransaction(amount=-remaining_amount, type=WalletTransactionType.SETTLEMENT, description=f"Paid debt to {debt.creditor.name}", group_id=group_id, user_id=debt.owes_user_id, status=ActionStatus.CONFIRMED)
            credit_tx = models.WalletTransaction(amount=remaining_amount, type=WalletTransactionType.SETTLEMENT, description=f"Received settlement from {debt.debtor.name}", group_id=group_id, user_id=debt.owed_to_user_id, status=ActionStatus.CONFIRMED)
            payment_record = models.Payment(amount=remaining_amount, debt_id=debt.id)
            db.add_all([debit_tx, credit_tx, payment_record]); debt.is_settled = True
            settlement_logs.append(SettlementLog(debt_id=debt.id, amount_settled=remaining_amount, status="Fully Settled"))
        else:
            settlement_logs.append(SettlementLog(debt_id=debt.id, amount_settled=0, status="Insufficient Funds"))
    db.commit()
    return SettlementSummaryResponse(message="Wallet settlement process completed.", settlements=settlement_logs)

# --- Comprehensive Balance Summary Endpoint (Corrected) ---
@app.get("/balance-summary", response_model=List[BalanceSummaryResponse], tags=["Smart Features"])
def get_balance_summary(db: Session = Depends(get_db)):
    net_balances = defaultdict(float)
    # Step 1: Calculate balances from CONFIRMED inter-personal debts
    unsettled_debts = db.query(models.Debt).join(models.Expense).filter(models.Debt.is_settled == False, models.Expense.status == ActionStatus.CONFIRMED).all()
    for debt in unsettled_debts:
        remaining = calculate_remaining_amount(debt)
        if remaining > 0:
            net_balances[debt.owed_to_user_id] += remaining
            net_balances[debt.owes_user_id] -= remaining
    # Step 2: Calculate balances from CONFIRMED wallet transactions
    wallet_balances_query = (db.query(models.WalletTransaction.user_id, func.sum(models.WalletTransaction.amount).label("balance")).filter(models.WalletTransaction.status == ActionStatus.CONFIRMED).group_by(models.WalletTransaction.user_id).all())
    for user_id, balance in wallet_balances_query:
        if balance is not None: net_balances[user_id] += balance
    # Step 3: Generate the simplified settlement plan
    debtors = sorted([(uid, bal) for uid, bal in net_balances.items() if bal < -0.01], key=lambda x: x[1])
    creditors = sorted([(uid, bal) for uid, bal in net_balances.items() if bal > 0.01], key=lambda x: x[1], reverse=True)
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
            debtors[debtor_idx] = (debtor_id, debtor_balance + amount_to_transfer)
            creditors[creditor_idx] = (creditor_id, creditor_balance - amount_to_transfer)
        if math.isclose(debtors[debtor_idx][1], 0, abs_tol=0.01): debtor_idx += 1
        if math.isclose(creditors[creditor_idx][1], 0, abs_tol=0.01): creditor_idx += 1
    return settlement_plan