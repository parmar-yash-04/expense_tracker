import logging

security_logger = logging.getLogger("security")

def log_failed_authentication(username: str, ip_address: str, reason: str = "invalid_credentials"):
    security_logger.warning(
        f"Failed authentication attempt | username={username} | ip={ip_address} | reason={reason}"
    )

def log_unauthorized_access(ip_address: str, path: str, method: str, user_id: str = "unknown"):
    security_logger.warning(
        f"Unauthorized access attempt | user_id={user_id} | path={path} | method={method} | ip={ip_address}"
    )

def log_rate_limit_violation(ip_address: str, endpoint: str, limit: int, window: int):
    security_logger.warning(
        f"Rate limit violation | ip={ip_address} | endpoint={endpoint} | limit={limit} | window_seconds={window}"
    )
