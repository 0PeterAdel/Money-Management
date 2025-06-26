# models.py

from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Table, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

# --- Enums for Statuses and Types ---
class ActionStatus(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"

class ActionType(enum.Enum):
    EXPENSE = "EXPENSE"
    WALLET_DEPOSIT = "WALLET_DEPOSIT"

class WalletTransactionType(enum.Enum):
    DEPOSIT = "DEPOSIT"
    EXPENSE = "EXPENSE"
    WITHDRAWAL = "WITHDRAWAL"
    SETTLEMENT = "SETTLEMENT"

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    expenses = relationship("Expense", back_populates="category")

# --- NEW: PendingAction Table ---
class PendingAction(Base):
    """Stores actions that require confirmation from other users."""
    __tablename__ = "pending_actions"
    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(Enum(ActionType), nullable=False)
    status = Column(Enum(ActionStatus), default=ActionStatus.PENDING)
    details = Column(Text, nullable=False) # Stores JSON data of the action
    
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    group = relationship("Group")
    initiator = relationship("User")
    votes = relationship("ActionVote", back_populates="action", cascade="all, delete-orphan")

# --- NEW: ActionVote Table ---
class ActionVote(Base):
    """Stores a single user's vote on a pending action."""
    __tablename__ = "action_votes"
    id = Column(Integer, primary_key=True, index=True)
    vote = Column(Boolean, nullable=True) # True for Approve, False for Reject, Null for not voted yet
    
    action_id = Column(Integer, ForeignKey("pending_actions.id"), nullable=False)
    voter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    action = relationship("PendingAction", back_populates="votes")
    voter = relationship("User")

# Association table to link Users and Groups
group_members_table = Table('group_members', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    telegram_id = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    groups = relationship("Group", secondary=group_members_table, back_populates="members")
    expenses_paid = relationship("Expense", back_populates="payer")
    wallet_transactions = relationship("WalletTransaction", back_populates="user")


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    members = relationship("User", secondary=group_members_table, back_populates="groups")
    expenses = relationship("Expense", back_populates="group")
    wallet_transactions = relationship("WalletTransaction", back_populates="group")


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    total_amount = Column(Float, nullable=False)
    status = Column(Enum(ActionStatus), default=ActionStatus.CONFIRMED)
    date = Column(DateTime, default=datetime.utcnow)
    
    paid_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payer = relationship("User", back_populates="expenses_paid")
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group", back_populates="expenses")
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="expenses")
    
    debts = relationship("Debt", back_populates="expense", cascade="all, delete-orphan")


class Debt(Base):
    __tablename__ = "debts"
    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float, nullable=False) 
    is_settled = Column(Boolean, default=False)
    owes_user_id = Column(Integer, ForeignKey("users.id"))
    owed_to_user_id = Column(Integer, ForeignKey("users.id"))
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    expense = relationship("Expense", back_populates="debts")
    debtor = relationship("User", foreign_keys=[owes_user_id])
    creditor = relationship("User", foreign_keys=[owed_to_user_id])
    payments = relationship("Payment", back_populates="debt", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    debt_id = Column(Integer, ForeignKey("debts.id"))
    debt = relationship("Debt", back_populates="payments")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    type = Column(Enum(WalletTransactionType), nullable=False)
    status = Column(Enum(ActionStatus), default=ActionStatus.CONFIRMED)
    description = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group = relationship("Group", back_populates="wallet_transactions")
    user = relationship("User", back_populates="wallet_transactions")