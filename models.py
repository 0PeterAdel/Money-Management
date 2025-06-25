# models.py - Final Version with Password and Enhanced Wallet Support

from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

# --- Enum for Wallet Transaction Types ---
class WalletTransactionType(enum.Enum):
    DEPOSIT = "DEPOSIT"
    EXPENSE = "EXPENSE"
    WITHDRAWAL = "WITHDRAWAL"
    SETTLEMENT = "SETTLEMENT"

# Association table to link Users and Groups (Many-to-Many)
group_members_table = Table('group_members', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

class User(Base):
    """Represents a user in the system."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    # **NEW**: Securely stores the user's hashed password.
    hashed_password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    groups = relationship("Group", secondary=group_members_table, back_populates="members")
    expenses_paid = relationship("Expense", back_populates="payer")
    wallet_transactions = relationship("WalletTransaction", back_populates="user")


class Group(Base):
    """Represents a group of users."""
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
    currency = Column(String, default="EGP")
    date = Column(DateTime, default=datetime.utcnow)
    paid_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payer = relationship("User", back_populates="expenses_paid")
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group", back_populates="expenses")
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
    """Represents a transaction for a group's wallet."""
    # **MODIFIED**: Added new Enum types
    __tablename__ = "wallet_transactions"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    type = Column(Enum(WalletTransactionType), nullable=False)
    description = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group = relationship("Group", back_populates="wallet_transactions")
    user = relationship("User", back_populates="wallet_transactions")
