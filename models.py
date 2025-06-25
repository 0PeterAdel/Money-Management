# models.py

from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# # This is the table to link users and groups (many to many)
group_members_table = Table('group_members', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # User relationship with the groups to which he belongs
    groups = relationship("Group",
                            secondary=group_members_table,
                            back_populates="members")
    
    # User relationship to expenses paid
    expenses_paid = relationship("Expense", back_populates="payer")


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Group relationship with members
    members = relationship("User",
                            secondary=group_members_table,
                            back_populates="groups")
    
    # The group's relationship to its expenses
    expenses = relationship("Expense", back_populates="group")


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="EGP")
    date = Column(DateTime, default=datetime.utcnow)
    
    # Who paid this expense (one-to-many relationship with the user)
    paid_by_user_id = Column(Integer, ForeignKey("users.id"))
    payer = relationship("User", back_populates="expenses_paid")

    # Which group does this expense belong to? (It can be blank if it is personal expense)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group", back_populates="expenses")

    # All debts associated with this expense
    debts = relationship("Debt", back_populates="expense", cascade="all, delete-orphan")


class Debt(Base):
    __tablename__ = "debts"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    is_settled = Column(Boolean, default=False)

    # Who does this debt belong to? (Relationship with the debtor user)
    owes_user_id = Column(Integer, ForeignKey("users.id"))
    # To whom the debt should be paid (relationship with the creditor user)
    owed_to_user_id = Column(Integer, ForeignKey("users.id"))

    # Which expense does this debt belong to? (Relationship with expense)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    expense = relationship("Expense", back_populates="debts")

    # For easy access to user data
    debtor = relationship("User", foreign_keys=[owes_user_id])
    creditor = relationship("User", foreign_keys=[owed_to_user_id])