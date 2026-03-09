import re
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, EmailStr, field_validator, model_validator, Field
from datetime import datetime, date
from typing import Optional
from datetime import date as date_type


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ExpenseCreate(BaseModel):
    category_id: int
    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    merchant: Optional[str] = None
    description: Optional[str] = None
    transaction_date: date_type

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

    @field_validator('transaction_date')
    @classmethod
    def validate_transaction_date(cls, v: date_type) -> date_type:
        if v > date.today():
            raise ValueError('Transaction date cannot be in the future')
        return v


class ExpenseUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    merchant: Optional[str] = None
    description: Optional[str] = None
    transaction_date: Optional[date_type] = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= 0:
            raise ValueError('Amount must be positive')
        return v

    @field_validator('transaction_date')
    @classmethod
    def validate_transaction_date(cls, v: Optional[date_type]) -> Optional[date_type]:
        if v is not None and v > date.today():
            raise ValueError('Transaction date cannot be in the future')
        return v


class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    amount: Decimal
    merchant: Optional[str] = None
    description: Optional[str] = None
    transaction_date: date_type
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) < 1 or len(v) > 50:
            raise ValueError('Category name must be between 1 and 50 characters')
        return v

    @field_validator('color')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color must be a valid hex color code (e.g., #FF0000)')
        return v


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetCreate(BaseModel):
    category_id: int
    limit_amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    month: int
    year: int

    @field_validator('limit_amount')
    @classmethod
    def validate_limit_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Limit amount must be positive')
        return v

    @field_validator('month')
    @classmethod
    def validate_month(cls, v: int) -> int:
        if v < 1 or v > 12:
            raise ValueError('Month must be between 1 and 12')
        return v

    @field_validator('year')
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 2000:
            raise ValueError('Year must be 2000 or greater')
        return v


class BudgetResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    limit_amount: Decimal
    month: int
    year: int

    class Config:
        from_attributes = True


class CategoryBreakdown(BaseModel):
    category_id: int
    category_name: str
    total_amount: Decimal
    transaction_count: int
    percentage: float


class MonthlySpend(BaseModel):
    month: int
    year: int
    total_amount: Decimal
    transaction_count: int
    categories: list[CategoryBreakdown]


class BudgetVariance(BaseModel):
    budget_id: int
    category_name: str
    limit_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    percentage_used: float
    is_over_budget: bool


class SummaryResponse(BaseModel):
    user_id: int
    total_spending: Decimal
    total_transactions: int
    average_transaction: Decimal
    category_breakdown: list[CategoryBreakdown]
    monthly_spend: list[MonthlySpend]
    budget_variance: list[BudgetVariance]
    period_start: date_type
    period_end: date_type
