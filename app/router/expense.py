from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from decimal import Decimal
from datetime import date, datetime
from app.database import get_db
from app.models import User, Expense, Category, Budget
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse, SummaryResponse
from app.oauth2 import get_current_user, get_current_user_id
from app.ai_model import predict_category

router = APIRouter(prefix="/api", tags=["expenses"])


def create_expense(
    expense_data: ExpenseCreate,
    user_id: int,
    db: Session
) -> Expense:
    category = db.query(Category).filter(Category.id == expense_data.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found"
        )
    
    if expense_data.transaction_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction date is required"
        )
    
    new_expense = Expense(
        user_id=user_id,
        category_id=expense_data.category_id,
        amount=expense_data.amount,
        merchant=expense_data.merchant,
        description=expense_data.description,
        transaction_date=expense_data.transaction_date
    )
    
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    return new_expense

@router.post("/expense", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def add_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_expense = create_expense(expense, current_user.id, db)
    return new_expense
    
def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    user_id: int,
    db: Session
) -> Expense:
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    if expense_data.category_id is not None:
        category = db.query(Category).filter(Category.id == expense_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found"
            )
        expense.category_id = expense_data.category_id
    
    if expense_data.amount is not None:
        expense.amount = expense_data.amount
    
    if expense_data.merchant is not None:
        expense.merchant = expense_data.merchant
    
    if expense_data.description is not None:
        expense.description = expense_data.description
    
    if expense_data.transaction_date is not None:
        expense.transaction_date = expense_data.transaction_date
    
    db.commit()
    db.refresh(expense)
    
    return expense


@router.put("/expense/{expense_id}", response_model=ExpenseResponse)
def update_expense_endpoint(
    expense_id: int,
    expense: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated_expense = update_expense(expense_id, expense, current_user.id, db)
    return updated_expense


def delete_expense(
    expense_id: int,
    user_id: int,
    db: Session
) -> bool:
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()
    
    if not expense:
        return False
    
    db.delete(expense)
    db.commit()
    
    return True


@router.delete("/expense/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense_endpoint(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted = delete_expense(expense_id, current_user.id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    return None

@router.get("/expenses", response_model=List[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date (transaction_date >=)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (transaction_date <=)"),
    min_amount: Optional[Decimal] = Query(None, description="Filter by minimum amount"),
    max_amount: Optional[Decimal] = Query(None, description="Filter by maximum amount"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    query = db.query(Expense).filter(Expense.user_id == current_user.id)
    
    if category_id is not None:
        query = query.filter(Expense.category_id == category_id)
    
    if start_date is not None:
        query = query.filter(Expense.transaction_date >= start_date)
    
    if end_date is not None:
        query = query.filter(Expense.transaction_date <= end_date)
    
    if min_amount is not None:
        query = query.filter(Expense.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(Expense.amount <= max_amount)
    
    expenses = query.order_by(
        Expense.transaction_date.desc(),
        Expense.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return expenses


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date")
):
    query = db.query(Expense).filter(Expense.user_id == current_user.id)
    
    if start_date is not None:
        query = query.filter(Expense.transaction_date >= start_date)
    
    if end_date is not None:
        query = query.filter(Expense.transaction_date <= end_date)
    
    expenses = query.all()
    
    total_spending = sum(float(expense.amount) for expense in expenses)
    total_transactions = len(expenses)
    average_transaction = total_spending / total_transactions if total_transactions > 0 else 0
    
    category_data = {}
    for expense in expenses:
        cat_id = expense.category_id
        if cat_id not in category_data:
            category_data[cat_id] = {'total': 0, 'count': 0}
        category_data[cat_id]['total'] += float(expense.amount)
        category_data[cat_id]['count'] += 1
    
    categories = db.query(Category).filter(Category.id.in_(category_data.keys())).all()
    cat_map = {c.id: c.name for c in categories}
    
    category_breakdown = []
    for cat_id, data in category_data.items():
        category_breakdown.append({
            'category_id': cat_id,
            'category_name': cat_map.get(cat_id, 'Unknown'),
            'total_amount': data['total'],
            'transaction_count': data['count'],
            'percentage': (data['total'] / total_spending * 100) if total_spending > 0 else 0
        })
    
    monthly_data = {}
    for expense in expenses:
        key = (expense.transaction_date.month, expense.transaction_date.year)
        if key not in monthly_data:
            monthly_data[key] = {'total': 0, 'count': 0, 'categories': {}}
        monthly_data[key]['total'] += float(expense.amount)
        monthly_data[key]['count'] += 1
        
        cat_id = expense.category_id
        if cat_id not in monthly_data[key]['categories']:
            monthly_data[key]['categories'][cat_id] = 0
        monthly_data[key]['categories'][cat_id] += float(expense.amount)
    
    monthly_spend = []
    for (month, year), data in sorted(monthly_data.items()):
        cat_breakdown = []
        for cat_id, total in data['categories'].items():
            cat_breakdown.append({
                'category_id': cat_id,
                'category_name': cat_map.get(cat_id, 'Unknown'),
                'total_amount': total,
                'transaction_count': 0,
                'percentage': (total / data['total'] * 100) if data['total'] > 0 else 0
            })
        monthly_spend.append({
            'month': month,
            'year': year,
            'total_amount': data['total'],
            'transaction_count': data['count'],
            'categories': cat_breakdown
        })
    
    period_start = start_date if start_date else (min(e.transaction_date for e in expenses) if expenses else date.today())
    period_end = end_date if end_date else (max(e.transaction_date for e in expenses) if expenses else date.today())
    
    return SummaryResponse(
        user_id=int(current_user.id),
        total_spending=total_spending,
        total_transactions=total_transactions,
        average_transaction=average_transaction,
        category_breakdown=category_breakdown,
        monthly_spend=monthly_spend,
        budget_variance=[],
        period_start=period_start,
        period_end=period_end
    )


@router.get("/summary/categories", response_model=list)
def get_category_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date")
):
    query = db.query(Expense).filter(Expense.user_id == current_user.id)
    
    if start_date is not None:
        query = query.filter(Expense.transaction_date >= start_date)
    
    if end_date is not None:
        query = query.filter(Expense.transaction_date <= end_date)
    
    expenses = query.all()
    
    if not expenses:
        return []
    
    total_spending = sum(float(expense.amount) for expense in expenses)
    
    category_data = {}
    for expense in expenses:
        cat_id = expense.category_id
        if cat_id not in category_data:
            category_data[cat_id] = {'total': 0, 'count': 0}
        category_data[cat_id]['total'] += float(expense.amount)
        category_data[cat_id]['count'] += 1
    
    categories = db.query(Category).filter(Category.id.in_(category_data.keys())).all()
    cat_map = {c.id: c.name for c in categories}
    
    breakdown = []
    for cat_id, data in sorted(category_data.items(), key=lambda x: x[1]['total'], reverse=True):
        breakdown.append({
            'category_id': cat_id,
            'category_name': cat_map.get(cat_id, 'Unknown'),
            'total_amount': data['total'],
            'transaction_count': data['count'],
            'percentage': round((data['total'] / total_spending * 100), 2) if total_spending > 0 else 0
        })
    
    return breakdown


@router.get("/summary/budgets", response_model=list)
def calculate_budget_variance(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, description="Year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.month == month,
        Budget.year == year
    ).all()
    
    if not budgets:
        return []
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.transaction_date >= start_date,
        Expense.transaction_date < end_date
    ).all()
    
    expense_by_category = {}
    for expense in expenses:
        cat_id = expense.category_id
        if cat_id not in expense_by_category:
            expense_by_category[cat_id] = 0
        expense_by_category[cat_id] += float(expense.amount)
    
    categories = db.query(Category).filter(
        Category.id.in_([b.category_id for b in budgets])
    ).all()
    cat_map = {c.id: c.name for c in categories}
    
    variance_list = []
    for budget in budgets:
        spent = expense_by_category.get(budget.category_id, 0)
        limit = float(budget.limit_amount)
        remaining = limit - spent
        percentage_used = (spent / limit * 100) if limit > 0 else 0
        is_over_budget = spent > limit
        
        variance_list.append({
            'budget_id': budget.id,
            'category_name': cat_map.get(budget.category_id, 'Unknown'),
            'limit_amount': limit,
            'spent_amount': spent,
            'remaining_amount': remaining,
            'percentage_used': round(percentage_used, 2),
            'is_over_budget': is_over_budget
        })
    
    variance_list.sort(key=lambda x: x['percentage_used'], reverse=True)
    
    return variance_list


@router.get("/summary/budget-variance", response_model=list)
def calculate_budget_variance_v2(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, description="Year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.month == month,
        Budget.year == year
    ).all()
    
    if not budgets:
        return []
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.transaction_date >= start_date,
        Expense.transaction_date < end_date
    ).all()
    
    expense_by_category = {}
    for expense in expenses:
        cat_id = expense.category_id
        if cat_id not in expense_by_category:
            expense_by_category[cat_id] = 0
        expense_by_category[cat_id] += float(expense.amount)
    
    categories = db.query(Category).filter(
        Category.id.in_([b.category_id for b in budgets])
    ).all()
    cat_map = {c.id: c.name for c in categories}
    
    variance_list = []
    for budget in budgets:
        spent = expense_by_category.get(budget.category_id, 0)
        limit = float(budget.limit_amount)
        remaining = limit - spent
        percentage_used = (spent / limit * 100) if limit > 0 else 0
        is_over_budget = spent > limit
        
        variance_list.append({
            'budget_id': budget.id,
            'category_name': cat_map.get(budget.category_id, 'Unknown'),
            'limit_amount': limit,
            'spent_amount': spent,
            'remaining_amount': remaining,
            'percentage_used': round(percentage_used, 2),
            'is_over_budget': is_over_budget
        })
    
    variance_list.sort(key=lambda x: x['percentage_used'], reverse=True)
    
    return variance_list
