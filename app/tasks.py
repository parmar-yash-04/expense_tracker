import os
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import User, Expense, Category, Budget

logger = logging.getLogger(__name__)


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    finally:
        pass


@celery_app.task(name="app.tasks.send_monthly_report")
def send_monthly_report(user_id: int, month: int, year: int) -> Dict[str, Any]:
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        expenses = db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.transaction_date >= start_date,
            Expense.transaction_date < end_date
        ).all()
        
        total_spending = sum(float(expense.amount) for expense in expenses)
        total_transactions = len(expenses)
        average_transaction = total_spending / total_transactions if total_transactions > 0 else 0
        
        category_data = {}
        for expense in expenses:
            cat_id = expense.category_id
            if cat_id not in category_data:
                category_data[cat_id] = {"total": 0, "count": 0}
            category_data[cat_id]["total"] += float(expense.amount)
            category_data[cat_id]["count"] += 1
        
        categories = db.query(Category).filter(Category.id.in_(category_data.keys())).all()
        cat_map = {c.id: c.name for c in categories}
        
        category_breakdown = []
        for cat_id, data in category_data.items():
            category_breakdown.append({
                "category_name": cat_map.get(cat_id, "Unknown"),
                "total_amount": round(data["total"], 2),
                "transaction_count": data["count"],
                "percentage": round((data["total"] / total_spending * 100), 2) if total_spending > 0 else 0
            })
        
        category_breakdown.sort(key=lambda x: x["total_amount"], reverse=True)
        
        budgets = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.month == month,
            Budget.year == year
        ).all()
        
        expense_by_category = {}
        for expense in expenses:
            cat_id = expense.category_id
            if cat_id not in expense_by_category:
                expense_by_category[cat_id] = 0
            expense_by_category[cat_id] += float(expense.amount)
        
        budget_variance = []
        for budget in budgets:
            spent = expense_by_category.get(budget.category_id, 0)
            limit = float(budget.limit_amount)
            remaining = limit - spent
            percentage_used = (spent / limit * 100) if limit > 0 else 0
            is_over_budget = spent > limit
            
            budget_variance.append({
                "category_name": cat_map.get(budget.category_id, "Unknown"),
                "limit_amount": round(limit, 2),
                "spent_amount": round(spent, 2),
                "remaining_amount": round(remaining, 2),
                "percentage_used": round(percentage_used, 2),
                "is_over_budget": is_over_budget
            })
        
        month_name = date(year, month, 1).strftime("%B")
        
        report_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            },
            "period": {
                "month": month,
                "year": year,
                "month_name": month_name
            },
            "summary": {
                "total_spending": round(total_spending, 2),
                "total_transactions": total_transactions,
                "average_transaction": round(average_transaction, 2)
            },
            "category_breakdown": category_breakdown,
            "budget_variance": budget_variance,
            "generated_at": date.today().isoformat()
        }
        
        logger.info(f"Generated monthly report for user {user_id}: {month_name} {year}")
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error generating monthly report: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.cleanup_old_sessions")
def cleanup_old_sessions() -> Dict[str, str]:
    logger.info("Running session cleanup task")
    return {"status": "completed", "message": "Session cleanup task placeholder"}


@celery_app.task(name="app.tasks.send_budget_alert")
def send_budget_alert(user_id: int, category_id: int, month: int, year: int, percentage_used: float) -> Dict[str, Any]:
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        category = db.query(Category).filter(Category.id == category_id).first()
        
        if not user or not category:
            return {"error": "User or category not found"}
        
        alert_data = {
            "user_id": user_id,
            "email": user.email,
            "category": category.name,
            "month": month,
            "year": year,
            "percentage_used": percentage_used,
            "message": f"Budget alert: You've used {percentage_used:.1f}% of your {category.name} budget for {date(year, month, 1).strftime('%B %Y')}"
        }
        
        logger.info(f"Budget alert sent to user {user_id} for category {category.name}")
        
        return alert_data
        
    except Exception as e:
        logger.error(f"Error sending budget alert: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.schedule_all_monthly_reports")
def schedule_all_monthly_reports() -> Dict[str, Any]:
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)
    prev_month = first_day_of_month - timedelta(days=1)
    month = prev_month.month
    year = prev_month.year
    
    db = get_db()
    try:
        users = db.query(User).all()
        
        results = []
        for user in users:
            result = send_monthly_report.delay(user.id, month, year)
            results.append({
                "user_id": user.id,
                "username": user.username,
                "task_id": result.id
            })
        
        logger.info(f"Scheduled monthly reports for {len(users)} users for {date(year, month, 1).strftime('%B %Y')}")
        
        return {
            "status": "scheduled",
            "month": month,
            "year": year,
            "users_count": len(users),
            "tasks": results
        }
        
    except Exception as e:
        logger.error(f"Error scheduling monthly reports: {e}")
        return {"error": str(e)}
    finally:
        db.close()
