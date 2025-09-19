from sqlalchemy.orm import Session
from app import models, schemas, auth
from typing import List

# 用户操作
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, name=user.name, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 群组操作
def create_group(db: Session, group: schemas.GroupCreate, user_id: int):
    db_group = models.Group(**group.dict(), created_by=user_id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    # 添加创建者为成员
    add_member_to_group(db, db_group.id, user_id)
    return db_group

def get_group(db: Session, group_id: int):
    return db.query(models.Group).filter(models.Group.id == group_id).first()

def get_user_groups(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Group).join(models.Group.members).filter(
        models.User.id == user_id
    ).offset(skip).limit(limit).all()

def add_member_to_group(db: Session, group_id: int, user_id: int):
    group = get_group(db, group_id)
    user = get_user(db, user_id)
    if user not in group.members:
        group.members.append(user)
        db.commit()
        db.refresh(group)
    return group

# 费用操作
def create_expense(db: Session, expense: schemas.ExpenseCreate, paid_by: int):
    db_expense = models.Expense(**expense.dict(), paid_by=paid_by)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    # 如果是均分，自动创建份额
    if expense.split_type == "EQUAL" and (not expense.shares or len(expense.shares) == 0):
        group = get_group(db, expense.group_id)
        share_amount = expense.amount / len(group.members)
        for member in group.members:
            share = models.ExpenseShare(
                expense_id=db_expense.id, 
                user_id=member.id, 
                amount=share_amount
            )
            db.add(share)
        db.commit()
    # 如果有指定的份额
    elif expense.shares:
        for share in expense.shares:
            db_share = models.ExpenseShare(
                expense_id=db_expense.id, 
                user_id=share.user_id, 
                amount=share.amount
            )
            db.add(db_share)
        db.commit()
    
    db.refresh(db_expense)
    return db_expense

def get_group_expenses(db: Session, group_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Expense).filter(
        models.Expense.group_id == group_id
    ).offset(skip).limit(limit).all()

def get_user_expenses(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Expense).filter(
        models.Expense.paid_by == user_id
    ).offset(skip).limit(limit).all()

# 支付操作
def create_payment(db: Session, payment: schemas.PaymentCreate):
    db_payment = models.Payment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment