from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    phone_number: str
    is_verified: bool

class Token(BaseModel):
    access_token: str
    token_type: str


class ExpenseCreate(BaseModel):
    amount: float
    description: str
    category: Optional[str] = None
    date: date


class ExpenseResponse(BaseModel):
    id: int
    amount: float
    description: str
    category: str
    date: date
    user_id: int

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    total_spending: float
    transactions: int
