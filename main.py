from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.router import auth, expense, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Expense Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(expense.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "AI Expense Tracker API is running"}