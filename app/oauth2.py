from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User
from app.security_logger import log_unauthorized_access
import os
from dotenv import load_dotenv

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
http_bearer = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "0987654321abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except JWTError:
        raise credentials_exception


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), request: Request = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    client_ip = request.client.host if request and request.client else "unknown"
    path = request.url.path if request and request.url else "unknown"
    method = request.method if request else "unknown"
    
    try:
        user_id = verify_token(token, credentials_exception)
    except HTTPException:
        log_unauthorized_access(client_ip, path, method, "invalid_token")
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        log_unauthorized_access(client_ip, path, method, str(user_id))
        raise credentials_exception
    return user


def get_current_user_id(
    credentials = Depends(http_bearer),
    request: Request = None
) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    client_ip = request.client.host if request and request.client else "unknown"
    path = request.url.path if request and request.url else "unknown"
    method = request.method if request else "unknown"
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        log_unauthorized_access(client_ip, path, method, "expired_token")
        raise expired_exception
    except JWTError:
        log_unauthorized_access(client_ip, path, method, "invalid_token")
        raise credentials_exception
    
    user_id = payload.get("user_id")
    if user_id is None:
        log_unauthorized_access(client_ip, path, method, "missing_user_id")
        raise credentials_exception
    
    return int(user_id)