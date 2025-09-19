from sqlalchemy.orm import Session
from app import crud
from typing import Dict, List

def calculate_balances(db: Session, group_id: int) -> Dict[int, float]:
    """计算群组中所有成员的余额"""
    expenses = crud.get_group_expenses(db, group_id)
    group = crud.get_group(db, group_id)
    
    balances = {member.id: 0.0 for member in group.members}
    
    # 处理费用
    for expense in expenses:
        payer_id = expense.paid_by
        amount = expense.amount
        
        # 支付者收到全额
        balances[payer_id] += amount
        
        # 处理份额
        for share in expense.shares:
            user_id = share.user_id
            share_amount = share.amount
            balances[user_id] -= share_amount
    
    return balances

def simplify_balances(balances: Dict[int, float]) -> List[Dict]:
    """简化余额计算"""
    creditors = []
    debtors = []
    
    # 分离债权人和债务人
    for user_id, balance in balances.items():
        if balance > 0:
            creditors.append({"user_id": user_id, "amount": balance})
        elif balance < 0:
            debtors.append({"user_id": user_id, "amount": -balance})
    
    # 排序
    creditors.sort(key=lambda x: x["amount"], reverse=True)
    debtors.sort(key=lambda x: x["amount"], reverse=True)
    
    transactions = []
    i = j = 0
    
    while i < len(creditors) and j < len(debtors):
        min_amount = min(creditors[i]["amount"], debtors[j]["amount"])
        
        transactions.append({
            "from_user_id": debtors[j]["user_id"],
            "to_user_id": creditors[i]["user_id"],
            "amount": min_amount
        })
        
        creditors[i]["amount"] -= min_amount
        debtors[j]["amount"] -= min_amount
        
        if creditors[i]["amount"] == 0:
            i += 1
        if debtors[j]["amount"] == 0:
            j += 1
    
    return transactions