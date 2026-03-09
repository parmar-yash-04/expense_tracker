from datetime import datetime
from typing import Optional


def get_utcnow() -> datetime:
    return datetime.utcnow()


def ensure_timestamp(value: Optional[datetime]) -> datetime:
    return value if value is not None else get_utcnow()


def preserve_created_at(obj, updates: dict) -> dict:
    if hasattr(obj, 'created_at') and 'created_at' not in updates:
        updates['created_at'] = obj.created_at
    return updates
