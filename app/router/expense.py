from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Expense
from app.schemas import ExpenseCreate, ExpenseResponse, SummaryResponse
from app.oauth2 import get_current_user
from app.ai_model import predict_category

router = APIRouter(prefix="/api", tags=["expenses"])

@router.post("/expense", response_model=dict)
def add_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = expense.category if expense.category else predict_category(expense.description)
    
    new_expense = Expense(
        amount=expense.amount,
        description=expense.description,
        category=category,
        date=expense.date,
        user_id=current_user.user_id
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return {"message": "Expense added", "category": category}


@router.get("/expenses", response_model=List[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expenses = db.query(Expense).filter(Expense.user_id == current_user.user_id).all()
    return expenses


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expenses = db.query(Expense).filter(Expense.user_id == current_user.user_id).all()
    total_spending = sum(expense.amount for expense in expenses)
    transactions = len(expenses)
    return {"total_spending": total_spending, "transactions": transactions}
