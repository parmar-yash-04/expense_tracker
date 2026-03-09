import os
import logging
from typing import Optional
import redis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info(f"Connected to Redis at {REDIS_URL}")
        except redis.ConnectionError as e:
            logger.warning(f"Could not connect to Redis: {e}. Rate limiting will be disabled.")
            _redis_client = None
    return _redis_client


def close_redis_connection():
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None


class RateLimiter:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or get_redis_client()
    
    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        if not self.redis:
            return False, 0
        
        try:
            current = self.redis.get(key)
            if current is None:
                self.redis.setex(key, window_seconds, 1)
                return False, max_requests - 1
            
            current_count = int(current)
            if current_count >= max_requests:
                ttl = self.redis.ttl(key)
                return True, max(0, max_requests - current_count)
            
            self.redis.incr(key)
            return False, max(0, max_requests - current_count - 1)
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            return False, 0
    
    def get_remaining(self, key: str, max_requests: int) -> int:
        if not self.redis:
            return max_requests
        
        try:
            current = self.redis.get(key)
            if current is None:
                return max_requests
            return max(0, max_requests - int(current))
        except redis.RedisError:
            return 0
    
    def get_ttl(self, key: str) -> int:
        if not self.redis:
            return 0
        
        try:
            ttl = self.redis.ttl(key)
            return max(0, ttl) if ttl > 0 else 0
        except redis.RedisError:
            return 0
    
    def reset(self, key: str) -> bool:
        if not self.redis:
            return False
        
        try:
            self.redis.delete(key)
            return True
        except redis.RedisError:
            return False


rate_limiter = RateLimiter()
