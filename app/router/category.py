from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Category
from app.schemas import CategoryCreate, CategoryResponse
from app.oauth2 import get_current_user

router = APIRouter(prefix="/api/categories", tags=["categories"])


def create_category(
    category_data: CategoryCreate,
    db: Session
) -> Category:
    existing = db.query(Category).filter(Category.name == category_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists"
        )
    
    new_category = Category(
        name=category_data.name,
        description=category_data.description,
        color=category_data.color
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category


def get_categories(db: Session) -> List[Category]:
    return db.query(Category).order_by(Category.name).all()


def get_category_by_id(category_id: int, db: Session) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


def update_category(
    category_id: int,
    category_data: CategoryCreate,
    db: Session
) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    if category_data.name != category.name:
        existing = db.query(Category).filter(Category.name == category_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name already exists"
            )
        category.name = category_data.name
    
    category.description = category_data.description
    category.color = category_data.color
    
    db.commit()
    db.refresh(category)
    
    return category


def delete_category(category_id: int, db: Session) -> bool:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return False
    
    db.delete(category)
    db.commit()
    
    return True


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category_endpoint(
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    return create_category(category, db)


@router.get("", response_model=List[CategoryResponse])
def get_categories_endpoint(db: Session = Depends(get_db)):
    return get_categories(db)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    return get_category_by_id(category_id, db)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category_endpoint(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    return update_category(category_id, category, db)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    deleted = delete_category(category_id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return None
