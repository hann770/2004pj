from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas, crud, auth, services
from app.database import SessionLocal, engine
from app.auth import get_current_user

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Manager API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 依赖项 - 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 认证路由
@app.post("/auth/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/auth/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user or not auth.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = auth.create_access_token(data={"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

# 用户路由
@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# 群组路由
@app.post("/groups", response_model=schemas.Group)
def create_group(
    group: schemas.GroupCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_group(db=db, group=group, user_id=current_user.id)

@app.get("/groups", response_model=List[schemas.Group])
def read_groups(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_user_groups(db=db, user_id=current_user.id, skip=skip, limit=limit)

@app.get("/groups/{group_id}", response_model=schemas.Group)
def read_group(
    group_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    group = crud.get_group(db, group_id=group_id)
    if not group or current_user.id not in [m.id for m in group.members]:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@app.post("/groups/{group_id}/members")
def add_member(
    group_id: int, 
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    group = crud.get_group(db, group_id=group_id)
    if not group or group.created_by != current_user.id:
        raise HTTPException(status_code=404, detail="Group not found or not admin")
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return crud.add_member_to_group(db=db, group_id=group_id, user_id=user_id)

# 费用路由
@app.post("/expenses", response_model=schemas.Expense)
def create_expense(
    expense: schemas.ExpenseCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 检查用户是否在群组中
    group = crud.get_group(db, group_id=expense.group_id)
    if not group or current_user.id not in [m.id for m in group.members]:
        raise HTTPException(status_code=404, detail="Group not found or not a member")
    
    return crud.create_expense(db=db, expense=expense, paid_by=current_user.id)

@app.get("/expenses", response_model=List[schemas.Expense])
def read_expenses(
    group_id: int = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if group_id:
        # 检查用户是否在群组中
        group = crud.get_group(db, group_id=group_id)
        if not group or current_user.id not in [m.id for m in group.members]:
            raise HTTPException(status_code=404, detail="Group not found or not a member")
        return crud.get_group_expenses(db=db, group_id=group_id, skip=skip, limit=limit)
    else:
        return crud.get_user_expenses(db=db, user_id=current_user.id, skip=skip, limit=limit)

# 余额计算路由
@app.get("/groups/{group_id}/balances")
def get_balances(
    group_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    group = crud.get_group(db, group_id=group_id)
    if not group or current_user.id not in [m.id for m in group.members]:
        raise HTTPException(status_code=404, detail="Group not found or not a member")
    
    balances = services.calculate_balances(db, group_id)
    simplified = services.simplify_balances(balances)
    
    return {"balances": balances, "simplified": simplified}

# 支付路由
@app.post("/payments", response_model=schemas.Payment)
def create_payment(
    payment: schemas.PaymentCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if payment.from_user != current_user.id:
        raise HTTPException(status_code=403, detail="Can only create payments from yourself")
    
    return crud.create_payment(db=db, payment=payment)