import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL"))
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL"))

celery_app = Celery(
    "expense_tracker",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    beat_schedule={
        "schedule-monthly-reports": {
            "task": "app.tasks.schedule_all_monthly_reports",
            "schedule": crontab(minute="0", hour="0", day_of_month="1"),
        },
    },
)
