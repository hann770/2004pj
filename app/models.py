from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# 群组成员关联表
group_members = Table(
    'group_members',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    groups = relationship("Group", secondary=group_members, back_populates="members")
    expenses_paid = relationship("Expense", back_populates="paid_by_user")
    expense_shares = relationship("ExpenseShare", back_populates="user")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    members = relationship("User", secondary=group_members, back_populates="groups")
    expenses = relationship("Expense", back_populates="group")

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    amount = Column(Float)
    paid_by = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    split_type = Column(String, default="EQUAL")  # EQUAL, EXACT, PERCENTAGE, SHARES
    date = Column(DateTime(timezone=True), server_default=func.now())
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String, nullable=True)  # DAILY, WEEKLY, MONTHLY
    
    # 关系
    paid_by_user = relationship("User", back_populates="expenses_paid")
    group = relationship("Group", back_populates="expenses")
    shares = relationship("ExpenseShare", back_populates="expense")

class ExpenseShare(Base):
    __tablename__ = "expense_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    
    # 关系
    expense = relationship("Expense", back_populates="shares")
    user = relationship("User", back_populates="expense_shares")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    from_user = Column(Integer, ForeignKey("users.id"))
    to_user = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    description = Column(String)
    date = Column(DateTime(timezone=True), server_default=func.now())