# models.py - Final Version with Group Wallet Support

from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

# --- Enum for Wallet Transaction Types ---
class WalletTransactionType(enum.Enum):
    DEPOSIT = "DEPOSIT"
    EXPENSE = "EXPENSE"

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
    # **NEW**: A group now has a list of all its wallet transactions.
    wallet_transactions = relationship("WalletTransaction", back_populates="group")

class Expense(Base):
    """Represents a single expense transaction."""
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="EGP")
    date = Column(DateTime, default=datetime.utcnow)
    
    paid_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Can be null if paid from wallet
    payer = relationship("User", back_populates="expenses_paid")

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group", back_populates="expenses")

    # If paid by a person, it generates debts. If from wallet, it generates wallet transactions.
    debts = relationship("Debt", back_populates="expense", cascade="all, delete-orphan")

class Debt(Base):
    """Represents a debt owed by one user to another for a specific expense."""
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
    """Represents a single partial (or full) payment made towards a debt."""
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    
    debt_id = Column(Integer, ForeignKey("debts.id"))
    debt = relationship("Debt", back_populates="payments")

# --- NEW TABLE: WalletTransaction ---
class WalletTransaction(Base):
    """Represents a transaction (deposit or expense) for a group's wallet."""
    __tablename__ = "wallet_transactions"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False) # Positive for deposit, negative for expense
    type = Column(Enum(WalletTransactionType), nullable=False)
    description = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # The user who initiated the transaction
    
    group = relationship("Group", back_populates="wallet_transactions")
    user = relationship("User", back_populates="wallet_transactions")
