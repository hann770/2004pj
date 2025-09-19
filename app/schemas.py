from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    created_by: int
    created_at: datetime
    members: List[User] = []
    
    class Config:
        orm_mode = True

class ExpenseShareBase(BaseModel):
    user_id: int
    amount: float

class ExpenseBase(BaseModel):
    description: str
    amount: float
    group_id: int
    split_type: str = "EQUAL"

class ExpenseCreate(ExpenseBase):
    shares: Optional[List[ExpenseShareBase]] = None

class Expense(ExpenseBase):
    id: int
    paid_by: int
    date: datetime
    
    class Config:
        orm_mode = True

class PaymentBase(BaseModel):
    from_user: int
    to_user: int
    amount: float
    group_id: Optional[int] = None
    description: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: int
    date: datetime
    
    class Config:
        orm_mode = True