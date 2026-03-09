import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Expense Tracker")


class EmailService:
    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.username = SMTP_USERNAME
        self.password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
        self.from_name = SMTP_FROM_NAME
    
    def _create_message(self, to_email: str, subject: str, body: str, html: Optional[str] = None) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        
        text_part = MIMEText(body, "plain")
        msg.attach(text_part)
        
        if html:
            html_part = MIMEText(html, "html")
            msg.attach(html_part)
        
        return msg
    
    def send_email(self, to_email: str, subject: str, body: str, html: Optional[str] = None) -> bool:
        if not self.username or not self.password:
            logger.warning("Email not configured. SMTP_USERNAME or SMTP_PASSWORD not set.")
            return False
        
        try:
            msg = self._create_message(to_email, subject, body, html)
            
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False


email_service = EmailService()


def send_expense_report_email(
    to_email: str,
    username: str,
    report_data: Dict[str, Any]
) -> bool:
    period = report_data.get("period", {})
    month_name = period.get("month_name", "")
    year = period.get("year", "")
    
    summary = report_data.get("summary", {})
    total_spending = summary.get("total_spending", 0)
    total_transactions = summary.get("total_transactions", 0)
    
    subject = f"Your Expense Report for {month_name} {year}"
    
    body = f"""Hi {username},

Here's your expense report for {month_name} {year}:

Summary:
- Total Spending: ${total_spending:.2f}
- Total Transactions: {total_transactions}

"""

    category_breakdown = report_data.get("category_breakdown", [])
    if category_breakdown:
        body += "Category Breakdown:\n"
        for cat in category_breakdown:
            body += f"  - {cat['category_name']}: ${cat['total_amount']:.2f} ({cat['percentage']:.1f}%)\n"
        body += "\n"

    budget_variance = report_data.get("budget_variance", [])
    if budget_variance:
        body += "Budget Status:\n"
        for budget in budget_variance:
            status = "OVER BUDGET" if budget['is_over_budget'] else "Under budget"
            body += f"  - {budget['category_name']}: ${budget['spent_amount']:.2f} / ${budget['limit_amount']:.2f} ({status})\n"

    body += f"""
Thank you for using Expense Tracker!

Best regards,
The Expense Tracker Team
"""

    html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Your Expense Report for {month_name} {year}</h2>
    
    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h3 style="margin-top: 0;">Summary</h3>
        <p><strong>Total Spending:</strong> ${total_spending:.2f}</p>
        <p><strong>Total Transactions:</strong> {total_transactions}</p>
    </div>
"""

    if category_breakdown:
        html += """
    <h3>Category Breakdown</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background-color: #eee;">
            <th style="padding: 8px; text-align: left;">Category</th>
            <th style="padding: 8px; text-align: right;">Amount</th>
            <th style="padding: 8px; text-align: right;">%</th>
        </tr>
"""
        for cat in category_breakdown:
            html += f"""
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;">{cat['category_name']}</td>
            <td style="padding: 8px; text-align: right;">${cat['total_amount']:.2f}</td>
            <td style="padding: 8px; text-align: right;">{cat['percentage']:.1f}%</td>
        </tr>
"""
        html += "    </table>"

    if budget_variance:
        html += """
    <h3>Budget Status</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background-color: #eee;">
            <th style="padding: 8px; text-align: left;">Category</th>
            <th style="padding: 8px; text-align: right;">Spent</th>
            <th style="padding: 8px; text-align: right;">Limit</th>
            <th style="padding: 8px; text-align: right;">Status</th>
        </tr>
"""
        for budget in budget_variance:
            status_color = "#d32f2f" if budget['is_over_budget'] else "#388e3c"
            status_text = "OVER" if budget['is_over_budget'] else "OK"
            html += f"""
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px;">{budget['category_name']}</td>
            <td style="padding: 8px; text-align: right;">${budget['spent_amount']:.2f}</td>
            <td style="padding: 8px; text-align: right;">${budget['limit_amount']:.2f}</td>
            <td style="padding: 8px; text-align: right; color: {status_color}; font-weight: bold;">{status_text}</td>
        </tr>
"""
        html += "    </table>"

    html += """
    <p style="margin-top: 30px; color: #666;">
        Thank you for using Expense Tracker!<br>
        Best regards,<br>
        The Expense Tracker Team
    </p>
</body>
</html>
"""

    return email_service.send_email(to_email, subject, body, html)


def send_welcome_email(to_email: str, username: str) -> bool:
    subject = "Welcome to Expense Tracker!"
    
    body = f"""Hi {username},

Welcome to Expense Tracker! We're excited to have you on board.

With Expense Tracker, you can:
- Track your daily expenses
- Create budgets and monitor spending
- Get detailed reports and analytics
- Set up category-based expense tracking

Get started by logging in and adding your first expense!

Best regards,
The Expense Tracker Team
"""

    html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Welcome to Expense Tracker!</h2>
    <p>Hi {username},</p>
    <p>We're excited to have you on board!</p>
    
    <h3>With Expense Tracker, you can:</h3>
    <ul>
        <li>Track your daily expenses</li>
        <li>Create budgets and monitor spending</li>
        <li>Get detailed reports and analytics</li>
        <li>Set up category-based expense tracking</li>
    </ul>
    
    <p>Get started by logging in and adding your first expense!</p>
    
    <p style="margin-top: 30px; color: #666;">
        Best regards,<br>
        The Expense Tracker Team
    </p>
</body>
</html>
"""

    return email_service.send_email(to_email, subject, body, html)


def send_password_reset_email(to_email: str, username: str, reset_token: str) -> bool:
    subject = "Password Reset Request"
    
    body = f"""Hi {username},

You requested a password reset. Use the following token to reset your password:

Token: {reset_token}

This token will expire in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
The Expense Tracker Team
"""

    html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Password Reset Request</h2>
    <p>Hi {username},</p>
    <p>You requested a password reset. Use the following token:</p>
    
    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
        <code style="font-size: 18px; letter-spacing: 2px;">{reset_token}</code>
    </div>
    
    <p>This token will expire in 1 hour.</p>
    
    <p style="color: #666;">If you didn't request this, please ignore this email.</p>
    
    <p style="margin-top: 30px; color: #666;">
        Best regards,<br>
        The Expense Tracker Team
    </p>
</body>
</html>
"""

    return email_service.send_email(to_email, subject, body, html)
