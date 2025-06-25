# models.py - Final Version with Partial Payments Support

from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

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

    # Defines the many-to-many relationship between User and Group
    groups = relationship("Group",
                            secondary=group_members_table,
                            back_populates="members")
    
    # Defines the one-to-many relationship for expenses paid by the user
    expenses_paid = relationship("Expense", back_populates="payer")


class Group(Base):
    """Represents a group of users."""
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Defines the many-to-many relationship between Group and User
    members = relationship("User",
                            secondary=group_members_table,
                            back_populates="groups")
    
    # Defines the one-to-many relationship for expenses belonging to the group
    expenses = relationship("Expense", back_populates="group")


class Expense(Base):
    """Represents a single expense transaction."""
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="EGP")
    date = Column(DateTime, default=datetime.utcnow)
    
    paid_by_user_id = Column(Integer, ForeignKey("users.id"))
    payer = relationship("User", back_populates="expenses_paid")

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group", back_populates="expenses")

    # An expense can generate multiple debts (one for each participant except the payer)
    debts = relationship("Debt", back_populates="expense", cascade="all, delete-orphan")


class Debt(Base):
    """Represents a debt owed by one user to another for a specific expense."""
    __tablename__ = "debts"
    id = Column(Integer, primary_key=True, index=True)
    
    # **MODIFIED**: This field now represents the total original amount of this specific debt portion.
    total_amount = Column(Float, nullable=False) 
    
    is_settled = Column(Boolean, default=False)

    owes_user_id = Column(Integer, ForeignKey("users.id"))     # The user who owes money
    owed_to_user_id = Column(Integer, ForeignKey("users.id"))  # The user who is owed money
    expense_id = Column(Integer, ForeignKey("expenses.id"))

    expense = relationship("Expense", back_populates="debts")
    debtor = relationship("User", foreign_keys=[owes_user_id])
    creditor = relationship("User", foreign_keys=[owed_to_user_id])
    
    # **NEW**: A Debt can now have multiple payments associated with it.
    payments = relationship("Payment", back_populates="debt", cascade="all, delete-orphan")


class Payment(Base):
    """
    **NEW TABLE**: Represents a single partial (or full) payment made towards a debt.
    """
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    
    # Foreign key to link this payment back to the debt it belongs to.
    debt_id = Column(Integer, ForeignKey("debts.id"))
    debt = relationship("Debt", back_populates="payments")
