from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, TIMESTAMP
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    expenses = relationship("Expense", back_populates="user")
    username = Column(String, name="user_name", index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=True)
    create_at = Column(TIMESTAMP, default=datetime.utcnow)


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    description = Column(String)
    category = Column(String)
    date = Column(Date)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    user = relationship("User", back_populates="expenses")
