from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import User, Category, Budget
from app.schemas import BudgetCreate, BudgetResponse
from app.oauth2 import get_current_user

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


def create_budget(
    budget_data: BudgetCreate,
    user_id: int,
    db: Session
) -> Budget:
    category = db.query(Category).filter(Category.id == budget_data.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found"
        )
    
    existing = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category_id == budget_data.category_id,
        Budget.month == budget_data.month,
        Budget.year == budget_data.year
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget for this category, month, and year already exists"
        )
    
    new_budget = Budget(
        user_id=user_id,
        category_id=budget_data.category_id,
        limit_amount=budget_data.limit_amount,
        month=budget_data.month,
        year=budget_data.year
    )
    
    try:
        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget for this category, month, and year already exists"
        )
    
    return new_budget


def get_budgets(user_id: int, db: Session) -> List[Budget]:
    return db.query(Budget).filter(Budget.user_id == user_id).all()


def get_budget_by_id(budget_id: int, user_id: int, db: Session) -> Budget:
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    return budget


def update_budget(
    budget_id: int,
    budget_data: BudgetCreate,
    user_id: int,
    db: Session
) -> Budget:
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    category = db.query(Category).filter(Category.id == budget_data.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found"
        )
    
    existing = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category_id == budget_data.category_id,
        Budget.month == budget_data.month,
        Budget.year == budget_data.year,
        Budget.id != budget_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget for this category, month, and year already exists"
        )
    
    budget.category_id = budget_data.category_id
    budget.limit_amount = budget_data.limit_amount
    budget.month = budget_data.month
    budget.year = budget_data.year
    
    db.commit()
    db.refresh(budget)
    
    return budget


def delete_budget(budget_id: int, user_id: int, db: Session) -> bool:
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()
    
    if not budget:
        return False
    
    db.delete(budget)
    db.commit()
    
    return True


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget_endpoint(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_budget(budget, current_user.id, db)


@router.get("", response_model=List[BudgetResponse])
def get_budgets_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_budgets(current_user.id, db)


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget_endpoint(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_budget_by_id(budget_id, current_user.id, db)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget_endpoint(
    budget_id: int,
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_budget(budget_id, budget, current_user.id, db)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget_endpoint(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted = delete_budget(budget_id, current_user.id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    return None
